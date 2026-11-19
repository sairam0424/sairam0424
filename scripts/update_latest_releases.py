#!/usr/bin/env python3
"""Keep the README's "Latest releases" table and commit counts current.

Two jobs, one run:
  1. Rewrite the block between <!--START_SECTION:latest-releases--> and
     <!--END_SECTION:latest-releases--> from each project's real release
     source (GitHub releases, or the npm registry where the GitHub release
     list does not give one current version).
  2. Refresh the `N commits` figure on every README row that links a
     public repo. A figure is only ever raised: a lower live count is kept
     out of the README and reported, because it means a rewritten history
     or a misread response, and a person should look.

A lookup that fails keeps the previous row/figure and warns (as a GitHub
Actions annotation when run there). Everything that could be refreshed is
still written, but the run then exits 3 so a stale row cannot sit behind a
green job. A run where every release lookup fails writes nothing and exits 1.

Exit codes: 0 ok (updated or unchanged), 1 no release data at all,
2 bad usage (missing file or markers), 3 written, but some rows or counts
could not be refreshed.
"""

from __future__ import annotations

import http.client
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

START_MARKER = "<!--START_SECTION:latest-releases-->"
END_MARKER = "<!--END_SECTION:latest-releases-->"

MAX_VERSION_CHARS = 40
HTTP_TIMEOUT_SECONDS = 30
GH_TIMEOUT_SECONDS = 30
MAX_NPM_DOCUMENT_BYTES = 32 * 1024 * 1024
RELEASES_PER_PAGE = 100

EXIT_DEGRADED = 3

UNAVAILABLE = "unavailable"
NO_DATE = "-"
HEADER = "| Project | Latest release | Released | Source |"
SEPARATOR = "|---|---|---|---|"
SOURCE_NAMES = {"github": "GitHub", "npm": "npm"}

# Anything a lookup can raise that means "this source is unavailable right now".
FETCH_ERRORS = (
    OSError,
    ValueError,
    subprocess.SubprocessError,
    http.client.HTTPException,
)

_EARLIEST = datetime.min.replace(tzinfo=timezone.utc)

# Characters that survive into the README: enough for any real version string,
# none that can break out of a table cell, a link or an HTML tag.
_UNSAFE_VERSION_CHARS = re.compile(r"[^A-Za-z0-9._+@/-]")
# Only the two hosts the table links to, and no whitespace or markup characters.
_SAFE_URL = re.compile(r"https://(?:github\.com|www\.npmjs\.com)/[^\s()<>|`\\\"\[\]]*")
_ROW_LABEL = re.compile(r"^\| \[([^\]]+)\]\(")
_LAST_LINK = re.compile(r"<([^>]+)>;\s*rel=\"?last\"?", re.IGNORECASE)
_ANY_REL = re.compile(r"\brel=", re.IGNORECASE)
# `gh api --include` ends the status line with LF but the headers with CRLF.
_HEADER_BODY_GAP = re.compile(r"\r?\n\r?\n")

# A linked repo followed by its count, in the two shapes the README uses:
#   **[name](https://github.com/o/r)** · `1,234 commits`
#   [name](https://github.com/o/r) (`56 commits`, note)
_COUNT_PATTERN = re.compile(
    r"(?P<head>\[[^\]]+\]\(https://github\.com/(?P<repo>[\w.-]+/[\w.-]+)\)"
    r"(?:\*\*\s*·\s*|\s+\()`)(?P<count>\d[\d,]*)(?P<tail> commits`)"
)


@dataclass(frozen=True)
class Project:
    label: str
    repo: str
    source: str  # "github" or "npm"
    ref: str = ""  # npm package name
    tag_prefix: str = ""  # selects one version line inside a shared repo


@dataclass(frozen=True)
class Release:
    version: str
    released: str
    url: str


