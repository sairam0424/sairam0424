"""Contract tests for check_readme_links.

A second independent mutation sweep (231 mutants, 78 survived) showed which
documented rules no test pinned, and a regression hunt found defects introduced
by the first round of fixes. Each test here pins one of those rules.

Run: python3 -m unittest discover -s scripts -p 'test_*.py' -v
"""

import contextlib
import http.server
import io
import re
import socket
import tempfile
import threading
import time
import tracemalloc
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import check_readme_links as crl
import test_check_readme_links as base
from test_check_readme_links_robustness import quiet_main, raw_server

BASE = ""
SERVER = None
OK = crl._Outcome(200, "image/png", b"", None)
TIMED_OUT = crl._Outcome(None, "", b"", "timed out")


def setUpModule():
    global SERVER, BASE
    SERVER = http.server.ThreadingHTTPServer(("127.0.0.1", 0), base.Handler)
    SERVER.daemon_threads = True
    BASE = f"http://127.0.0.1:{SERVER.server_address[1]}"
    threading.Thread(target=SERVER.serve_forever, daemon=True).start()


def tearDownModule():
    SERVER.shutdown()
    SERVER.server_close()


def check(path, kind, **overrides):
    options = {"timeout": 2.0, "retries": 0, "backoff": 0.0, "soft_hosts": ()}
    options.update(overrides)
    return crl.check_url(f"{BASE}{path}", kind, **options)


def write_readme(directory, body="plain text, no urls"):
    path = Path(directory) / "README.md"
    path.write_text(body, encoding="utf-8")
    return path


class ClassificationContractTests(unittest.TestCase):
    def test_the_content_type_must_start_with_image_slash(self):
        for path in ("/ctype-embedded", "/ctype-no-slash"):
            with self.subTest(path=path):
                self.assertEqual(check(path, "image").level, "fail")

    def test_badge_text_is_only_inspected_in_svg(self):
        self.assertEqual(check("/png-with-badge-text", "image").level, "ok")

    def test_undecodable_bytes_in_an_svg_do_not_break_the_check(self):
        self.assertEqual(check("/svg-bad-utf8", "image").level, "ok")

    def test_a_multiline_title_is_read(self):
        self.assertEqual(check("/svg-multiline-title", "image").level, "fail")

    def test_the_message_after_the_first_colon_is_read(self):
        # shields.io reports a bad parameter as "label: invalid query parameter: url"
        path = "/title-badge/custom%20badge:%20invalid%20query%20parameter:%20url.svg"
        self.assertEqual(check(path, "image").level, "fail")

    def test_a_long_title_is_still_read(self):
        path = "/title-badge/" + "a" * 500 + ":%20not%20found.svg"
        self.assertEqual(check(path, "image").level, "fail")

    def test_phrases_match_whole_words_only(self):
        for text in (
            "release:%20piano%20data",
            "cache:%20invalidation%20scheduled",
            "docs:%20no%20database%20errors",
        ):
            with self.subTest(text=text):
                self.assertEqual(check(f"/title-badge/{text}.svg", "image").level, "ok")

    def test_http_429_is_retried(self):
        limited = crl._Outcome(429, "text/html", b"", None)
        with (
            mock.patch.object(crl, "_fetch", side_effect=[limited, OK]) as fetch,
            mock.patch.object(crl.time, "sleep"),
        ):
            finding = crl.check_url(
                "https://a.example/a.png",
                "image",
                retries=1,
                backoff=0.0,
                soft_hosts=(),
            )
        self.assertEqual(finding.level, "ok")
        self.assertEqual(fetch.call_count, 2)

    def test_backoff_doubles_from_the_given_base(self):
        with (
            mock.patch.object(
                crl, "_fetch", side_effect=[TIMED_OUT, TIMED_OUT, TIMED_OUT, OK]
            ),
            mock.patch.object(crl.time, "sleep") as sleep,
        ):
            crl.check_url(
                "https://a.example/a.png",
                "image",
                retries=3,
                backoff=0.5,
                soft_hosts=(),
            )
        self.assertEqual(
            sleep.call_args_list, [mock.call(0.5), mock.call(1.0), mock.call(2.0)]
        )

    def test_medium_is_a_soft_host_by_default_for_links_only(self):
        self.assertEqual(crl.SOFT_HOSTS, ("medium.com",))
        with mock.patch.object(crl, "_fetch", return_value=TIMED_OUT):
            link = crl.check_url("https://www.medium.com/x", "link", retries=0)
            image = crl.check_url("https://www.medium.com/x.png", "image", retries=0)
        self.assertEqual(link.level, "warn")
        self.assertEqual(image.level, "fail")

    def test_a_garbage_status_line_counts_as_a_retryable_connection_failure(self):
        payload = b"GARBAGE not http\r\n\r\n"
        with raw_server(payload, connections=2) as (port, served):
            finding = crl.check_url(
                f"http://127.0.0.1:{port}/",
                "link",
                timeout=2.0,
                retries=1,
                backoff=0.0,
                soft_hosts=(),
            )
        self.assertEqual(finding.level, "fail")
        self.assertTrue(finding.detail.startswith("connection failed"), finding.detail)
        self.assertEqual(len(served), 2)


