"""Robustness tests for check_readme_links.

Written after an independent review reproduced crashes, truncated URLs, unescaped
server text in the report, and 31 of 67 mutants surviving the first test suite.
Each test pins one behaviour so that regressing it fails loudly.

Run: python3 -m unittest discover -s scripts -p 'test_*.py' -v
"""

import contextlib
import http.server
import io
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import check_readme_links as crl
import test_check_readme_links as base  # reuses its Handler, ROUTES and fixtures

BASE = ""
SERVER = None


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


def quiet_main(argv):
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        return crl.main(argv)


@contextlib.contextmanager
def raw_server(payload, connections=1):
    """A TCP server that answers connections with arbitrary bytes.

    Yields (port, served) where served is a list that gets one entry per
    connection the server handled.
    """
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(connections)
    listener.settimeout(5)
    served = []

    def serve():
        try:
            for _ in range(connections):
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(2)
                    with contextlib.suppress(OSError):
                        connection.recv(4096)
                    connection.sendall(payload)
                served.append(1)
        except OSError:
            pass

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        yield listener.getsockname()[1], served
    finally:
        listener.close()
        thread.join(timeout=3)


class ExtractRobustnessTests(unittest.TestCase):
    def test_balanced_parentheses_stay_inside_urls(self):
        images, links = crl.extract_urls(
            "[w](https://en.wikipedia.org/wiki/Foo_(bar)) "
            "![x](https://a.example/i_(1).png) "
            "https://a.example/b_(c) (see https://a.example/z)"
        )
        self.assertEqual(images, ("https://a.example/i_(1).png",))
        self.assertEqual(
            links,
            (
                "https://en.wikipedia.org/wiki/Foo_(bar)",
                "https://a.example/b_(c)",
                "https://a.example/z",
            ),
        )

    def test_html_entities_in_urls_are_decoded(self):
        images, links = crl.extract_urls(
            '<img src="https://a.example/i.svg?style=flat&amp;logo=x"> '
            '<a href="https://a.example/?a=1&amp;b=2">x</a>'
        )
        self.assertEqual(images, ("https://a.example/i.svg?style=flat&logo=x",))
        self.assertEqual(links, ("https://a.example/?a=1&b=2",))

    def test_emphasis_and_code_wrappers_are_not_part_of_the_url(self):
        _, links = crl.extract_urls(
            "**https://a.example/bold** ~~https://a.example/strike~~ `https://a.example/code`"
        )
        self.assertEqual(
            links,
            (
                "https://a.example/bold",
                "https://a.example/strike",
                "https://a.example/code",
            ),
        )

    def test_only_img_and_source_tags_are_images(self):
        images, links = crl.extract_urls(
            '<script src="https://a.example/x.js"></script> '
            '<video src="https://a.example/v.mp4"></video> '
            '<iframe src="https://a.example/f.html"></iframe> '
            '<img data-src="https://a.example/lazy.png">'
        )
        self.assertEqual(images, ())
        self.assertEqual(
            links,
            (
                "https://a.example/x.js",
                "https://a.example/v.mp4",
                "https://a.example/f.html",
                "https://a.example/lazy.png",
            ),
        )

    def test_unquoted_and_uppercase_attributes_are_images(self):
        images, _ = crl.extract_urls(
            '<img src=https://a.example/uq.png alt=x> <IMG SRC="https://a.example/UP.png">'
        )
        self.assertEqual(
            images, ("https://a.example/uq.png", "https://a.example/UP.png")
        )

    def test_markdown_image_titles_in_every_form(self):
        images, links = crl.extract_urls(
            "![t](https://a.example/t1.png 'Title') "
            '![t](https://a.example/t2.png "Title") '
            "![t](https://a.example/t3.png (Title))"
        )
        self.assertEqual(
            images,
            (
                "https://a.example/t1.png",
                "https://a.example/t2.png",
                "https://a.example/t3.png",
            ),
        )
        self.assertEqual(links, ())

    def test_srcset_candidates_without_a_space_after_the_comma(self):
        images, links = crl.extract_urls(
            '<source srcset="https://a.example/1.png 1x,https://a.example/2.png 2x">'
        )
        self.assertEqual(images, ("https://a.example/1.png", "https://a.example/2.png"))
        self.assertEqual(links, ())

    def test_a_space_inside_src_does_not_invent_a_link(self):
        images, links = crl.extract_urls('<img src="https://a.example/a b.png">')
        self.assertEqual(images, ("https://a.example/a b.png",))
        self.assertEqual(links, ())

    def test_protocol_relative_images_are_checked_as_https(self):
        images, _ = crl.extract_urls('<img src="//cdn.example/x.png">')
        self.assertEqual(images, ("https://cdn.example/x.png",))

    def test_multiline_comments_are_ignored(self):
        images, links = crl.extract_urls(
            '<!--\n<img src="https://hidden.example/a.png">\n-->'
        )
        self.assertEqual((images, links), ((), ()))

    def test_an_unclosed_comment_marker_is_literal_so_nothing_is_skipped(self):
        # A browser would swallow the rest of the file, but a "<!--" in prose or a
        # code span must never make the checker silently stop checking.
        images, _ = crl.extract_urls('<!-- <img src="https://shown.example/b.png">')
        self.assertEqual(images, ("https://shown.example/b.png",))

    def test_many_unclosed_comments_are_linear_time(self):
        started = time.monotonic()
        crl.extract_urls("<!--" * 20000)
        self.assertLess(time.monotonic() - started, 3.0)


