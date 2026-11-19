"""Tests for update_latest_releases: parsing, rendering and commit counting.

No network. The sources, the run and the workflow are in
test_update_latest_releases_io.py.
Run: python3 -m unittest discover -s scripts -p 'test_*.py' -v
"""

import unittest
from datetime import datetime, timezone
from pathlib import Path

import update_latest_releases as ulr
from _update_releases_fixtures import AGBASH, END, START, TRELIX, github_release


class ParseGithubTests(unittest.TestCase):
    def test_the_newest_published_release_wins(self):
        releases = [
            github_release("v3.5.1"),
            github_release("v3.5.0", "2026-10-27T00:00:00Z"),
        ]
        release = ulr.release_from_github(releases)
        self.assertEqual((release.version, release.released), ("v3.5.1", "2026-10-29"))
        self.assertEqual(release.url, "https://github.com/o/r/releases/tag/v3.5.1")

    def test_drafts_and_prereleases_are_skipped(self):
        releases = [
            github_release("v4.0.0-rc.1", prerelease=True),
            github_release("v4.0.0-draft", draft=True),
            github_release("v3.9.0", "2026-09-01T00:00:00Z"),
        ]
        self.assertEqual(ulr.release_from_github(releases).version, "v3.9.0")

    def test_a_tag_prefix_selects_one_version_line_and_is_not_shown(self):
        releases = [
            github_release("evals/v0.10.1", "2026-09-22T08:29:32Z"),
            github_release("gateway/v0.20.0", "2026-10-15T12:44:07Z"),
        ]
        gateway = ulr.release_from_github(releases, tag_prefix="gateway/")
        evals = ulr.release_from_github(releases, tag_prefix="evals/")
        self.assertEqual((gateway.version, gateway.released), ("v0.20.0", "2026-10-15"))
        self.assertEqual((evals.version, evals.released), ("v0.10.1", "2026-09-22"))
        self.assertTrue(gateway.url.endswith("gateway/v0.20.0"))

    def test_no_matching_release_gives_none(self):
        self.assertIsNone(ulr.release_from_github([]))
        self.assertIsNone(
            ulr.release_from_github([github_release("v1.0.0")], tag_prefix="gateway/")
        )

    def test_a_malformed_date_becomes_a_dash_not_a_crash(self):
        release = ulr.release_from_github(
            [github_release("v1.0.0", published="not a date")]
        )
        self.assertEqual(release.released, "-")


class ParseNpmTests(unittest.TestCase):
    DOCUMENT = {
        "dist-tags": {"latest": "6.0.5", "next": "7.0.0-beta.1"},
        "time": {
            "6.0.5": "2026-09-24T12:59:00.000Z",
            "7.0.0-beta.1": "2026-11-01T00:00:00.000Z",
        },
    }

    def test_the_latest_dist_tag_and_its_publish_date(self):
        release = ulr.release_from_npm("@ag-bash/bash", self.DOCUMENT)
        self.assertEqual((release.version, release.released), ("6.0.5", "2026-09-24"))
        self.assertEqual(
            release.url, "https://www.npmjs.com/package/@ag-bash/bash/v/6.0.5"
        )

    def test_a_document_without_latest_or_time_gives_none(self):
        self.assertIsNone(ulr.release_from_npm("x", {}))
        self.assertIsNone(
            ulr.release_from_npm("x", {"dist-tags": {"latest": "1.0.0"}, "time": {}})
        )


class SafeTextTests(unittest.TestCase):
    def test_markup_and_pipes_become_question_marks(self):
        self.assertEqual(
            ulr.safe_text("v1.0.0|[x](http://e)<b>"), "v1.0.0??x??http?//e??b?"
        )
        for bad in '|[]()<>`*!\\" ':
            self.assertNotIn(bad, ulr.safe_text(f"a{bad}b"))

    def test_normal_versions_survive_and_length_is_limited(self):
        self.assertEqual(
            ulr.safe_text("v1.2.3-rc.1+build@scope/x"), "v1.2.3-rc.1+build@scope/x"
        )
        self.assertEqual(len(ulr.safe_text("v" + "9" * 200)), ulr.MAX_VERSION_CHARS)