class ExtractionContractTests(unittest.TestCase):
    def test_data_srcset_is_not_an_image_attribute(self):
        images, _ = crl.extract_urls('<img data-srcset="https://a.example/d.png">')
        self.assertEqual(images, ())

    def test_uppercase_attributes_and_spaces_around_the_equals_sign(self):
        images, _ = crl.extract_urls(
            '<SOURCE SRCSET = "https://a.example/s.png 1x"> <img src = "https://a.example/sp.png">'
        )
        self.assertEqual(
            images, ("https://a.example/s.png", "https://a.example/sp.png")
        )

    def test_a_comma_inside_a_srcset_url_is_not_a_separator(self):
        images, _ = crl.extract_urls(
            '<source srcset="https://a.example/w_100,h_100/x.png 1x, https://a.example/y.png 2x">'
        )
        self.assertEqual(
            images, ("https://a.example/w_100,h_100/x.png", "https://a.example/y.png")
        )

    def test_empty_srcset_candidates_are_skipped(self):
        images, _ = crl.extract_urls(
            '<source srcset="https://a.example/a.png 1x,  , https://a.example/b.png 2x">'
        )
        self.assertEqual(images, ("https://a.example/a.png", "https://a.example/b.png"))

    def test_markdown_image_forms(self):
        images, links = crl.extract_urls(
            "![x](<https://a.example/ab.png>) ![](https://a.example/empty.png) "
            "![x]( https://a.example/sp1.png) ![x](https://a.example/sp2.png )"
        )
        self.assertEqual(
            images,
            (
                "https://a.example/ab.png",
                "https://a.example/empty.png",
                "https://a.example/sp1.png",
                "https://a.example/sp2.png",
            ),
        )
        self.assertEqual(links, ())

    def test_bare_urls_are_case_insensitive_and_stop_at_brackets(self):
        _, links = crl.extract_urls("HTTPS://A.EXAMPLE/UP and [https://a.example/br]")
        self.assertEqual(links, ("HTTPS://A.EXAMPLE/UP", "https://a.example/br"))

    def test_each_trailing_punctuation_mark_is_stripped(self):
        _, links = crl.extract_urls(
            "https://a.example/c, https://a.example/d: https://a.example/e! https://a.example/f?"
        )
        self.assertEqual(
            links,
            (
                "https://a.example/c",
                "https://a.example/d",
                "https://a.example/e",
                "https://a.example/f",
            ),
        )

    def test_underscore_emphasis_around_a_url_is_stripped_but_a_real_underscore_stays(
        self,
    ):
        _, links = crl.extract_urls(
            "_https://a.example/ital_ __https://a.example/b__ https://a.example/Foo_"
        )
        self.assertEqual(
            links,
            ("https://a.example/ital", "https://a.example/b", "https://a.example/Foo_"),
        )

    def test_an_empty_image_source_is_ignored(self):
        images, links = crl.extract_urls('<img src=""> <img src="   ">')
        self.assertEqual((images, links), ((), ()))

    def test_fragment_and_mailto_sources_are_not_images(self):
        images, _ = crl.extract_urls('<img src="#frag"> <img src="mailto:a@b.c">')
        self.assertEqual(images, ())

    def test_only_entities_with_a_semicolon_are_decoded(self):
        _, links = crl.extract_urls(
            "[a](https://a.example/p?x=1&region=us) [b](https://a.example/q?x=1&amp;y=2) "
            "[c](https://a.example/r?x=1&#38;y=2) [d](https://a.example/s?copy&copy)"
        )
        self.assertEqual(
            links,
            (
                "https://a.example/p?x=1&region=us",
                "https://a.example/q?x=1&y=2",
                "https://a.example/r?x=1&y=2",
                "https://a.example/s?copy&copy",
            ),
        )

    def test_a_greater_than_sign_inside_an_attribute_does_not_end_the_tag(self):
        images, links = crl.extract_urls(
            '<img alt="a > b" src="https://a.example/gt.png"> <img title="1>0" width="3" src="https://a.example/gt3.png">'
        )
        self.assertEqual(
            images, ("https://a.example/gt.png", "https://a.example/gt3.png")
        )
        self.assertEqual(links, ())

    def test_a_comment_marker_in_a_code_span_does_not_hide_the_rest(self):
        images, links = crl.extract_urls(
            "Start a comment with `<!--` in HTML.\n\n[later](https://a.example/after) ![i](https://a.example/i.png)"
        )
        self.assertEqual(images, ("https://a.example/i.png",))
        self.assertEqual(links, ("https://a.example/after",))

    def test_many_unclosed_tags_are_fast(self):
        for source in ("<img " * 20000, "<source " * 20000):
            with self.subTest(source=source[:8]):
                started = time.monotonic()
                crl.extract_urls(source)
                self.assertLess(time.monotonic() - started, 3.0)

    def test_many_unclosed_title_tags_are_fast(self):
        started = time.monotonic()
        crl._badge_phrase(("<title" * 18000).encode(), crl.BROKEN_BADGE_PHRASES)
        self.assertLess(time.monotonic() - started, 3.0)