class FetchRobustnessTests(unittest.TestCase):
    def test_any_2xx_counts_as_success(self):
        self.assertEqual(check("/created.svg", "image").level, "ok")
        self.assertEqual(check("/nocontent", "link").level, "ok")

    def test_every_broken_badge_phrase_fails(self):
        for phrase in (
            "inaccessible",
            "invalid",
            "not%20found",
            "no%20releases",
            "no%20tags",
            "no%20data",
        ):
            with self.subTest(phrase=phrase):
                finding = check(f"/badge/{phrase}.svg", "image")
                self.assertEqual(finding.level, "fail")
                self.assertIn("error badge", finding.detail)

    def test_badge_text_in_only_the_title_or_a_single_quoted_aria_label_fails(self):
        for path in (
            "/title-badge/release:%20inaccessible.svg",
            "/aria-single/release:%20inaccessible.svg",
        ):
            with self.subTest(path=path):
                self.assertEqual(check(path, "image").level, "fail")

    def test_badge_phrases_are_case_insensitive(self):
        self.assertEqual(check("/badge/INACCESSIBLE.svg", "image").level, "fail")

    def test_the_badge_message_is_read_not_the_whole_label(self):
        for path in (
            "/title-badge/cache%20invalidation:%20passing.svg",
            "/title-badge/no%20data%20race:%20passing.svg",
        ):
            with self.subTest(path=path):
                self.assertEqual(check(path, "image").level, "ok")

    def test_an_uppercase_svg_content_type_is_still_inspected(self):
        finding = check("/upper-badge.svg", "image")
        self.assertEqual(finding.level, "fail")
        self.assertIn("error badge", finding.detail)

    def test_non_ascii_urls_are_percent_encoded_not_a_crash(self):
        base.Handler.hits.pop("/%C3%A9.svg", None)
        finding = crl.check_url(
            f"{BASE}/é.svg", "image", timeout=2.0, retries=0, backoff=0.0, soft_hosts=()
        )
        self.assertEqual(finding.level, "ok")
        self.assertEqual(base.Handler.hits["/%C3%A9.svg"], 1)

    def test_spaces_in_urls_are_percent_encoded(self):
        finding = crl.check_url(
            f"{BASE}/with space.svg",
            "image",
            timeout=2.0,
            retries=0,
            backoff=0.0,
            soft_hosts=(),
        )
        self.assertEqual(finding.level, "ok")

    def test_a_malformed_url_is_a_finding_not_an_exception(self):
        finding = crl.check_url(
            "http://[::1/x.png",
            "image",
            timeout=1.0,
            retries=0,
            backoff=0.0,
            soft_hosts=(),
        )
        self.assertEqual(finding.level, "fail")
        self.assertIn("invalid url", finding.detail.lower())

    def test_an_unexpected_exception_becomes_a_failure(self):
        with mock.patch.object(crl, "_fetch", side_effect=RuntimeError("boom")):
            finding = crl.check_url(
                "https://a.example/x.png",
                "image",
                retries=0,
                backoff=0.0,
                soft_hosts=(),
            )
        self.assertEqual(finding.level, "fail")
        self.assertIn("RuntimeError", finding.detail)

    def test_a_redirect_to_ftp_never_contacts_the_ftp_server(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            listener.settimeout(0.5)
            base.Handler.ftp_port = listener.getsockname()[1]
            finding = check("/redirect-ftp-live", "image")
            self.assertEqual(finding.level, "fail")
            self.assertIn("redirect refused", finding.detail)
            with self.assertRaises((TimeoutError, BlockingIOError, socket.timeout)):
                listener.accept()

    def test_five_redirects_are_followed_and_six_are_refused(self):
        self.assertEqual(check("/hop/5", "image").level, "ok")
        finding = check("/hop/6", "image")
        self.assertEqual(finding.level, "fail")
        self.assertIn("redirect refused", finding.detail)

    def test_soft_hosts_excuse_network_errors_on_links_only(self):
        soft = ("127.0.0.1",)
        self.assertEqual(check("/missing", "link", soft_hosts=soft).level, "fail")
        self.assertEqual(
            check("/slow", "image", timeout=0.2, soft_hosts=soft).level, "fail"
        )


class RetryTests(unittest.TestCase):
    OK = crl._Outcome(200, "image/png", b"", None)

    def test_timeouts_and_connection_errors_are_retried_with_backoff(self):
        outcomes = [
            crl._Outcome(None, "", b"", "timed out"),
            crl._Outcome(None, "", b"", "connection failed: boom"),
            self.OK,
        ]
        with (
            mock.patch.object(crl, "_fetch", side_effect=outcomes) as fetch,
            mock.patch.object(crl.time, "sleep") as sleep,
        ):
            finding = crl.check_url(
                "https://a.example/a.png",
                "image",
                timeout=1.0,
                retries=2,
                backoff=1.0,
                soft_hosts=(),
            )
        self.assertEqual(finding.level, "ok")
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(1.0), mock.call(2.0)])

    def test_a_refused_redirect_is_not_retried(self):
        refused = crl._Outcome(
            None, "", b"", "redirect refused: ftp scheme not allowed"
        )
        with (
            mock.patch.object(crl, "_fetch", return_value=refused) as fetch,
            mock.patch.object(crl.time, "sleep"),
        ):
            finding = crl.check_url(
                "https://a.example/a.png",
                "image",
                retries=3,
                backoff=1.0,
                soft_hosts=(),
            )
        self.assertEqual(finding.level, "fail")
        self.assertEqual(fetch.call_count, 1)