# The GitHub release is the source unless its release list does not give one
# current version: ag-bash makes one release per package (its newest is an
# example package) and ContextOS's releases stop at v1.6.1, while both keep
# publishing to npm.
PROJECTS: tuple[Project, ...] = (
    Project("trelix", "sairam0424/trelix", "github"),
    Project("MindForge", "sairam0424/MindForge", "github"),
    Project("ag-bash", "sairam0424/ag-bash", "npm", ref="@ag-bash/bash"),
    Project("ContextOS", "sairam0424/ContextOS", "npm", ref="@context-os/core"),
    Project("CommandVault", "sairam0424/CommandVault", "github"),
    Project("Tombstone", "sairam0424/Tombstone", "github"),
    Project("RateCap", "sairam0424/RateCap", "github"),
    Project("tracehub-mcp", "mcpsmiths/tracehub-mcp", "github"),
    Project("cost-guard-mcp", "mcpsmiths/cost-guard-mcp", "github"),
    Project("kelvran/gateway", "kelvran/gateway", "github", tag_prefix="gateway/"),
    Project("kelvran/evals", "kelvran/gateway", "github", tag_prefix="evals/"),
)


def safe_text(value: object) -> str:
    """Make server-supplied text inert in a markdown table cell."""
    cleaned = _UNSAFE_VERSION_CHARS.sub("?", str(value))
    return cleaned[:MAX_VERSION_CHARS]


def _parse_time(value: object) -> Optional[datetime]:
    """An ISO-8601 timestamp as an aware UTC datetime, or None."""
    if not isinstance(value, str):
        return None
    # fromisoformat only learned the "Z" suffix in Python 3.11.
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _day(moment: Optional[datetime]) -> str:
    return moment.date().isoformat() if moment else NO_DATE


def release_from_github(releases: object, tag_prefix: str = "") -> Optional[Release]:
    """Newest published, non-draft, non-prerelease entry for one tag prefix."""
    if not isinstance(releases, list):
        return None
    best: Optional[tuple[Optional[datetime], dict]] = None
    for entry in releases:
        if not isinstance(entry, dict) or entry.get("draft") or entry.get("prerelease"):
            continue
        tag = entry.get("tag_name")
        if not isinstance(tag, str) or not tag.startswith(tag_prefix):
            continue
        if not tag[len(tag_prefix) :]:
            continue
        moment = _parse_time(entry.get("published_at"))
        if best is None or (moment or _EARLIEST) > (best[0] or _EARLIEST):
            best = (moment, entry)
    if best is None:
        return None
    moment, entry = best
    url = entry.get("html_url")
    return Release(
        version=safe_text(entry["tag_name"][len(tag_prefix) :]),
        released=_day(moment),
        url=url if isinstance(url, str) else "",
    )


def release_from_npm(name: str, document: object) -> Optional[Release]:
    """The `latest` dist-tag of an npm registry document, with its date."""
    if not isinstance(document, dict):
        return None
    tags = document.get("dist-tags")
    times = document.get("time")
    if not isinstance(tags, dict) or not isinstance(times, dict):
        return None
    latest = tags.get("latest")
    moment = _parse_time(times.get(latest)) if isinstance(latest, str) else None
    if moment is None:
        return None
    package = urllib.parse.quote(name, safe="@/")
    return Release(
        version=safe_text(latest),
        released=_day(moment),
        url=f"https://www.npmjs.com/package/{package}/v/{urllib.parse.quote(latest, safe='')}",
    )


def _link(text: str, url: str) -> str:
    """A markdown link, or plain text when the URL is not a clean GitHub/npm one."""
    return f"[{text}]({url})" if _SAFE_URL.fullmatch(url) else text


def _label_cell(project: Project) -> str:
    return f"[{project.label}](https://github.com/{project.repo})"


def _row(project: Project, release: Release) -> str:
    version = _link(safe_text(release.version), release.url)
    source = SOURCE_NAMES[project.source]
    return f"| {_label_cell(project)} | {version} | {release.released} | {source} |"


def _unavailable_row(project: Project) -> str:
    source = SOURCE_NAMES[project.source]
    return f"| {_label_cell(project)} | {UNAVAILABLE} | {NO_DATE} | {source} |"


def render_block(
    rows: Sequence[tuple[Project, Optional[Release]]],
    earlier_rows: Mapping[str, str],
) -> str:
    """The marked block. A failed lookup (None) keeps the earlier row."""
    lines = [START_MARKER, HEADER, SEPARATOR]
    for project, release in rows:
        if release is not None:
            lines.append(_row(project, release))
        else:
            lines.append(earlier_rows.get(project.label) or _unavailable_row(project))
    lines.append(END_MARKER)
    return "\n".join(lines)


