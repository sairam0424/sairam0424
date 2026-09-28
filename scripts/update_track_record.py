#!/usr/bin/env python3
"""Recomputes the Track Record table in README.md from live GitHub data."""

import re
import subprocess

README = "README.md"
START = "<!--START_SECTION:track-record-->"
END = "<!--END_SECTION:track-record-->"

# Personal repos with their own release history, counted toward "versioned
# releases shipped" — deliberately excludes org repos (kelvran/*, mcpsmiths/*)
# and private repos, matching how this figure was originally verified.
RELEASE_REPOS = [
    "MindForge",
    "ContextOS",
    "ag-bash",
    "anvilry",
    "Tombstone",
    "trelix",
    "RateCap",
    "nh-deck",
    "daily-dose",
    "CommandVault",
    "Inkforge",
]


def gh(*args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def count_releases():
    total = 0
    for repo in RELEASE_REPOS:
        out = gh(
            "api", f"repos/sairam0424/{repo}/releases", "--paginate", "--jq", "length"
        )
        total += sum(int(line) for line in out.splitlines() if line)
    return total


def merged_prs():
    return int(
        gh(
            "api",
            "search/issues?q=author:sairam0424+is:pr+is:merged",
            "--jq",
            ".total_count",
        )
    )


def repos_contributed_to():
    query = (
        'query { user(login:"sairam0424") { '
        "repositoriesContributedTo(includeUserRepositories: true, "
        "contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, PULL_REQUEST_REVIEW, REPOSITORY]) "
        "{ totalCount } } }"
    )
    return int(
        gh(
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "--jq",
            ".data.user.repositoriesContributedTo.totalCount",
        )
    )


def contributions_last_year():
    query = (
        'query { user(login:"sairam0424") { contributionsCollection { '
        "contributionCalendar { totalContributions } } } }"
    )
    return int(
        gh(
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "--jq",
            ".data.user.contributionsCollection.contributionCalendar.totalContributions",
        )
    )


def format_k(n):
    return f"{n / 1000:.1f}K+"


def build_table():
    releases = count_releases()
    prs = merged_prs()
    repos = repos_contributed_to()
    contrib = contributions_last_year()
    return (
        f"{START}\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Versioned releases shipped | **{releases}** across {len(RELEASE_REPOS)} projects |\n"
        f"| PRs merged (career total) | **{prs:,}** |\n"
        f"| Repositories contributed to | **{repos}** (all-time, all contribution types) |\n"
        f"| Contributions (last 12 months) | **{format_k(contrib)}** |\n"
        f"{END}"
    )


def main():
    with open(README) as f:
        content = f.read()

    new_table = build_table()
    new_content = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        new_table,
        content,
        flags=re.DOTALL,
    )

    if new_content != content:
        with open(README, "w") as f:
            f.write(new_content)
        print("README.md updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