class RequestContractTests(unittest.TestCase):
    def test_userinfo_is_dropped_and_ipv6_keeps_its_brackets(self):
        self.assertEqual(
            crl._request_url("http://user:pw@127.0.0.1:8080/x"),
            "http://127.0.0.1:8080/x",
        )
        self.assertEqual(crl._request_url("http://[::1]:8080/x"), "http://[::1]:8080/x")

    def test_idn_hosts_become_ascii(self):
        self.assertEqual(
            crl._request_url("http://ｌｏｃａｌｈｏｓｔ:8080/x"),
            "http://localhost:8080/x",
        )
        self.assertEqual(
            crl._request_url("http://bücher.example/x"),
            "http://xn--bcher-kva.example/x",
        )

    def test_the_query_is_encoded_but_existing_escapes_and_brackets_survive(self):
        self.assertEqual(
            crl._request_url("http://h.example/p?a b&c=é&d=%2F&e[]=1"),
            "http://h.example/p?a%20b&c=%C3%A9&d=%2F&e[]=1",
        )

    def test_unusable_urls_are_rejected(self):
        for url in (
            "http://127.0.0.1:99999/x",
            "http://:80/x",
            "ftp://127.0.0.1:1/x",
            "mailto:a@b.c",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                crl._request_url(url)

    def test_the_fragment_is_never_sent(self):
        self.assertEqual(
            crl._request_url("http://h.example/p#frag"), "http://h.example/p"
        )

    def test_a_non_http_url_is_invalid_without_any_connection(self):
        finding = crl.check_url(
            "ftp://127.0.0.1:1/x",
            "image",
            timeout=1.0,
            retries=0,
            backoff=0.0,
            soft_hosts=(),
        )
        self.assertEqual((finding.level, finding.detail), ("fail", "invalid URL"))

    def test_userinfo_urls_are_fetched_without_credentials(self):
        port = BASE.rsplit(":", 1)[1]
        finding = crl.check_url(
            f"http://user:pw@127.0.0.1:{port}/ok.svg",
            "image",
            timeout=2.0,
            retries=0,
            backoff=0.0,
            soft_hosts=(),
        )
        self.assertEqual(finding.level, "ok")


class ReportContractTests(unittest.TestCase):
    def test_counts_and_plurals(self):
        findings = (
            crl.Finding("https://a.example/1.svg", "image", "fail", "HTTP 402"),
            crl.Finding("https://a.example/2.svg", "image", "fail", "HTTP 404"),
            crl.Finding("https://b.example/y", "link", "warn", "HTTP 403 (bot wall)"),
            crl.Finding("https://b.example/z", "link", "ok", "HTTP 200"),
            crl.Finding("https://b.example/w", "link", "ok", "HTTP 200"),
        )
        self.assertIn(
            "2 failures, 1 warning, 5 checked (2 images, 3 links)",
            crl.render_report(findings),
        )
        single = (crl.Finding("https://a.example/1.svg", "image", "fail", "HTTP 402"),)
        self.assertIn(
            "1 failure, 0 warnings, 1 checked (1 image, 0 links)",
            crl.render_report(single),
        )

    def test_a_warning_is_not_listed_as_a_failure(self):
        report = crl.render_report(
            (crl.Finding("https://b.example/y", "link", "warn", "HTTP 403"),)
        )
        self.assertIn("0 failures, 1 warning", report)
        self.assertEqual(report.count("| Kind |"), 1)
        self.assertGreater(report.index("| Kind |"), report.index("<details>"))

    def test_the_detail_cell_is_a_length_limited_code_span_without_backticks(self):
        self.assertEqual(
            crl._detail_cell("x" * 5000), "`" + "x" * crl.MAX_DETAIL_CHARS + "`"
        )
        self.assertNotIn("`", crl._detail_cell("a `code` b")[1:-1])

    def test_the_url_cell_collapses_whitespace_and_is_length_limited(self):
        self.assertEqual(
            crl._url_cell("https://a.example/a\nb"), "https://a.example/a b"
        )
        long_cell = crl._url_cell("https://a.example/" + "x" * 400)
        self.assertEqual(len(long_cell), crl.MAX_URL_CHARS)
        self.assertTrue(long_cell.endswith("..."))

    def test_the_report_is_ascii_even_for_non_ascii_paths(self):
        report = crl.render_report(
            (crl.Finding("assets/café.png", "image", "fail", "file not found"),)
        )
        self.assertTrue(report.isascii())

    def test_github_auto_references_in_server_text_are_inert_inside_a_code_span(self):
        finding = crl.Finding(
            "https://a.example/x",
            "link",
            "fail",
            "www.evil.example octocat/hello-world#1 :+1:",
        )
        row = next(
            line
            for line in crl.render_report((finding,)).splitlines()
            if line.startswith("| link")
        )
        self.assertRegex(row, r"^\| link \| `[^`]*` \| `[^`]*` \|$")

    def test_the_documented_limits_are_exactly_200_and_300_characters(self):
        self.assertEqual(
            len(crl._detail_cell("x" * 5000)), 202
        )  # 200 plus two backticks
        exact = "https://a.example/" + "x" * (300 - len("https://a.example/"))
        self.assertEqual(crl._url_cell(exact), exact)
        self.assertEqual(len(crl._url_cell(exact + "y")), 300)

    def test_every_markup_character_is_removed_from_details(self):
        for char in '[]<>@|`*!\\"{}':
            with self.subTest(char=char):
                self.assertNotIn(char, crl._detail_cell(f"a{char}b")[1:-1])

    def test_details_collapse_all_whitespace_to_single_spaces(self):
        self.assertEqual(crl._detail_cell("a\nb\r\n\tc"), "`a b c`")

    def test_main_prints_the_report_to_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = crl.main([str(write_readme(tmp))])
        self.assertEqual(code, 0)
        self.assertIn("README image and link check", output.getvalue())


class CliContractTests(unittest.TestCase):
    def test_main_passes_every_option_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = str(write_readme(tmp))
            with mock.patch.object(
                crl, "check_readme", return_value=()
            ) as check_readme:
                quiet_main(
                    [readme, "--timeout", "7", "--retries", "4", "--workers", "3"]
                )
                defaults = check_readme.call_args.kwargs
                quiet_main(
                    [readme, "--soft-host", "A.example", "--soft-host", "b.example"]
                )
                custom = check_readme.call_args.kwargs
        self.assertEqual(
            (defaults["timeout"], defaults["retries"], defaults["workers"]), (7.0, 4, 3)
        )
        self.assertEqual(defaults["soft_hosts"], ("medium.com",))
        self.assertEqual(custom["soft_hosts"], ("a.example", "b.example"))

    def test_invalid_numeric_options_are_bad_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = str(write_readme(tmp))
            for option in (
                ["--timeout", "-1"],
                ["--timeout", "0"],
                ["--timeout", "nan"],
                ["--timeout", "inf"],
                ["--retries", "-1"],
                ["--workers", "0"],
            ):
                with self.subTest(option=option):
                    self.assertEqual(quiet_main([readme, *option]), 2)

    def test_check_readme_survives_zero_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = crl.check_readme(
                write_readme(tmp),
                timeout=1.0,
                retries=0,
                backoff=0.0,
                workers=0,
                soft_hosts=(),
            )
        self.assertEqual(findings, ())


class FetchErrorContractTests(unittest.TestCase):
    def test_timeouts_and_connection_errors_are_told_apart(self):
        cases = (
            (TimeoutError("read"), "timed out"),
            (socket.timeout("read"), "timed out"),
            (urllib.error.URLError(TimeoutError("connect")), "timed out"),
            (urllib.error.URLError("refused"), "connection failed: refused"),
        )
        for raised, expected in cases:
            with self.subTest(raised=repr(raised)):
                opener = mock.Mock()
                opener.open.side_effect = raised
                with mock.patch.object(
                    crl.urllib.request, "build_opener", return_value=opener
                ):
                    outcome = crl._fetch("http://a.example/x", 1.0)
                self.assertEqual(outcome.error, expected)


class LocalPathContractTests(unittest.TestCase):
    def test_an_existing_relative_image_is_found_next_to_the_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "assets").mkdir()
            (Path(tmp) / "assets" / "zz-contract-test.png").write_bytes(b"png")
            readme = write_readme(tmp, "![x](assets/zz-contract-test.png)")
            findings = crl.check_readme(
                readme, timeout=1.0, retries=0, backoff=0.0, workers=1, soft_hosts=()
            )
        self.assertEqual([f.level for f in findings], ["ok"])

    def test_a_symlink_loop_error_is_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                Path, "resolve", side_effect=RuntimeError("Symlink loop")
            ):
                finding = crl.check_local_image("a.png", Path(tmp))
        self.assertEqual((finding.level, finding.detail), ("fail", "invalid path"))


class RedirectBodyContractTests(unittest.TestCase):
    def test_a_huge_redirect_body_is_not_loaded_into_memory(self):
        tracemalloc.start()
        try:
            finding = check("/redirect-big", "image", timeout=20.0)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        self.assertEqual(finding.level, "ok")
        self.assertLess(peak, 16 * 1024 * 1024)

    def test_every_redirect_status_bounds_the_body(self):
        for status in (301, 303, 307, 308):
            with self.subTest(status=status):
                tracemalloc.start()
                try:
                    finding = check(f"/redirect-big/{status}", "image", timeout=20.0)
                    peak = tracemalloc.get_traced_memory()[1]
                finally:
                    tracemalloc.stop()
                self.assertEqual(finding.level, "ok")
                self.assertLess(peak, 16 * 1024 * 1024)

    def test_the_bounded_body_reads_at_most_its_limit(self):
        body = crl._BoundedBody(io.BytesIO(b"x" * (crl.MAX_REDIRECT_BODY * 4)))
        self.assertEqual(len(body.read()), crl.MAX_REDIRECT_BODY)
        self.assertEqual(len(body.read(10)), 10)


if __name__ == "__main__":
    unittest.main()
