#!/usr/bin/env python3
"""Check that every image and link in README.md still resolves.

Why: a README can look fine in the repo while an image host quietly dies
(a disabled Vercel deployment answers HTTP 402 and the page shows empty boxes).
This finds that the week it happens instead of whenever someone notices.

Rules
- Images must answer 2xx with an image/* content type. An SVG whose title says
  "inaccessible" or "not found" is a badge service reporting an error with
  status 200, so it counts as broken too.
- Links fail on 404/410/5xx and on connection errors. 401/403/999 are bot walls
  (npm, LinkedIn, CodePen and others refuse scripts), so they only warn.
  429 means rate limited, which proves nothing, so it only warns.
- Relative image paths are checked against the folder holding the README.

Threat model: the input is this repository's own README on a protected branch
(the workflow does not run on pull requests). Redirects are limited to http(s)
and five hops.

Usage: python3 scripts/check_readme_links.py README.md [--report report.md]
Exit code: 0 no failures, 1 at least one failure, 2 bad usage.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import http.client
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
RATE_LIMIT_BADGE_PHRASES = ("rate limit",)
MAX_REDIRECTS = 5
SVG_SNIFF_BYTES = 65536
DEFAULT_TIMEOUT = 20.0
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.0
DEFAULT_WORKERS = 8

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_SRC_ATTR = re.compile(r"""\bsrc\s*=\s*(["'])(.*?)\1""", re.IGNORECASE | re.DOTALL)
_SRCSET_ATTR = re.compile(
    r"""\bsrcset\s*=\s*(["'])(.*?)\1""", re.IGNORECASE | re.DOTALL
)
_MARKDOWN_IMAGE = re.compile(r"""!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)""")
_BARE_URL = re.compile(r"""https?://[^\s<>"'()\[\]]+""")
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_ARIA_LABEL = re.compile(r"""aria-label\s*=\s*"([^"]*)\"""", re.IGNORECASE)
_SRCSET_SPLIT = re.compile(r",\s+")


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


def _is_image_reference(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith(("data:", "#", "//", "mailto:")):
        return False
    return True


def extract_urls(markdown: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (images, links) in document order, each de-duplicated.

    Images are src/srcset/markdown image targets, absolute or relative.
    Links are the remaining absolute http(s) URLs. HTML comments are skipped.
    """
    text = _COMMENT.sub("", markdown)
    found: list[tuple[int, int, str]] = []
    for match in _SRC_ATTR.finditer(text):
        found.append((match.start(), 0, match.group(2).strip()))
    for match in _MARKDOWN_IMAGE.finditer(text):
        found.append((match.start(), 0, match.group(1).strip()))
    for match in _SRCSET_ATTR.finditer(text):
        for index, candidate in enumerate(_SRCSET_SPLIT.split(match.group(2).strip())):
            tokens = candidate.split()
            if tokens:
                found.append((match.start(), index, tokens[0]))
    images = _unique(
        value
        for _, _, value in sorted(found, key=lambda item: item[:2])
        if _is_image_reference(value)
    )
    image_set = set(images)
    links = _unique(
        url
        for url in (raw.rstrip(".,;:!?") for raw in _BARE_URL.findall(text))
        if url not in image_set
    )
    return images, links


def is_soft_host(host: str, soft_hosts: tuple[str, ...]) -> bool:
    host = host.lower()
    return any(host == soft or host.endswith("." + soft) for soft in soft_hosts if soft)


class _HttpOnlyRedirects(urllib.request.HTTPRedirectHandler):
    max_redirections = MAX_REDIRECTS

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


def _badge_phrase(sample: bytes, phrases: tuple[str, ...]) -> str | None:
    text = sample.decode("utf-8", errors="replace")
    labels = [
        *(m.group(1) for m in _TITLE.finditer(text)),
        *(m.group(1) for m in _ARIA_LABEL.finditer(text)),
    ]
    haystack = " ".join(labels).lower()
    return next((phrase for phrase in phrases if phrase in haystack), None)


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
    outcome = _fetch(url, timeout)
    for attempt in range(retries):
        if not _is_retryable(outcome):
            break
        time.sleep(backoff * (2**attempt))
        outcome = _fetch(url, timeout)
    return _classify(url, kind, outcome, soft_hosts)


def check_local_image(path: str, root: Path) -> Finding:
    root = root.resolve()
    target = (root / path).resolve()
    if root != target and root not in target.parents:
        return Finding(path, "image", "fail", "path escapes the repository")
    if not target.is_file():
        return Finding(path, "image", "fail", "file not found")
    return Finding(path, "image", "ok", "file exists")


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
    images, links = extract_urls(readme.read_text(encoding="utf-8"))
    jobs = [("image", url) for url in images] + [("link", url) for url in links]

    def run(job: tuple[str, str]) -> Finding:
        kind, url = job
        if kind == "image" and not url.startswith(("http://", "https://")):
            return check_local_image(url, readme.parent)
        return check_url(
            url,
            kind,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
            soft_hosts=soft_hosts,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return tuple(pool.map(run, jobs))


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


def _table(findings: list[Finding]) -> list[str]:
    rows = ["| Kind | URL | Problem |", "|---|---|---|"]
    for finding in findings:
        url = finding.url.replace("|", "%7C")
        rows.append(f"| {finding.kind} | `{url}` | {finding.detail} |")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check README images and links.")
    parser.add_argument("readme", help="path to README.md")
    parser.add_argument("--report", help="write a markdown report to this path")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument(
        "--soft-host",
        action="append",
        help="host whose network errors only warn (repeatable; an empty value clears the defaults)",
    )
    args = parser.parse_args(argv)

    readme = Path(args.readme)
    if not readme.is_file():
        print(f"error: {readme} not found", file=sys.stderr)
        return 2
    soft_hosts = tuple(
        host
        for host in (args.soft_host if args.soft_host is not None else SOFT_HOSTS)
        if host
    )

    findings = check_readme(
        readme,
        timeout=args.timeout,
        retries=args.retries,
        workers=args.workers,
        soft_hosts=soft_hosts,
    )
    report = render_report(findings)
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    return 1 if any(f.level == "fail" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