class RenderTests(unittest.TestCase):
    ROWS = (
        (
            TRELIX,
            ulr.Release(
                "v3.5.1",
                "2026-10-29",
                "https://github.com/sairam0424/trelix/releases/tag/v3.5.1",
            ),
        ),
        (
            AGBASH,
            ulr.Release(
                "6.0.5",
                "2026-09-24",
                "https://www.npmjs.com/package/@ag-bash/bash/v/6.0.5",
            ),
        ),
    )

    def test_block_has_markers_header_and_one_row_per_project(self):
        block = ulr.render_block(self.ROWS, earlier_rows={})
        lines = block.splitlines()
        self.assertEqual(lines[0], START)
        self.assertEqual(lines[-1], END)
        self.assertEqual(lines[1], "| Project | Latest release | Released | Source |")
        self.assertEqual(
            lines[3],
            "| [trelix](https://github.com/sairam0424/trelix) | "
            "[v3.5.1](https://github.com/sairam0424/trelix/releases/tag/v3.5.1) | 2026-10-29 | GitHub |",
        )
        self.assertIn("| npm |", lines[4])

    def test_a_failed_lookup_keeps_the_previous_row(self):
        previous = {
            "trelix": "| [trelix](https://github.com/sairam0424/trelix) | [v3.4.0](u) | 2026-09-01 | GitHub |"
        }
        block = ulr.render_block(((TRELIX, None),), earlier_rows=previous)
        self.assertIn(previous["trelix"], block)

    def test_a_failed_lookup_with_no_previous_row_says_unavailable(self):
        block = ulr.render_block(((TRELIX, None),), earlier_rows={})
        self.assertIn("unavailable", block)

    def test_rendering_is_deterministic(self):
        self.assertEqual(
            ulr.render_block(self.ROWS, {}), ulr.render_block(self.ROWS, {})
        )

    def test_previous_rows_are_read_from_an_existing_block(self):
        block = ulr.render_block(self.ROWS, {})
        text = f"intro\n\n{block}\n\noutro\n"
        previous = ulr.previous_rows(text)
        self.assertEqual(set(previous), {"trelix", "ag-bash"})
        self.assertTrue(previous["trelix"].startswith("| [trelix]"))


class ReplaceBlockTests(unittest.TestCase):
    def test_only_the_marked_block_changes(self):
        text = f"before\n{START}\nold table\n{END}\nafter\n"
        new_block = f"{START}\nnew table\n{END}"
        self.assertEqual(
            ulr.replace_block(text, new_block), f"before\n{new_block}\nafter\n"
        )

    def test_missing_or_duplicate_markers_raise(self):
        new_block = f"{START}\nx\n{END}"
        for text in (
            "no markers",
            f"{START}\nonly start",
            f"{START}\na\n{END}\n{START}\nb\n{END}",
        ):
            with self.subTest(text=text[:20]), self.assertRaises(ValueError):
                ulr.replace_block(text, new_block)

    def test_replacement_text_is_literal_not_a_regex_template(self):
        text = f"{START}\nold\n{END}"
        new_block = f"{START}\n| a \\1 \\g<0> |\n{END}"
        self.assertEqual(ulr.replace_block(text, new_block), new_block)


