"""Shared constants and builders for the update_latest_releases tests."""

import update_latest_releases as ulr

START = "<!--START_SECTION:latest-releases-->"
END = "<!--END_SECTION:latest-releases-->"

TRELIX = ulr.Project("trelix", "sairam0424/trelix", "github")
GATEWAY = ulr.Project(
    "kelvran/gateway", "kelvran/gateway", "github", tag_prefix="gateway/"
)
AGBASH = ulr.Project("ag-bash", "sairam0424/ag-bash", "npm", ref="@ag-bash/bash")


def github_release(tag, published="2026-10-29T12:23:17Z", **extra):
    base = {
        "tag_name": tag,
        "published_at": published,
        "draft": False,
        "prerelease": False,
        "html_url": f"https://github.com/o/r/releases/tag/{tag}",
    }
    base.update(extra)
    return base
