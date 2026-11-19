"""Tests for update_latest_releases: sources, the run, exit codes and the workflow.

No network: gh and the npm registry are replaced by fakes.
Run: python3 -m unittest discover -s scripts -p 'test_*.py' -v
"""

import contextlib
import http.client
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import update_latest_releases as ulr
from _update_releases_fixtures import AGBASH, END, GATEWAY, START, TRELIX, github_release


class GhCommitCountTests(unittest.TestCase):
    """`gh api --include` output: LF after the status line, CRLF in headers."""

    LINK = (
        '<https://api.github.com/repositories/1/commits?per_page=1&page=2>; rel="next", '
        '<https://api.github.com/repositories/1/commits?per_page=1&page=58>; rel="last"'
    )

    @staticmethod
    def _response(body, link=None):
        headers = "Content-Type: application/json\r\n"
        if link:
            headers += f"Link: {link}\r\n"
        return f"HTTP/2.0 200 OK\n{headers}\r\n{body}"

    def _count(self, output):
        with mock.patch.object(ulr, "_gh", return_value=output):
            return ulr._commit_count("o/r")

    def test_the_last_page_number_is_the_commit_count(self):
        self.assertEqual(self._count(self._response('[{"sha":"a"}]', self.LINK)), 58)

    def test_a_single_commit_repo_has_no_link_header_and_counts_one(self):
        self.assertEqual(self._count(self._response('[{"sha":"a"}]')), 1)

    def test_an_empty_list_is_an_error_not_a_count_of_zero(self):
        with self.assertRaises(ValueError):
            self._count(self._response("[]"))

    def test_a_link_header_without_a_last_page_is_an_error_not_a_count_of_one(self):
        for link in (
            '<https://api.github.com/r/commits?per_page=1&page=2>; rel="next"',
            '<https://api.github.com/r/commits?per_page=1&page=x>; rel="last"',
            '<https://api.github.com/r/commits?per_page=1>; rel="last"',
        ):
            with self.subTest(link=link), self.assertRaises(ValueError):
                self._count(self._response('[{"sha":"a"}]', link))

    def test_the_page_parameter_may_come_first_and_the_rel_may_be_unquoted(self):
        for link in (
            '<https://api.github.com/r/commits?page=58&per_page=1>; rel="last"',
            "<https://api.github.com/r/commits?per_page=1&page=58>; rel=last",
        ):
            with self.subTest(link=link):
                self.assertEqual(self._count(self._response('[{"sha":"a"}]', link)), 58)

    def test_lf_only_output_is_split_too(self):
        output = f'HTTP/2.0 200 OK\nLink: {self.LINK}\n\n[{{"sha":"a"}}]'
        self.assertEqual(self._count(output), 58)

    def test_link_text_inside_the_body_is_not_read_as_a_header(self):
        body = '[{"commit":{"message":"x page=9>; rel=\\"last\\""}}]'
        self.assertEqual(self._count(self._response(body)), 1)

    def test_a_repo_that_fails_is_skipped_and_the_rest_are_kept(self):
        def fake(repo):
            if repo == "o/private":
                raise OSError("boom")
            return 7

        with (
            mock.patch.object(ulr, "_commit_count", side_effect=fake),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            counts = ulr.load_commit_counts(["o/a", "o/private", "o/b"])
        self.assertEqual(counts, {"o/a": 7, "o/b": 7})


class LoadReleaseTests(unittest.TestCase):
    PAGE_ONE = [github_release("v2.0.0", "2026-03-01T00:00:00Z")]
    PAGE_TWO = [github_release("v3.0.0", "2026-04-01T00:00:00Z")]

    def test_github_releases_are_read_from_every_page(self):
        body = json.dumps([self.PAGE_ONE, self.PAGE_TWO])
        with mock.patch.object(ulr, "_gh", return_value=body) as gh:
            release = ulr.load_release(TRELIX)
        self.assertEqual(release.version, "v3.0.0")
        arguments = gh.call_args.args
        self.assertIn("--paginate", arguments)
        self.assertIn("--slurp", arguments)
        self.assertIn("repos/sairam0424/trelix/releases?per_page=100", arguments)

    def test_a_prefix_is_applied_to_the_flattened_pages(self):
        pages = [[github_release("gateway/v0.20.0")], [github_release("evals/v0.10.1")]]
        with mock.patch.object(ulr, "_gh", return_value=json.dumps(pages)):
            self.assertEqual(ulr.load_release(GATEWAY).version, "v0.20.0")

    def _npm_document(self, document, size_limit=None):
        response = mock.MagicMock()
        response.read.return_value = json.dumps(document).encode()
        opener = mock.MagicMock()
        opener.return_value.__enter__.return_value = response
        return opener

    def test_npm_uses_the_latest_tag_and_its_own_date_not_created(self):
        document = {
            "dist-tags": {"latest": "6.0.5"},
            "time": {
                "created": "2020-01-01T00:00:00.000Z",
                "modified": "2026-11-01T00:00:00.000Z",
                "6.0.5": "2026-09-24T12:59:00.000Z",
            },
        }
        opener = self._npm_document(document)
        with mock.patch.object(ulr.urllib.request, "urlopen", opener):
            release = ulr.load_release(AGBASH)
        self.assertEqual((release.version, release.released), ("6.0.5", "2026-09-24"))
        self.assertEqual(
            release.url, "https://www.npmjs.com/package/@ag-bash/bash/v/6.0.5"
        )
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, "https://registry.npmjs.org/@ag-bash%2Fbash")

    def test_an_oversized_npm_document_is_refused(self):
        opener = self._npm_document({"dist-tags": {}, "time": {}})
        with (
            mock.patch.object(ulr.urllib.request, "urlopen", opener),
            mock.patch.object(ulr, "MAX_NPM_DOCUMENT_BYTES", 5),
            self.assertRaises(ValueError),
        ):
            ulr.load_release(AGBASH)