class CommitCountTests(unittest.TestCase):
    README = (
        "| **[trelix](https://github.com/sairam0424/trelix)** · `1,453 commits` | desc |\n"
        "| **[gRPC Microservices](https://github.com/sairam0424/gRPC-micro-services)** · `316 commits` — *Order* | d |\n"
        "| **Graph-Forge** · `574 commits` *(private)* | d |\n"
        "| **[Not-Humans-Lab](https://github.com/sairam0424/not-humans-lab)** | Umbrella: "
        "[daily-dose](https://github.com/sairam0424/daily-dose) (`156 commits`, digest) and "
        "[nh-deck](https://github.com/sairam0424/nh-deck) (`58 commits`, CLI) | x |\n"
        "Commit counts are a build-signal only. Also 12 commits ago in prose.\n"
    )

    def test_all_three_row_shapes_are_found_in_order_without_duplicates(self):
        self.assertEqual(
            ulr.find_count_repos(self.README),
            [
                "sairam0424/trelix",
                "sairam0424/gRPC-micro-services",
                "sairam0424/daily-dose",
                "sairam0424/nh-deck",
            ],
        )

    def test_counts_are_replaced_with_thousands_separators(self):
        counts = {
            "sairam0424/trelix": 1881,
            "sairam0424/gRPC-micro-services": 317,
            "sairam0424/daily-dose": 215,
        }
        text, changes = ulr.update_commit_counts(self.README, counts)
        self.assertIn("`1,881 commits`", text)
        self.assertIn("`317 commits`", text)
        self.assertIn("(`215 commits`, digest)", text)
        self.assertEqual(len(changes), 3)
        self.assertIn("sairam0424/trelix: 1,453 -> 1,881", changes)

    def test_unknown_repos_private_rows_and_prose_are_untouched(self):
        text, changes = ulr.update_commit_counts(
            self.README, {"sairam0424/trelix": 1881}
        )
        self.assertIn("`574 commits` *(private)*", text)
        self.assertIn("(`58 commits`, CLI)", text)
        self.assertIn("Also 12 commits ago in prose.", text)
        self.assertEqual(len(changes), 1)

    def test_an_unchanged_count_is_not_reported(self):
        text, changes = ulr.update_commit_counts(
            self.README, {"sairam0424/nh-deck": 58}
        )
        self.assertEqual((text, changes), (self.README, []))

    def test_repo_names_match_case_insensitively(self):
        text, _ = ulr.update_commit_counts(self.README, {"SAIRAM0424/TRELIX": 1881})
        self.assertIn("`1,881 commits`", text)

    def test_the_real_readme_keeps_the_markers_and_matchable_rows(self):
        readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual((readme.count(START), readme.count(END)), (1, 1))
        self.assertGreaterEqual(len(ulr.find_count_repos(readme)), 12)


class ReleaseSelectionTests(unittest.TestCase):
    def _version(self, releases, prefix=""):
        release = ulr.release_from_github(releases, prefix)
        return release.version if release else None

    def test_the_newest_wins_even_when_it_is_listed_last(self):
        releases = [
            github_release("v1.0.0", "2026-01-01T00:00:00Z"),
            github_release("v1.1.0", "2026-02-01T00:00:00Z"),
        ]
        self.assertEqual(self._version(releases), "v1.1.0")

    def test_two_releases_on_one_day_are_ordered_by_the_time_of_day(self):
        releases = [
            github_release("v1.0.1", "2026-01-01T08:00:00Z"),
            github_release("v1.0.2", "2026-01-01T09:00:00Z"),
        ]
        self.assertEqual(self._version(releases), "v1.0.2")
        self.assertEqual(self._version(list(reversed(releases))), "v1.0.2")

    def test_an_identical_timestamp_keeps_the_first_listed(self):
        releases = [
            github_release("v1.0.1", "2026-01-01T08:00:00Z"),
            github_release("v1.0.2", "2026-01-01T08:00:00Z"),
        ]
        self.assertEqual(self._version(releases), "v1.0.1")

    def test_an_impossible_or_non_ascii_date_ranks_below_a_real_one(self):
        for bogus in (
            "9999-99-99T00:00:00Z",
            "٢٠٢٦-١٠-٢٩T00:00:00Z",
            "2026-13-45",
            None,
        ):
            releases = [
                github_release("v9.9.9", bogus),
                github_release("v1.0.0", "2026-01-01T00:00:00Z"),
            ]
            with self.subTest(bogus=bogus):
                release = ulr.release_from_github(releases)
                self.assertEqual(
                    (release.version, release.released), ("v1.0.0", "2026-01-01")
                )

    def test_the_day_is_the_utc_day(self):
        release = ulr.release_from_github(
            [github_release("v1.0.0", "2026-10-29T23:30:00-05:00")]
        )
        self.assertEqual(release.released, "2026-10-30")

    def test_a_tag_prefix_must_start_the_tag_and_leave_a_version(self):
        releases = [
            github_release("pre-gateway/v9.0.0", "2026-12-01T00:00:00Z"),
            github_release("gateway/", "2026-11-01T00:00:00Z"),
            github_release("gateway/v0.20.0", "2026-10-15T00:00:00Z"),
        ]
        self.assertEqual(self._version(releases, "gateway/"), "v0.20.0")