class LocalImageRobustnessTests(unittest.TestCase):
    def _repo(self, tmp):
        root = Path(tmp) / "repo"
        (root / "assets").mkdir(parents=True)
        (root / "assets" / "a.png").write_bytes(b"png")
        (root / "assets" / "a b.png").write_bytes(b"png")
        return root

    def test_query_fragment_percent_encoding_and_root_relative_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            for path in (
                "assets/a.png?raw=true",
                "assets/a.png#fragment",
                "assets/a%20b.png",
                "/assets/a.png",
                "./assets/a.png",
            ):
                with self.subTest(path=path):
                    self.assertEqual(crl.check_local_image(path, root).level, "ok")

    def test_an_existing_file_outside_the_repo_is_still_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            (Path(tmp) / "outside.gif").write_bytes(b"GIF89a")
            finding = crl.check_local_image("../outside.gif", root)
        self.assertEqual(finding.level, "fail")
        self.assertIn("escapes", finding.detail)

    def test_a_directory_is_not_an_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                crl.check_local_image("assets", self._repo(tmp)).level, "fail"
            )

    def test_a_nul_byte_is_a_failure_not_an_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                crl.check_local_image("a\x00b.png", self._repo(tmp)).level, "fail"
            )


class ReadmeRobustnessTests(unittest.TestCase):
    def _readme(self, tmp, body, *, binary=False):
        path = Path(tmp) / "README.md"
        if binary:
            path.write_bytes(body)
        else:
            path.write_text(body, encoding="utf-8")
        return path

    def _run(self, readme):
        return crl.check_readme(
            readme, timeout=2.0, retries=0, backoff=0.0, workers=4, soft_hosts=()
        )

    def test_an_uppercase_scheme_is_fetched_not_read_from_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            upper = BASE.replace("http://", "HTTP://", 1)
            findings = self._run(self._readme(tmp, f'<img src="{upper}/ok.svg">'))
        self.assertEqual([f.level for f in findings], ["ok"])

    def test_a_readme_that_is_not_valid_utf8_is_still_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = b'caf\xe9 <img src="' + BASE.encode() + b'/ok.svg">'
            findings = self._run(self._readme(tmp, body, binary=True))
        self.assertEqual([f.level for f in findings], ["ok"])

    def test_parentheses_and_ampersand_entities_work_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = self._readme(
                tmp,
                f'[w]({BASE}/wiki/Foo_(bar)) <img src="{BASE}/q?a=1&amp;b=2"> ![i]({BASE}/i_(1).png)',
            )
            findings = self._run(readme)
        self.assertEqual(sorted(f.level for f in findings), ["ok", "ok", "ok"])

    def test_a_crashing_worker_is_contained_as_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = self._readme(
                tmp, f'<img src="{BASE}/ok.svg"> [p]({BASE}/page.html)'
            )
            with mock.patch.object(crl, "check_url", side_effect=RuntimeError("boom")):
                findings = self._run(readme)
        self.assertEqual([f.level for f in findings], ["fail", "fail"])
        self.assertTrue(
            all("checker error: RuntimeError" in f.detail for f in findings)
        )