def _block_span(text: str) -> tuple[int, int]:
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise ValueError(
            f"README must contain exactly one {START_MARKER} and one {END_MARKER}"
        )
    start = text.index(START_MARKER)
    end = text.index(END_MARKER)
    if end < start:
        raise ValueError("the end marker comes before the start marker")
    return start, end + len(END_MARKER)


def replace_block(text: str, new_block: str) -> str:
    start, end = _block_span(text)
    return text[:start] + new_block + text[end:]


def previous_rows(text: str) -> dict[str, str]:
    """Rows of the current block, keyed by project label."""
    try:
        start, end = _block_span(text)
    except ValueError:
        return {}
    rows: dict[str, str] = {}
    for line in text[start:end].splitlines():
        match = _ROW_LABEL.match(line)
        if match:
            rows[match.group(1)] = line
    return rows


def _figure(match: re.Match) -> int:
    return int(match.group("count").replace(",", ""))


def find_count_repos(text: str) -> list[str]:
    """Repos with a linked `N commits` figure, first-seen order, no repeats."""
    seen: dict[str, str] = {}
    for match in _COUNT_PATTERN.finditer(text):
        seen.setdefault(match.group("repo").lower(), match.group("repo"))
    return list(seen.values())


def split_lower_counts(
    text: str, counts: Mapping[str, int]
) -> tuple[dict[str, int], list[str]]:
    """Keep counts that raise a README figure; report the ones that would lower it."""
    figures: dict[str, int] = {}
    for match in _COUNT_PATTERN.finditer(text):
        key = match.group("repo").lower()
        figures[key] = max(figures.get(key, 0), _figure(match))
    kept: dict[str, int] = {}
    lower: list[str] = []
    for repo, number in counts.items():
        current = figures.get(repo.lower())
        if current is not None and number < current:
            lower.append(f"{repo}: live {number:,} is below the README's {current:,}")
        else:
            kept[repo] = number
    return kept, lower


def update_commit_counts(text: str, counts: Mapping[str, int]) -> tuple[str, list[str]]:
    """Rewrite known repos' counts; return the new text and change notes."""
    wanted = {repo.lower(): number for repo, number in counts.items()}
    changes: list[str] = []

    def replace(match: re.Match) -> str:
        repo = match.group("repo")
        number = wanted.get(repo.lower())
        old = _figure(match)
        if number is None or number == old:
            return match.group(0)
        note = f"{repo}: {old:,} -> {number:,}"
        if note not in changes:
            changes.append(note)
        return f"{match.group('head')}{number:,}{match.group('tail')}"

    return _COUNT_PATTERN.sub(replace, text), changes


# --- network sources -------------------------------------------------------


def _gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=GH_TIMEOUT_SECONDS,
    )
    return result.stdout


def _flatten_pages(document: object) -> object:
    """`gh api --paginate --slurp` returns a list of pages; make it one list."""
    if isinstance(document, list) and all(isinstance(page, list) for page in document):
        return [entry for page in document for entry in page]
    return document