class LinkTests(unittest.TestCase):
    def test_github_and_npm_urls_become_links(self):
        for url in (
            "https://github.com/o/r/releases/tag/gateway/v0.20.0",
            "https://www.npmjs.com/package/@ag-bash/bash/v/6.0.5",
        ):
            with self.subTest(url=url):
                self.assertEqual(ulr._link("v1", url), f"[v1]({url})")

    def test_anything_else_stays_plain_text(self):
        for url in (
            "",
            "https://github.com/o/r/x\n",
            "https://evil.example/phish",
            "https://github.com.evil.example/x",
            "https://github.com@evil.example/x",
            "http://github.com/o/r",
            "javascript:alert(1)",
            "https://github.com/o/r)[x](https://evil.example",
            "https://github.com/o/r|x",
            "https://github.com/o/r x",
        ):
            with self.subTest(url=url):
                self.assertEqual(ulr._link("v1", url), "v1")

    def test_a_version_set_directly_on_a_release_is_still_made_safe_in_the_row(self):
        row = ulr._row(TRELIX, ulr.Release("v1|[x](y)", "2026-01-01", ""))
        self.assertEqual(row.count("|"), 5)
        self.assertNotIn("[x]", row)

    def test_the_npm_url_is_built_from_a_percent_encoded_version(self):
        document = {
            "dist-tags": {"latest": "1.0.0\n"},
            "time": {"1.0.0\n": "2026-01-01T00:00:00Z"},
        }
        release = ulr.release_from_npm("@x/y", document)
        self.assertEqual(release.url, "https://www.npmjs.com/package/@x/y/v/1.0.0%0A")
        self.assertNotIn("\n", ulr._row(AGBASH, release))


class LowerCountTests(unittest.TestCase):
    TEXT = (
        "[a](https://github.com/o/r) (`1,881 commits`, x) and "
        "[a again](https://github.com/o/r) (`1,881 commits`, y)\n"
    )

    def test_a_count_below_the_readme_figure_is_held_back_and_reported(self):
        kept, lower = ulr.split_lower_counts(self.TEXT, {"O/R": 1, "o/other": 5})
        self.assertEqual(kept, {"o/other": 5})
        self.assertEqual(lower, ["O/R: live 1 is below the README's 1,881"])

    def test_equal_and_higher_counts_pass_through(self):
        kept, lower = ulr.split_lower_counts(self.TEXT, {"o/r": 1881})
        self.assertEqual((kept, lower), ({"o/r": 1881}, []))
        kept, lower = ulr.split_lower_counts(self.TEXT, {"o/r": 2000})
        self.assertEqual((kept, lower), ({"o/r": 2000}, []))

    def test_one_repo_shown_twice_gives_one_change_note(self):
        text, changes = ulr.update_commit_counts(self.TEXT, {"o/r": 1900})
        self.assertEqual(text.count("`1,900 commits`"), 2)
        self.assertEqual(changes, ["o/r: 1,881 -> 1,900"])

    def test_a_cell_with_no_digits_is_left_alone(self):
        text = "[a](https://github.com/o/r) (`, commits`)"
        self.assertEqual(ulr.find_count_repos(text), [])
        self.assertEqual(ulr.update_commit_counts(text, {"o/r": 5}), (text, []))