class WarningTests(unittest.TestCase):
    def _warning(self, env):
        stderr = io.StringIO()
        with (
            mock.patch.dict(ulr.os.environ, env, clear=False),
            contextlib.redirect_stderr(stderr),
        ):
            ulr._warn("trelix: release lookup failed (OSError)")
        return stderr.getvalue()

    def test_on_github_actions_a_warning_is_a_workflow_annotation(self):
        text = self._warning({"GITHUB_ACTIONS": "true"})
        self.assertTrue(text.startswith("::warning title=Latest releases::trelix"))

    def test_elsewhere_it_is_a_plain_line(self):
        text = self._warning({"GITHUB_ACTIONS": "false"})
        self.assertEqual(text, "WARNING: trelix: release lookup failed (OSError)\n")


class MainTests(unittest.TestCase):
    PROJECTS = (TRELIX, GATEWAY)

    def _readme(
        self,
        tmp,
        counts_line="| **[trelix](https://github.com/sairam0424/trelix)** · `100 commits` | d |\n",
    ):
        path = Path(tmp) / "README.md"
        path.write_text(
            f"# Hi\n\n{START}\nplaceholder\n{END}\n\n{counts_line}", encoding="utf-8"
        )
        return path

    @staticmethod
    def _fetch_ok(project):
        version = {"trelix": "v3.5.1", "kelvran/gateway": "v0.20.0"}[project.label]
        return ulr.Release(version, "2026-10-29", f"https://example.test/{version}")

    @staticmethod
    def _counts_ok(repos):
        return {repo: 1881 for repo in repos}

    def _run(self, path, fetch_release, fetch_counts):
        output = io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            code = ulr.main(
                [str(path)],
                projects=self.PROJECTS,
                fetch_release=fetch_release,
                fetch_counts=fetch_counts,
            )
        return code, output.getvalue()

    def test_a_run_updates_the_table_and_the_counts_then_a_second_run_changes_nothing(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._readme(tmp)
            code, output = self._run(path, self._fetch_ok, self._counts_ok)
            first = path.read_text(encoding="utf-8")
            self.assertEqual(code, 0)
            self.assertIn("v3.5.1", first)
            self.assertIn("`1,881 commits`", first)
            self.assertIn("README.md updated", output)
            code, output = self._run(path, self._fetch_ok, self._counts_ok)
            self.assertEqual(code, 0)
            self.assertIn("No changes", output)
            self.assertEqual(path.read_text(encoding="utf-8"), first)

    def test_one_failed_lookup_keeps_that_row_and_still_updates_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._readme(tmp)
            self._run(path, self._fetch_ok, self._counts_ok)
            before = path.read_text(encoding="utf-8")

            def flaky(project):
                if project.label == "kelvran/gateway":
                    raise OSError("network down")
                return ulr.Release(
                    "v9.9.9", "2026-11-19", "https://example.test/v9.9.9"
                )

            code, _ = self._run(path, flaky, self._counts_ok)
            after = path.read_text(encoding="utf-8")
        self.assertEqual(code, 3)  # written, but not everything could be refreshed
        self.assertIn("v9.9.9", after)
        self.assertIn("v0.20.0", after)  # the previous kelvran row survived
        self.assertNotEqual(before, after)

    def test_every_kind_of_source_failure_keeps_the_previous_row(self):
        failures = (
            http.client.IncompleteRead(b"abc", 10),
            subprocess.CalledProcessError(1, "gh"),
            subprocess.TimeoutExpired("gh", 30),
            json.JSONDecodeError("bad", "doc", 0),
            OSError("down"),
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                with tempfile.TemporaryDirectory() as tmp:
                    path = self._readme(tmp)
                    self._run(path, self._fetch_ok, self._counts_ok)

                    def flaky(project, failure=failure):
                        if project.label == "kelvran/gateway":
                            raise failure
                        return self._fetch_ok(project)

                    code, _ = self._run(path, flaky, self._counts_ok)
                    text = path.read_text(encoding="utf-8")
                self.assertEqual(code, 3)
                self.assertIn("v0.20.0", text)

    def test_a_live_count_below_the_readme_figure_is_not_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._readme(tmp)
            code, _ = self._run(
                path, self._fetch_ok, lambda repos: {r: 1 for r in repos}
            )
            text = path.read_text(encoding="utf-8")
        self.assertEqual(code, 3)
        self.assertIn("`100 commits`", text)
        self.assertNotIn("`1 commits`", text)

    def test_when_everything_fails_nothing_is_written_and_the_exit_code_says_so(self):
        def down(*_):
            raise OSError("network down")

        with tempfile.TemporaryDirectory() as tmp:
            path = self._readme(tmp)
            before = path.read_text(encoding="utf-8")
            code, _ = self._run(path, down, down)
            self.assertEqual(code, 1)
            self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_missing_markers_and_missing_files_are_bad_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text("no markers here\n", encoding="utf-8")
            self.assertEqual(self._run(path, self._fetch_ok, self._counts_ok)[0], 2)
            self.assertEqual(
                self._run(Path(tmp) / "absent.md", self._fetch_ok, self._counts_ok)[0],
                2,
            )

    def test_the_default_project_list_covers_the_featured_projects(self):
        labels = [project.label for project in ulr.PROJECTS]
        for expected in (
            "trelix",
            "MindForge",
            "ag-bash",
            "kelvran/gateway",
            "kelvran/evals",
            "tracehub-mcp",
            "cost-guard-mcp",
        ):
            self.assertIn(expected, labels)
        self.assertEqual(len(labels), len(set(labels)))
        for project in ulr.PROJECTS:
            self.assertRegex(project.repo, r"^[\w.-]+/[\w.-]+$")
            self.assertIn(project.source, ("github", "npm"))
            self.assertTrue(project.source != "npm" or project.ref)


class CommitCountRequestTests(unittest.TestCase):
    """Production sees LF-only output: gh runs with text=True."""

    @staticmethod
    def _lf(link=None, body="[]"):
        headers = "Content-Type: application/json\n"
        if link:
            headers += f"Link: {link}\n"
        return f"HTTP/2.0 200 OK\n{headers}\n{body}"

    def _count(self, output):
        with mock.patch.object(ulr, "_gh", return_value=output) as gh:
            return ulr._commit_count("o/r"), gh

    def test_the_request_asks_for_one_commit_a_page_with_headers_included(self):
        link = '<https://api.github.com/r/commits?per_page=1&page=7>; rel="last"'
        number, gh = self._count(self._lf(link))
        self.assertEqual(number, 7)
        self.assertEqual(
            gh.call_args.args, ("api", "repos/o/r/commits?per_page=1", "--include")
        )

    def test_a_single_commit_without_a_link_header_counts_one(self):
        self.assertEqual(self._count(self._lf(body='[{"sha":"a"}]'))[0], 1)

    def test_link_text_in_the_body_is_not_a_header(self):
        body = '[{"commit":{"message":"page=9>; rel=\\"last\\""}}]'
        self.assertEqual(self._count(self._lf(body=body))[0], 1)

    def test_rel_is_case_insensitive(self):
        link = '<https://api.github.com/r/commits?per_page=1&page=58>; REL="LAST"'
        self.assertEqual(self._count(self._lf(link))[0], 58)

    def test_page_zero_is_refused(self):
        link = '<https://api.github.com/r/commits?per_page=1&page=0>; rel="last"'
        with self.assertRaises(ValueError):
            self._count(self._lf(link))

    def test_every_kind_of_failure_skips_only_that_repo(self):
        failures = (
            OSError("x"),
            ValueError("x"),
            subprocess.CalledProcessError(1, "gh"),
            subprocess.TimeoutExpired("gh", 30),
            http.client.IncompleteRead(b"x", 5),
        )
        for failure in failures:

            def fake(repo, failure=failure):
                if repo == "o/bad":
                    raise failure
                return 3

            with self.subTest(failure=type(failure).__name__):
                with (
                    mock.patch.object(ulr, "_commit_count", side_effect=fake),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    counts = ulr.load_commit_counts(["o/a", "o/bad"])
                self.assertEqual(counts, {"o/a": 3})


class SourceCallTests(unittest.TestCase):
    def test_gh_runs_with_a_timeout_check_and_utf8(self):
        with mock.patch.object(
            ulr.subprocess, "run", return_value=mock.Mock(stdout="out")
        ) as run:
            self.assertEqual(ulr._gh("api", "x"), "out")
        run.assert_called_once_with(
            ["gh", "api", "x"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=ulr.GH_TIMEOUT_SECONDS,
        )
        self.assertTrue(0 < ulr.GH_TIMEOUT_SECONDS <= 60)

    def test_the_npm_request_has_a_timeout(self):
        response = mock.MagicMock()
        response.read.return_value = b'{"dist-tags":{},"time":{}}'
        opener = mock.MagicMock()
        opener.return_value.__enter__.return_value = response
        with mock.patch.object(ulr.urllib.request, "urlopen", opener):
            ulr.load_release(AGBASH)
        self.assertEqual(opener.call_args.kwargs["timeout"], ulr.HTTP_TIMEOUT_SECONDS)
        self.assertTrue(0 < ulr.HTTP_TIMEOUT_SECONDS <= 60)


class DegradedRunTests(unittest.TestCase):
    """What a run that could not refresh everything must write, exit with and say."""

    PROJECTS = (TRELIX, GATEWAY)
    ROW = "| **[trelix](https://github.com/sairam0424/trelix)** · `100 commits` | d |\n"

    @staticmethod
    def _ok(project):
        version = {"trelix": "v3.5.1", "kelvran/gateway": "v0.20.0"}[project.label]
        return ulr.Release(
            version, "2026-10-29", f"https://github.com/o/r/releases/tag/{version}"
        )

    def _go(self, fetch_release, fetch_counts, on_actions="false"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text(
                f"# Hi\n\n{START}\nx\n{END}\n\n{self.ROW}", encoding="utf-8"
            )
            out, err = io.StringIO(), io.StringIO()
            with (
                mock.patch.dict(ulr.os.environ, {"GITHUB_ACTIONS": on_actions}),
                contextlib.redirect_stdout(out),
                contextlib.redirect_stderr(err),
            ):
                code = ulr.main(
                    [str(path)],
                    projects=self.PROJECTS,
                    fetch_release=fetch_release,
                    fetch_counts=fetch_counts,
                )
            return code, path.read_text(encoding="utf-8"), err.getvalue()

    def test_a_clean_run_exits_zero_and_says_nothing(self):
        code, text, err = self._go(self._ok, lambda repos: {r: 150 for r in repos})
        self.assertEqual((code, err), (0, ""))
        self.assertIn("`150 commits`", text)

    def test_a_missing_count_exits_three_keeps_the_figure_and_still_writes_the_table(
        self,
    ):
        code, text, _ = self._go(self._ok, lambda repos: {})
        self.assertEqual(code, 3)
        self.assertIn("`100 commits`", text)
        self.assertIn("v3.5.1", text)

    def test_a_count_source_that_fails_outright_exits_three(self):
        failures = (
            OSError("x"),
            ValueError("x"),
            subprocess.CalledProcessError(1, "gh"),
            subprocess.TimeoutExpired("gh", 30),
            http.client.IncompleteRead(b"x", 5),
        )
        for failure in failures:

            def broken(repos, failure=failure):
                raise failure

            with self.subTest(failure=type(failure).__name__):
                code, text, _ = self._go(self._ok, broken)
                self.assertEqual(code, 3)
                self.assertIn("v3.5.1", text)

    def test_a_held_back_count_is_reported_and_exits_three(self):
        code, text, err = self._go(self._ok, lambda repos: {r: 1 for r in repos})
        self.assertEqual(code, 3)
        self.assertIn("commit count kept", err)
        self.assertIn("`100 commits`", text)

    def test_server_text_never_reaches_a_workflow_command(self):
        def fetch(project):
            if project.label == "trelix":
                raise OSError("::error::pwned\n::add-mask::secret")
            raise subprocess.CalledProcessError(1, "gh", stderr="::error::boom")

        def counts(repos):
            raise OSError("::stop-commands::token")

        def one_good(project):
            return (
                self._ok(project)
                if project.label == "kelvran/gateway"
                else fetch(project)
            )

        _, _, err = self._go(one_good, counts, on_actions="true")
        for hostile in ("pwned", "add-mask", "boom", "stop-commands", "secret"):
            self.assertNotIn(hostile, err)
        for line in err.splitlines():
            self.assertTrue(
                line.startswith("::warning title=Latest releases::")
                or line
                == "some rows or counts could not be refreshed: see the warnings",
                line,
            )


class WorkflowContractTests(unittest.TestCase):
    WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"

    def _text(self, name):
        return (self.WORKFLOWS / name).read_text(encoding="utf-8")

    def test_every_readme_writer_shares_one_serial_concurrency_group(self):
        for name in (
            "blog-post-workflow.yml",
            "update-activity.yml",
            "update-track-record.yml",
            "update-latest-releases.yml",
        ):
            with self.subTest(name=name):
                text = self._text(name)
                self.assertIn("group: readme-writes", text)
                self.assertIn("cancel-in-progress: false", text)

    def test_the_commit_step_still_runs_after_a_degraded_update(self):
        self.assertIn(
            "if: ${{ !cancelled() }}", self._text("update-latest-releases.yml")
        )


if __name__ == "__main__":
    unittest.main()