class CliRobustnessTests(unittest.TestCase):
    def _readme(self, tmp):
        path = Path(tmp) / "README.md"
        path.write_text("plain text, no urls", encoding="utf-8")
        return path

    def test_an_unwritable_report_path_is_bad_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = quiet_main(
                [str(self._readme(tmp)), "--report", "/nonexistent-dir/report.md"]
            )
        self.assertEqual(code, 2)

    def test_an_internal_error_exits_3_not_the_failures_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                crl, "check_readme", side_effect=RuntimeError("boom")
            ):
                code = quiet_main([str(self._readme(tmp))])
        self.assertEqual(code, 3)

    def test_soft_hosts_are_normalised_and_validated(self):
        self.assertEqual(
            crl.parse_soft_hosts(["Medium.COM", " dev.to "]), ("medium.com", "dev.to")
        )
        self.assertEqual(crl.parse_soft_hosts([""]), ())
        for bad in ("https://medium.com", "a/b", "has space"):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                crl.parse_soft_hosts([bad])

    def test_a_url_shaped_soft_host_is_bad_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = quiet_main(
                [str(self._readme(tmp)), "--soft-host", "https://medium.com"]
            )
        self.assertEqual(code, 2)


class ReportSanitisingTests(unittest.TestCase):
    HOSTILE = "bad [click](https://evil.example) @octocat | <img src=x>\nline2"

    def test_server_supplied_text_cannot_inject_markdown_mentions_or_html(self):
        finding = crl.Finding("https://a.example/x`|y", "link", "fail", self.HOSTILE)
        report = crl.render_report((finding,))
        row = next(line for line in report.splitlines() if line.startswith("| link"))
        for forbidden in ("[click]", "@octocat", "<img", "line2\n"):
            self.assertNotIn(forbidden, report)
        self.assertEqual(row.count("|"), 4)
        self.assertEqual(
            row.count("`"), 4
        )  # one code span for the URL, one for the detail

    def test_details_are_length_limited(self):
        finding = crl.Finding("https://a.example/x", "link", "fail", "x" * 5000)
        report = crl.render_report((finding,))
        self.assertLess(max(len(line) for line in report.splitlines()), 400)

    def test_a_garbage_status_line_from_a_real_socket_is_sanitised_end_to_end(self):
        payload = (
            b"GARBAGE [click](https://evil.example) @octocat | <img src=x>\r\n\r\n"
        )
        with raw_server(payload) as (port, _):
            finding = crl.check_url(
                f"http://127.0.0.1:{port}/",
                "link",
                timeout=2.0,
                retries=0,
                backoff=0.0,
                soft_hosts=(),
            )
        self.assertEqual(finding.level, "fail")
        report = crl.render_report((finding,))
        for forbidden in ("[click]", "@octocat", "<img"):
            self.assertNotIn(forbidden, report)
        row = next(line for line in report.splitlines() if line.startswith("| link"))
        self.assertEqual(row.count("|"), 4)


if __name__ == "__main__":
    unittest.main()