class ProjectContractTests(unittest.TestCase):
    """The project list is the public output: pin every source and prefix."""

    EXPECTED = {
        "trelix": ("sairam0424/trelix", "github", "", ""),
        "MindForge": ("sairam0424/MindForge", "github", "", ""),
        "ag-bash": ("sairam0424/ag-bash", "npm", "@ag-bash/bash", ""),
        "ContextOS": ("sairam0424/ContextOS", "npm", "@context-os/core", ""),
        "CommandVault": ("sairam0424/CommandVault", "github", "", ""),
        "Tombstone": ("sairam0424/Tombstone", "github", "", ""),
        "RateCap": ("sairam0424/RateCap", "github", "", ""),
        "tracehub-mcp": ("mcpsmiths/tracehub-mcp", "github", "", ""),
        "cost-guard-mcp": ("mcpsmiths/cost-guard-mcp", "github", "", ""),
        "kelvran/gateway": ("kelvran/gateway", "github", "", "gateway/"),
        "kelvran/evals": ("kelvran/gateway", "github", "", "evals/"),
    }

    def test_every_project_reads_from_the_expected_source(self):
        actual = {
            p.label: (p.repo, p.source, p.ref, p.tag_prefix) for p in ulr.PROJECTS
        }
        self.assertEqual(actual, self.EXPECTED)


class ParseTimeTests(unittest.TestCase):
    def test_a_z_suffix_with_fractional_seconds(self):
        self.assertEqual(
            ulr._parse_time("2026-09-24T12:59:00.000Z"),
            datetime(2026, 9, 24, 12, 59, tzinfo=timezone.utc),
        )

    def test_an_offset_is_converted_to_utc(self):
        self.assertEqual(
            ulr._parse_time("2026-10-29T23:30:00-05:00"),
            datetime(2026, 10, 30, 4, 30, tzinfo=timezone.utc),
        )

    def test_a_naive_timestamp_is_read_as_utc_whatever_the_host_timezone(self):
        self.assertEqual(
            ulr._parse_time("2026-01-01T23:30:00"),
            datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc),
        )

    def test_unreadable_and_out_of_range_values_are_none_not_errors(self):
        for value in (
            None,
            5,
            "",
            "yesterday",
            "0001-01-01T00:00:00+05:00",
            "9999-12-31T23:59:59-05:00",
        ):
            with self.subTest(value=value):
                self.assertIsNone(ulr._parse_time(value))


