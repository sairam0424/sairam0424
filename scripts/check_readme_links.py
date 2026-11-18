#!/usr/bin/env python3
"""Check that every image and link in README.md still resolves.

Why: a README can look fine in the repo while an image host quietly dies
(a disabled Vercel deployment answers HTTP 402 and the page shows empty boxes).
This finds that the week it happens instead of whenever someone notices.

Rules
- Images must answer 2xx with an image/* content type. An SVG badge whose message
  (the text after the first colon of its title or aria-label, as in
  "label: message") says "inaccessible" or "not found" is a badge service
  reporting an error with status 200, so it counts as broken too. A badge that
  says "rate limit" is the service being throttled upstream: retried, then only
  a warning.
- Links fail on 404/410/5xx and on connection errors. 401/403/999 are bot walls
  (npm, LinkedIn, CodePen and others refuse scripts), so they only warn.
  429 means rate limited, which proves nothing, so it only warns.
- Network errors on "soft hosts" (default medium.com) only warn, and only for links.
- Relative image paths are checked against the folder holding the README.

Never crashes on one bad URL: every failure becomes a row in the report.

Not recognised (such images are still checked, but as plain links): reference-style
images (`![alt][ref]`) and image alt text containing square brackets. URLs with
parentheses nested two levels deep are cut at the second "(".
An unclosed "<!--" is treated as literal text, so a marker in prose or a code span
never hides the URLs after it. HTML entities in URLs are decoded only when they
end with a semicolon ("&amp;"), so "?a=1&region=us" is left alone.
No per-URL wall-clock deadline: the workflow's step timeout bounds a hung host.

Threat model: the input is this repository's own README on a protected branch
(the workflow does not run on pull requests). Redirects are limited to http(s)
and five hops. Text that came from a server is sanitised before it reaches the
report, because the report becomes a GitHub issue body.

Usage: python3 scripts/check_readme_links.py README.md [--report report.md]
Exit code: 0 no failures, 1 at least one failure, 2 bad usage, 3 internal error.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import http.client
import math
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

USER_AGENT = "readme-link-check (+https://github.com/sairam0424/sairam0424)"
BOT_WALL_STATUSES = frozenset({401, 403, 999})
INCONCLUSIVE_STATUSES = frozenset({429})
# Medium resets connections from plain HTTP clients, so a network error there
# says nothing about the link itself.
SOFT_HOSTS = ("medium.com",)
BROKEN_BADGE_PHRASES = (
    "inaccessible",
    "invalid",
    "not found",
    "no releases",
    "no tags",
    "no data",
)
# A badge service throttled by its own upstream (npm, GitHub) says so with
# status 200. That proves nothing about the README, so retry and then warn.
# Phrases are regular-expression fragments matched on whole words.
RATE_LIMIT_BADGE_PHRASES = (r"rate limit(?:ed)?",)
MAX_REDIRECTS = 5
MAX_REDIRECT_BODY = 65536  # stdlib reads a redirect's body before following it
SVG_SNIFF_BYTES = 65536
DEFAULT_TIMEOUT = 20.0
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.0
DEFAULT_WORKERS = 8
MAX_DETAIL_CHARS = 200
MAX_URL_CHARS = 300
TRAILING_PUNCTUATION = ".,;:!?*~`"

# A tag may hold a ">" inside a quoted attribute value. Bounded so that input made of
# thousands of unclosed "<img" cannot make the scan quadratic.
_IMG_TAG = re.compile(
    r"""<(?:img|source)\b(?:"[^"]{0,2000}"|'[^']{0,2000}'|[^>"']){0,500}>""",
    re.IGNORECASE,
)
_ENTITY = re.compile(r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
_ATTR_VALUE = r"""\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))"""
_SRC_ATTR = re.compile(r"(?<![\w-])src" + _ATTR_VALUE, re.IGNORECASE)
_SRCSET_ATTR = re.compile(r"(?<![\w-])srcset" + _ATTR_VALUE, re.IGNORECASE)
_SRCSET_SPLIT = re.compile(r",\s+|,(?=https?://)", re.IGNORECASE)
_MARKDOWN_TARGET = r"(?:[^()\s<>]|\([^()\s<>]*\))+"
_MARKDOWN_TITLE = r"""(?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?"""
_MARKDOWN_IMAGE = re.compile(
    r"!\[[^\]]*\]\(\s*<?(" + _MARKDOWN_TARGET + r")>?" + _MARKDOWN_TITLE + r"\s*\)"
)
_BARE_URL = re.compile(
    r"""https?://(?:[^\s<>"'()\[\]]|\([^\s<>"'()\[\]]*\))+""", re.IGNORECASE
)
_TITLE = re.compile(
    r"<title[^>]{0,200}>(.{0,2000}?)</title>", re.IGNORECASE | re.DOTALL
)
_ARIA_LABEL = re.compile(r"""aria-label\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)
_UNSAFE_REPORT_CHARS = re.compile(r"[^A-Za-z0-9 .,:;()/_'=%&#+\-]")
_HOST_NAME = re.compile(r"[a-z0-9.-]+")


@dataclass(frozen=True)
class Finding:
    url: str
    kind: str  # "image" or "link"
    level: str  # "ok", "warn" or "fail"
    detail: str


@dataclass(frozen=True)
class _Outcome:
    status: int | None
    content_type: str
    sample: bytes
    error: str | None


def _unique(items) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _attr_value(match: "re.Match[str]") -> str:
    return next(group for group in match.groups() if group is not None).strip()


def _decode_entities(value: str) -> str:
    """Decode HTML entities that end with a semicolon.

    html.unescape alone would also decode legacy forms without one, which turns
    the query "?x=1&region=us" into "?x=1®ion=us".
    """
    return _ENTITY.sub(lambda match: html.unescape(match.group(0)), value)


def _strip_comments(text: str) -> str:
    """Remove closed <!-- ... --> comments in a single linear pass.

    An unclosed marker is kept as text: a "<!--" in prose or a code span must never
    make the checker silently stop checking everything after it.
    """
    pieces = []
    position = 0
    while True:
        start = text.find("<!--", position)
        if start == -1:
            break
        end = text.find("-->", start + 4)
        if end == -1:
            break
        pieces.append(text[position:start])
        position = end + 3
    pieces.append(text[position:])
    return "".join(pieces)


def _image_reference(value: str) -> str | None:
    """Normalise an image target, or None when it is not something to check."""
    value = _decode_entities(value.strip())
    if not value or value.startswith(("data:", "#", "mailto:")):
        return None
    if value.startswith("//"):
        return "https:" + value
    return value


def extract_urls(markdown: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (images, links) in document order, each de-duplicated.

    Images are src/srcset values of <img> and <source> tags plus markdown image
    targets, absolute or relative. Links are the other absolute http(s) URLs.
    Closed HTML comments are skipped and HTML entities in URLs are decoded.
    """
    text = _strip_comments(markdown)
    found: list[tuple[int, int, str]] = []  # (position, index, value)
    spans: list[tuple[int, int]] = []  # image references, hidden from the link scan
    for tag in _IMG_TAG.finditer(text):
        for match in _SRC_ATTR.finditer(tag.group(0)):
            start = tag.start() + match.start()
            found.append((start, 0, _attr_value(match)))
            spans.append((start, tag.start() + match.end()))
        for match in _SRCSET_ATTR.finditer(tag.group(0)):
            start = tag.start() + match.start()
            for index, candidate in enumerate(_SRCSET_SPLIT.split(_attr_value(match))):
                if candidate.split():
                    found.append((start, index, candidate.split()[0]))
            spans.append((start, tag.start() + match.end()))
    for match in _MARKDOWN_IMAGE.finditer(text):
        found.append((match.start(), 0, match.group(1)))
        spans.append((match.start(), match.end()))

    images = _unique(
        reference
        for _, _, value in sorted(found, key=lambda item: item[:2])
        if (reference := _image_reference(value))
    )
    hidden_chars = list(text)
    for start, end in spans:
        hidden_chars[start:end] = " " * (end - start)
    hidden = "".join(hidden_chars)
    links = _unique(
        _decode_entities(_without_emphasis(match, hidden))
        for match in _BARE_URL.finditer(hidden)
    )
    return images, links


def _without_emphasis(match: "re.Match[str]", text: str) -> str:
    """The URL of a bare-URL match without trailing punctuation or markdown emphasis.

    "_https://x/y_" is emphasis: the closing underscore belongs to the markup. A
    URL that really ends in "_" keeps it, because nothing opened with "_" before it.
    """
    url = match.group(0).rstrip(TRAILING_PUNCTUATION)
    openers = 0
    while match.start() - openers > 0 and text[match.start() - openers - 1] == "_":
        openers += 1
    while openers and url.endswith("_"):
        url = url[:-1]
        openers -= 1
    return url


def is_soft_host(host: str, soft_hosts: tuple[str, ...]) -> bool:
    host = host.lower()
    return any(host == soft or host.endswith("." + soft) for soft in soft_hosts if soft)


def parse_soft_hosts(values) -> tuple[str, ...]:
    """Normalise --soft-host values; a URL or anything but a host name is rejected."""
    hosts = []
    for value in values:
        host = value.strip().lower()
        if not host:
            continue
        if not _HOST_NAME.fullmatch(host):
            raise ValueError(f"not a host name: {value!r}")
        hosts.append(host)
    return tuple(hosts)


def _request_url(url: str) -> str:
    """Turn a README URL into what goes on the wire (spaces, non-ASCII, IDN host).

    Raises ValueError for anything that is not a usable http(s) URL.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("not an http(s) URL")
    port = parts.port  # validates the port
    host = (
        parts.hostname
    )  # lower-cased, and without userinfo (credentials are never sent)
    if not host.isascii():
        host = host.encode("idna").decode("ascii")
    if ":" in host:
        host = f"[{host}]"  # an IPv6 literal needs its brackets back
    netloc = host + (f":{port}" if port is not None else "")
    path = urllib.parse.quote(parts.path, safe="/%:@!$&'()*+,;=~-._")
    query = urllib.parse.quote(parts.query, safe="/?%:@!$&'()*+,;=~-._[]")
    return urllib.parse.urlunsplit((parts.scheme, netloc, path, query, ""))


class _BoundedBody:
    """A response body that reads at most MAX_REDIRECT_BODY bytes per call.

    stdlib's redirect handler calls fp.read() on a redirect's body before following
    it. A hostile or broken host could make that load gigabytes into memory.
    """

    def __init__(self, fp):
        self._fp = fp

    def read(self, amount=None):
        limit = (
            MAX_REDIRECT_BODY
            if amount is None or amount < 0
            else min(amount, MAX_REDIRECT_BODY)
        )
        return self._fp.read(limit)

    def __getattr__(self, name):
        return getattr(self._fp, name)


class _HttpOnlyRedirects(urllib.request.HTTPRedirectHandler):
    max_redirections = MAX_REDIRECTS

    def http_error_302(self, req, fp, code, msg, headers):
        return super().http_error_302(req, _BoundedBody(fp), code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        scheme = urllib.parse.urlsplit(newurl).scheme.lower()
        if scheme not in ("http", "https"):
            raise urllib.error.HTTPError(
                req.full_url,
                code,
                f"{scheme or 'unknown'} scheme not allowed",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(url: str, timeout: float) -> _Outcome:
    opener = urllib.request.build_opener(_HttpOnlyRedirects)
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}
    )
    try:
        with opener.open(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            sample = (
                response.read(SVG_SNIFF_BYTES) if "svg" in content_type.lower() else b""
            )
            return _Outcome(response.status, content_type, sample, None)
    except urllib.error.HTTPError as error:
        try:
            if 300 <= error.code < 400:
                return _Outcome(None, "", b"", f"redirect refused: {error.msg}")
            return _Outcome(
                error.code, error.headers.get("Content-Type", ""), b"", None
            )
        finally:
            error.close()
    except (TimeoutError, socket.timeout):
        return _Outcome(None, "", b"", "timed out")
    except urllib.error.URLError as error:
        if isinstance(error.reason, (TimeoutError, socket.timeout)):
            return _Outcome(None, "", b"", "timed out")
        return _Outcome(None, "", b"", f"connection failed: {error.reason}")
    except (OSError, http.client.HTTPException) as error:
        return _Outcome(None, "", b"", f"connection failed: {error}")


def _badge_phrase(sample: bytes, phrases: tuple[str, ...]) -> str | None:
    """Find a whole-word phrase in the message of an SVG badge.

    Badges read "label: message", so the message is the text after the first colon
    (a message may itself contain colons: "custom badge: invalid query parameter: url").
    """
    text = sample.decode("utf-8", errors="replace")
    labels = [m.group(1) for m in _TITLE.finditer(text)]
    labels += [
        m.group(1) if m.group(1) is not None else m.group(2)
        for m in _ARIA_LABEL.finditer(text)
    ]
    messages = [label.split(":", 1)[-1].strip().lower() for label in labels]
    return next(
        (
            phrase
            for phrase in phrases
            if any(re.search(rf"\b{phrase}\b", message) for message in messages)
        ),
        None,
    )


def _is_retryable(outcome: _Outcome) -> bool:
    if outcome.error is not None:
        return outcome.error == "timed out" or outcome.error.startswith(
            "connection failed"
        )
    return (
        outcome.status in INCONCLUSIVE_STATUSES
        or (outcome.status or 0) >= 500
        or _badge_phrase(outcome.sample, RATE_LIMIT_BADGE_PHRASES) is not None
    )


def _classify(
    url: str, kind: str, outcome: _Outcome, soft_hosts: tuple[str, ...]
) -> Finding:
    if outcome.error is not None:
        host = urllib.parse.urlsplit(url).hostname or ""
        if kind == "link" and is_soft_host(host, soft_hosts):
            return Finding(
                url, kind, "warn", f"{outcome.error} (soft host, inconclusive)"
            )
        return Finding(url, kind, "fail", outcome.error)
    status = outcome.status or 0
    if status in INCONCLUSIVE_STATUSES:
        return Finding(url, kind, "warn", f"HTTP {status} (rate limited, inconclusive)")
    if kind == "link" and status in BOT_WALL_STATUSES:
        return Finding(url, kind, "warn", f"HTTP {status} (bot wall, cannot verify)")
    if not 200 <= status < 300:
        return Finding(url, kind, "fail", f"HTTP {status}")
    if kind == "image":
        content_type = outcome.content_type.lower()
        if not content_type.startswith("image/"):
            return Finding(
                url,
                kind,
                "fail",
                f"content-type {content_type or 'missing'} is not an image",
            )
        phrase = _badge_phrase(outcome.sample, BROKEN_BADGE_PHRASES)
        if phrase:
            return Finding(
                url,
                kind,
                "fail",
                f"error badge served with HTTP {status}: says '{phrase}'",
            )
        if _badge_phrase(outcome.sample, RATE_LIMIT_BADGE_PHRASES):
            return Finding(
                url,
                kind,
                "warn",
                "badge says 'rate limit' (badge service throttled, inconclusive)",
            )
    return Finding(url, kind, "ok", f"HTTP {status}")


def check_url(
    url: str,
    kind: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    soft_hosts: tuple[str, ...] = SOFT_HOSTS,
) -> Finding:
    """Check one URL. Never raises: any problem becomes a failing Finding."""
    try:
        target = _request_url(url)
    except ValueError:
        return Finding(url, kind, "fail", "invalid URL")
    try:
        outcome = _fetch(target, timeout)
        for attempt in range(retries):
            if not _is_retryable(outcome):
                break
            time.sleep(backoff * (2**attempt))
            outcome = _fetch(target, timeout)
        return _classify(target, kind, outcome, soft_hosts)
    except Exception as error:  # a checker must report, not crash
        return Finding(url, kind, "fail", f"unexpected error: {type(error).__name__}")


def check_local_image(path: str, root: Path) -> Finding:
    try:
        cleaned = urllib.parse.unquote(re.split(r"[?#]", path, maxsplit=1)[0])
        if "\x00" in cleaned:
            return Finding(path, "image", "fail", "invalid path")
        root = root.resolve()
        target = (
            root / cleaned.lstrip("/")
        ).resolve()  # a leading "/" means repo root, as on GitHub
        if root != target and root not in target.parents:
            return Finding(path, "image", "fail", "path escapes the repository")
        if not target.is_file():
            return Finding(path, "image", "fail", "file not found")
        return Finding(path, "image", "ok", "file exists")
    except (
        OSError,
        ValueError,
        RuntimeError,
    ):  # RuntimeError: symlink loop on Python < 3.13
        return Finding(path, "image", "fail", "invalid path")


def check_readme(
    readme_path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    workers: int = DEFAULT_WORKERS,
    soft_hosts: tuple[str, ...] = SOFT_HOSTS,
) -> tuple[Finding, ...]:
    readme = Path(readme_path)
    images, links = extract_urls(readme.read_text(encoding="utf-8", errors="replace"))
    jobs = [("image", url) for url in images] + [("link", url) for url in links]

    def run(job: tuple[str, str]) -> Finding:
        kind, url = job
        try:
            if kind == "image" and not url.lower().startswith(("http://", "https://")):
                return check_local_image(url, readme.parent)
            return check_url(
                url,
                kind,
                timeout=timeout,
                retries=retries,
                backoff=backoff,
                soft_hosts=soft_hosts,
            )
        except Exception as error:  # one bad URL must not sink the whole run
            return Finding(url, kind, "fail", f"checker error: {type(error).__name__}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return tuple(pool.map(run, jobs))


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


def _detail_cell(text: str) -> str:
    """Make server-supplied text inert in a markdown table.

    Only plain characters survive, the text is length-limited, and it sits inside a
    code span, where GitHub renders no links, mentions, references or emoji.
    """
    cleaned = _UNSAFE_REPORT_CHARS.sub("?", " ".join(text.split()))[:MAX_DETAIL_CHARS]
    return f"`{cleaned}`"


def _url_cell(url: str) -> str:
    safe = " ".join(url.split()).replace("|", "%7C").replace("`", "%60")
    safe = safe.encode("ascii", "backslashreplace").decode("ascii")
    return safe if len(safe) <= MAX_URL_CHARS else safe[: MAX_URL_CHARS - 3] + "..."


def _table(findings: list[Finding]) -> list[str]:
    rows = ["| Kind | URL | Problem |", "|---|---|---|"]
    for finding in findings:
        rows.append(
            f"| {finding.kind} | `{_url_cell(finding.url)}` | {_detail_cell(finding.detail)} |"
        )
    return rows


def render_report(findings: tuple[Finding, ...]) -> str:
    failures = [f for f in findings if f.level == "fail"]
    warnings = [f for f in findings if f.level == "warn"]
    images = sum(1 for f in findings if f.kind == "image")
    lines = [
        "## README image and link check",
        "",
        f"{_plural(len(failures), 'failure')}, {_plural(len(warnings), 'warning')}, "
        f"{len(findings)} checked ({_plural(images, 'image')}, {_plural(len(findings) - images, 'link')}).",
        "",
    ]
    if failures:
        lines += _table(failures) + [""]
    if warnings:
        lines += [
            "<details>",
            f"<summary>{_plural(len(warnings), 'warning')} (bot walls and rate limits, not proof of a broken link)</summary>",
            "",
            *_table(warnings),
            "",
            "</details>",
            "",
        ]
    return "\n".join(lines)


def _positive_seconds(text: str) -> float:
    value = float(text)
    if not (math.isfinite(value) and value > 0):
        raise argparse.ArgumentTypeError("must be a finite number above 0")
    return value


def _count(minimum: int):
    def parse(text: str) -> int:
        value = int(text)
        if value < minimum:
            raise argparse.ArgumentTypeError(f"must be at least {minimum}")
        return value

    return parse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check README images and links.")
    parser.add_argument("readme", help="path to README.md")
    parser.add_argument("--report", help="write a markdown report to this path")
    parser.add_argument("--timeout", type=_positive_seconds, default=DEFAULT_TIMEOUT)
    parser.add_argument("--retries", type=_count(0), default=DEFAULT_RETRIES)
    parser.add_argument("--workers", type=_count(1), default=DEFAULT_WORKERS)
    parser.add_argument(
        "--soft-host",
        action="append",
        help="host whose network errors only warn (repeatable; an empty value clears the defaults)",
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit as request:  # argparse exits for --help (0) and bad usage (2)
        return request.code if isinstance(request.code, int) else 2

    readme = Path(args.readme)
    if not readme.is_file():
        print(f"error: {readme} not found", file=sys.stderr)
        return 2
    try:
        soft_hosts = parse_soft_hosts(
            args.soft_host if args.soft_host is not None else SOFT_HOSTS
        )
    except ValueError as error:
        print(f"error: --soft-host: {error}", file=sys.stderr)
        return 2

    try:
        findings = check_readme(
            readme,
            timeout=args.timeout,
            retries=args.retries,
            workers=args.workers,
            soft_hosts=soft_hosts,
        )
    except (
        Exception
    ) as error:  # exit 1 means "failures found", so a crash gets its own code
        print(f"error: checker crashed: {type(error).__name__}", file=sys.stderr)
        return 3
    report = render_report(findings)
    print(report)
    if args.report:
        try:
            Path(args.report).write_text(report, encoding="utf-8")
        except OSError as error:
            print(f"error: cannot write report: {error.strerror}", file=sys.stderr)
            return 2
    return 1 if any(f.level == "fail" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