def load_release(project: Project) -> Optional[Release]:
    if project.source == "github":
        body = _gh(
            "api",
            f"repos/{project.repo}/releases?per_page={RELEASES_PER_PAGE}",
            "--paginate",
            "--slurp",
        )
        return release_from_github(_flatten_pages(json.loads(body)), project.tag_prefix)
    quoted = urllib.parse.quote(project.ref, safe="@")
    request = urllib.request.Request(
        f"https://registry.npmjs.org/{quoted}",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        body = response.read(MAX_NPM_DOCUMENT_BYTES + 1)
    if len(body) > MAX_NPM_DOCUMENT_BYTES:
        raise ValueError("npm registry document is larger than expected")
    return release_from_npm(project.ref, json.loads(body))


def _commit_count(repo: str) -> int:
    """Commits on the default branch, read from the `last` page link.

    A response that cannot be read with certainty raises ValueError instead
    of guessing: a wrong count would be committed to a public profile.
    """
    output = _gh("api", f"repos/{repo}/commits?per_page=1", "--include")
    parts = _HEADER_BODY_GAP.split(output, maxsplit=1)
    head, body = parts[0], (parts[1] if len(parts) > 1 else "")
    if _ANY_REL.search(head):
        last = _LAST_LINK.search(head)
        pages = (
            urllib.parse.parse_qs(urllib.parse.urlsplit(last.group(1)).query)
            if last
            else {}
        )
        page = pages.get("page", [""])[0]
        if not page.isdigit() or int(page) < 1:
            raise ValueError("Link header without a readable last page")
        return int(page)
    commits = json.loads(body) if body.strip() else None
    if not isinstance(commits, list) or not commits:
        raise ValueError("no commits in the response")
    return len(commits)


def load_commit_counts(repos: Sequence[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for repo in repos:
        try:
            counts[repo] = _commit_count(repo)
        except FETCH_ERRORS as error:
            _warn(f"commit count for {repo} skipped ({_describe(error)})")
    return counts


# --- driver ----------------------------------------------------------------


def _describe(error: BaseException) -> str:
    """Error class only: server text never reaches the log."""
    if isinstance(error, subprocess.CalledProcessError):
        return f"gh exited {error.returncode}"
    return type(error).__name__


def _warn(message: str) -> None:
    """A workflow annotation on GitHub Actions, a plain line elsewhere."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title=Latest releases::{message}", file=sys.stderr)
    else:
        print(f"WARNING: {message}", file=sys.stderr)


FetchRelease = Callable[[Project], Optional[Release]]
FetchCounts = Callable[[Sequence[str]], Mapping[str, int]]


def _collect_releases(
    projects: Sequence[Project], fetch_release: FetchRelease
) -> list[tuple[Project, Optional[Release]]]:
    rows: list[tuple[Project, Optional[Release]]] = []
    for project in projects:
        try:
            release = fetch_release(project)
        except FETCH_ERRORS as error:
            _warn(f"{project.label}: release lookup failed ({_describe(error)})")
            release = None
        else:
            if release is None:
                _warn(f"{project.label}: no matching release found")
        rows.append((project, release))
    return rows


def _refresh_counts(
    text: str, fetch_counts: FetchCounts
) -> tuple[str, list[str], bool]:
    """New text, change notes, and whether every figure could be refreshed."""
    repos = find_count_repos(text)
    try:
        counts = dict(fetch_counts(repos))
    except FETCH_ERRORS as error:
        _warn(f"commit counts skipped ({_describe(error)})")
        counts = {}
    complete = {repo.lower() for repo in repos} <= {repo.lower() for repo in counts}
    counts, lower = split_lower_counts(text, counts)
    for note in lower:
        _warn(f"commit count kept: {note}")
    new_text, changes = update_commit_counts(text, counts)
    return new_text, changes, complete and not lower


def main(
    argv: Optional[Sequence[str]] = None,
    projects: Sequence[Project] = PROJECTS,
    fetch_release: FetchRelease = load_release,
    fetch_counts: FetchCounts = load_commit_counts,
) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    path = Path(args[0] if args else "README.md")
    try:
        original = path.read_text(encoding="utf-8")
        replace_block(original, f"{START_MARKER}\n{END_MARKER}")
    except (OSError, ValueError) as error:
        print(f"error: {path}: {error}", file=sys.stderr)
        return 2

    rows = _collect_releases(projects, fetch_release)
    if all(release is None for _, release in rows):
        print("error: no release data fetched; README left untouched", file=sys.stderr)
        return 1

    text = replace_block(original, render_block(rows, previous_rows(original)))
    text, changes, counts_complete = _refresh_counts(text, fetch_counts)
    degraded = not counts_complete or any(release is None for _, release in rows)

    if text == original:
        print("No changes")
    else:
        path.write_text(text, encoding="utf-8")
        print(f"{path.name} updated")
        for note in changes:
            print(f"  commits {note}")
    if degraded:
        print(
            "some rows or counts could not be refreshed: see the warnings",
            file=sys.stderr,
        )
        return EXIT_DEGRADED
    return 0


if __name__ == "__main__":
    sys.exit(main())