class RenderContractTests(unittest.TestCase):
    def test_the_header_and_separator_lines_are_exact(self):
        lines = ulr.render_block(((TRELIX, None),), earlier_rows={}).splitlines()
        self.assertEqual(lines[1], "| Project | Latest release | Released | Source |")
        self.assertEqual(lines[2], "|---|---|---|---|")

    def test_an_unavailable_row_keeps_the_projects_own_source(self):
        block = ulr.render_block(((AGBASH, None),), earlier_rows={})
        self.assertIn(
            "| [ag-bash](https://github.com/sairam0424/ag-bash) | unavailable | - | npm |",
            block.splitlines(),
        )

    def test_earlier_rows_are_read_only_from_inside_the_block(self):
        stray = (
            "| [trelix](https://github.com/sairam0424/trelix) | [v0.0.1](u) "
            "| 2020-01-01 | GitHub |"
        )
        self.assertEqual(ulr.previous_rows(f"{stray}\n{START}\n{END}\n"), {})

    def test_every_marker_problem_is_refused(self):
        block = f"{START}\nx\n{END}"
        for text in (
            f"{END}\nx\n{START}",
            f"{START}\n{START}\n{END}",
            f"{START}\n{END}\n{END}",
            "",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                ulr.replace_block(text, block)

    def test_the_npm_url_is_built_from_the_package_name_not_the_repo(self):
        document = {
            "dist-tags": {"latest": "6.0.5"},
            "time": {"6.0.5": "2026-09-24T12:59:00Z"},
        }
        release = ulr.release_from_npm("@ag-bash/bash", document)
        self.assertEqual(
            release.url, "https://www.npmjs.com/package/@ag-bash/bash/v/6.0.5"
        )


class ReleaseGuardTests(unittest.TestCase):
    def test_a_non_list_is_no_release(self):
        for junk in (None, "x", 5, {"tag_name": "v1"}):
            with self.subTest(junk=junk):
                self.assertIsNone(ulr.release_from_github(junk))

    def test_junk_entries_are_skipped_not_fatal(self):
        releases = [
            None,
            5,
            "x",
            {"tag_name": 5},
            {"tag_name": None},
            {},
            github_release("v1.0.0", "2026-01-01T00:00:00Z"),
        ]
        self.assertEqual(ulr.release_from_github(releases).version, "v1.0.0")

    def test_a_release_without_a_url_renders_as_plain_text(self):
        entry = github_release("v1.0.0")
        del entry["html_url"]
        release = ulr.release_from_github([entry])
        self.assertEqual(release.url, "")
        self.assertIn("| v1.0.0 |", ulr._row(TRELIX, release))

    def test_safe_text_keeps_case_and_underscores(self):
        self.assertEqual(ulr.safe_text("Release_1.0.0-RC1"), "Release_1.0.0-RC1")


class LinkCharacterTests(unittest.TestCase):
    def test_each_markup_or_space_character_in_a_url_keeps_it_plain(self):
        for char in '()<>[]|`\\" \t\n':
            with self.subTest(char=repr(char)):
                self.assertEqual(ulr._link("v", f"https://github.com/o/r{char}x"), "v")

    def test_a_dot_in_the_host_is_not_a_wildcard(self):
        self.assertEqual(ulr._link("v", "https://githubXcom/o/r"), "v")
        self.assertEqual(ulr._link("v", "https://wwwXnpmjsXcom/o"), "v")


class CountPatternTests(unittest.TestCase):
    def test_one_repo_on_two_rows_is_listed_once_whatever_its_case(self):
        text = (
            "[a](https://github.com/O/R) (`1 commits`, x) "
            "[b](https://github.com/o/r) (`2 commits`, y)"
        )
        self.assertEqual(ulr.find_count_repos(text), ["O/R"])

    def test_repo_names_may_contain_dots(self):
        text = "[a](https://github.com/o/r.js) (`5 commits`, x)"
        self.assertEqual(ulr.find_count_repos(text), ["o/r.js"])

    def test_only_github_links_are_counted(self):
        text = (
            "[a](https://gitlab.com/o/r) (`5 commits`, x) "
            "[b](https://github.example/o/r) (`6 commits`, y)"
        )
        self.assertEqual(ulr.find_count_repos(text), [])


class LowerCountRobustnessTests(unittest.TestCase):
    TEXT = (
        "[a](https://github.com/Owner/Repo) (`100 commits`, x) and "
        "[b](https://github.com/owner/repo) (`90 commits`, y)"
    )

    def test_the_guard_ignores_case_in_both_directions(self):
        for key in ("owner/repo", "OWNER/REPO", "Owner/Repo"):
            with self.subTest(key=key):
                kept, lower = ulr.split_lower_counts(self.TEXT, {key: 50})
                self.assertEqual((kept, len(lower)), ({}, 1))

    def test_with_two_different_figures_the_larger_decides(self):
        kept, lower = ulr.split_lower_counts(self.TEXT, {"owner/repo": 95})
        self.assertEqual((kept, len(lower)), ({}, 1))
        kept, lower = ulr.split_lower_counts(self.TEXT, {"owner/repo": 105})
        self.assertEqual((kept, lower), ({"owner/repo": 105}, []))


if __name__ == "__main__":
    unittest.main()
