"""Tests for check_readme_links, run against a local HTTP server.

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
import urllib.parse
from pathlib import Path

import check_readme_links as crl

SVG_OK = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Python</title><path d="M0 0h1v1z"/></svg>'
SVG_ERROR_BADGE = (
    b'<svg xmlns="http://www.w3.org/2000/svg" aria-label="release: inaccessible">'
    b"<title>release: inaccessible</title></svg>"
)
SVG_COORDINATES = (
    b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M404 404l40 4z"/></svg>'
)
SVG_RATE_LIMITED_BADGE = (
    b'<svg xmlns="http://www.w3.org/2000/svg" aria-label="downloads: rate limited by upstream service">'
    b"<title>downloads: rate limited by upstream service</title></svg>"
)

# path -> (status, content type, body)
ROUTES = {
    "/ok.svg": (200, "image/svg+xml", SVG_OK),
    "/ok.png": (200, "image/png", b"\x89PNG\r\n"),
    "/coordinates.svg": (200, "image/svg+xml", SVG_COORDINATES),
    "/error-badge.svg": (200, "image/svg+xml;charset=utf-8", SVG_ERROR_BADGE),
    "/rate-limited-badge.svg": (200, "image/svg+xml", SVG_RATE_LIMITED_BADGE),
    "/page.html": (200, "text/html", b"<html></html>"),
    "/disabled.svg": (402, "text/plain; charset=utf-8", b"The deployment is disabled"),
    "/missing": (404, "text/html", b"nope"),
    "/gone": (410, "text/html", b"gone"),
    "/forbidden": (403, "text/html", b"wall"),
    "/unauthorized": (401, "text/html", b"wall"),
    "/linkedin": (999, "text/html", b"wall"),
    "/limited": (429, "text/html", b"slow down"),
    "/broken": (500, "text/html", b"boom"),
    "/created.svg": (201, "image/svg+xml", SVG_OK),
    "/nocontent": (204, "text/html", b""),
    "/upper-badge.svg": (200, "IMAGE/SVG+XML", SVG_ERROR_BADGE),
    # Raw request paths, exactly as a client must send them (percent-encoded).
    "/%C3%A9.svg": (200, "image/svg+xml", SVG_OK),
    "/with%20space.svg": (200, "image/svg+xml", SVG_OK),
    "/q?a=1&b=2": (200, "image/svg+xml", SVG_OK),
    "/wiki/Foo_(bar)": (200, "text/html", b"<html></html>"),
    "/i_(1).png": (200, "image/png", b"\x89PNG\r\n"),
}


def _badge(label_text, *, title=True, aria=None):
    """An SVG badge like the ones badge services return, with chosen text sources."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg"']
    if aria:
        parts.append(f" aria-label={aria}{label_text}{aria}")
    parts.append(">")
    if title:
        parts.append(f"<title>{label_text}</title>")
    parts.append("</svg>")
    return "".join(parts).encode()


class Handler(http.server.BaseHTTPRequestHandler):
    hits = {}
    lock = threading.Lock()
    ftp_port = None  # set by the test that needs a live listener to prove it is never contacted

    def log_message(self, *args):
        pass

    def _count(self, key):
        with Handler.lock:
            Handler.hits[key] = Handler.hits.get(key, 0) + 1
            return Handler.hits[key]

    def _send(self, status, ctype, body, headers=()):
        try:
            self.send_response(status)
            if ctype:
                self.send_header("Content-Type", ctype)
            for name, value in headers:
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the client gave up (timeout tests); nothing to report

    def _dynamic(self, path):
        """Routes whose response depends on the path. Returns None when not dynamic."""
        route = urllib.parse.urlsplit(path).path
        prefix, _, rest = route[1:].partition("/")
        text = (
            urllib.parse.unquote(rest[: -len(".svg")]) if rest.endswith(".svg") else ""
        )
        if prefix == "badge":
            return 200, "image/svg+xml", _badge(f"release: {text}", aria='"')
        if prefix == "title-badge":
            return 200, "image/svg+xml", _badge(text)
        if prefix == "aria-single":
            return 200, "image/svg+xml", _badge(text, title=False, aria="'")
        if prefix == "hop":
            remaining = int(rest)
            if remaining == 0:
                return ROUTES["/ok.svg"]
            return 302, "", b"", (("Location", f"/hop/{remaining - 1}"),)
        if route == "/redirect-ftp-live":
            return (
                302,
                "",
                b"",
                (("Location", f"ftp://127.0.0.1:{Handler.ftp_port}/x.svg"),),
            )
        return None

    def do_GET(self):
        path = self.path
        count = self._count(path)
        dynamic = self._dynamic(path)
        if dynamic is not None:
            self._send(*dynamic)
            return
        if path == "/flaky.svg":
            status, ctype, body = (
                (503, "text/plain", b"later") if count == 1 else ROUTES["/ok.svg"]
            )
        elif path == "/recovering-badge.svg":
            status, ctype, body = (
                ROUTES["/rate-limited-badge.svg"] if count == 1 else ROUTES["/ok.svg"]
            )
        elif path == "/slow":
            time.sleep(1.0)
            status, ctype, body = 200, "text/html", b"late"
        elif path == "/redirect-ok":
            self.send_response(302)
            self.send_header("Location", "/ok.svg")
            self.end_headers()
            return
        elif path == "/redirect-ftp":
            self.send_response(302)
            self.send_header("Location", "ftp://127.0.0.1:1/x.svg")
            self.end_headers()
            return
        elif path in ROUTES:
            status, ctype, body = ROUTES[path]
        else:
            status, ctype, body = 404, "text/plain", b"unknown route"
        self._send(status, ctype, body)


def setUpModule():
    global SERVER, BASE
    SERVER = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    SERVER.daemon_threads = True
    BASE = f"http://127.0.0.1:{SERVER.server_address[1]}"
    threading.Thread(target=SERVER.serve_forever, daemon=True).start()


def tearDownModule():
    SERVER.shutdown()
    SERVER.server_close()


def quiet_main(argv):
    """Run main() without letting its report and errors flood the test output."""
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        return crl.main(argv)


def fast_check(path, kind, **overrides):
    options = {"timeout": 2.0, "retries": 0, "backoff": 0.0, "soft_hosts": ()}
    options.update(overrides)
    return crl.check_url(f"{BASE}{path}", kind, **options)


class ExtractUrlsTests(unittest.TestCase):
    def test_collects_html_and_markdown_images(self):
        text = (
            '<img src="https://a.example/one.svg" alt="x"/> '
            "![demo](https://a.example/two.png) "
            '<source srcset="https://a.example/three.svg" />'
        )
        images, links = crl.extract_urls(text)
        self.assertEqual(
            images,
            (
                "https://a.example/one.svg",
                "https://a.example/two.png",
                "https://a.example/three.svg",
            ),
        )
        self.assertEqual(links, ())

    def test_srcset_candidates_are_all_images_without_descriptors(self):
        images, links = crl.extract_urls(
            '<source srcset="https://a.example/x.png 2x, https://a.example/y.png 3x">'
        )
        self.assertEqual(images, ("https://a.example/x.png", "https://a.example/y.png"))
        self.assertEqual(links, ())

    def test_links_exclude_images_and_are_deduplicated(self):
        text = (
            '<a href="https://a.example/page">p</a> [again](https://a.example/page) '
            "https://b.example/bare "
            '<img src="https://a.example/i.svg"/>'
        )
        images, links = crl.extract_urls(text)
        self.assertEqual(images, ("https://a.example/i.svg",))
        self.assertEqual(links, ("https://a.example/page", "https://b.example/bare"))

    def test_nested_badge_yields_image_and_link(self):
        images, links = crl.extract_urls(
            "[![ci](https://a.example/badge.svg)](https://a.example/actions)"
        )
        self.assertEqual(images, ("https://a.example/badge.svg",))
        self.assertEqual(links, ("https://a.example/actions",))

    def test_html_comments_are_ignored(self):
        text = '<!-- <img src="https://hidden.example/x.png"/> --> <img src="https://shown.example/y.png"/>'
        images, links = crl.extract_urls(text)
        self.assertEqual(images, ("https://shown.example/y.png",))
        self.assertEqual(links, ())

    def test_trailing_punctuation_is_not_part_of_the_url(self):
        _, links = crl.extract_urls(
            "See https://a.example/docs. Also (https://b.example/x), and https://c.example/y;"
        )
        self.assertEqual(
            links,
            ("https://a.example/docs", "https://b.example/x", "https://c.example/y"),
        )

    def test_relative_images_are_kept_but_not_links(self):
        images, links = crl.extract_urls(
            "![gif](./assets/demo.gif) <img src='assets/b.png'/> ![d](data:image/png;base64,AAAA)"
        )
        self.assertEqual(images, ("./assets/demo.gif", "assets/b.png"))
        self.assertEqual(links, ())

    def test_mailto_and_anchors_are_not_links(self):
        _, links = crl.extract_urls(
            '<a href="mailto:a@b.c">m</a> <a href="#top">t</a> [x](#section)'
        )
        self.assertEqual(links, ())


class CheckImageTests(unittest.TestCase):
    def test_svg_and_png_pass(self):
        for path in ("/ok.svg", "/ok.png"):
            with self.subTest(path=path):
                self.assertEqual(fast_check(path, "image").level, "ok")

    def test_disabled_deployment_402_fails_with_status(self):
        finding = fast_check("/disabled.svg", "image")
        self.assertEqual(finding.level, "fail")
        self.assertIn("402", finding.detail)

    def test_missing_image_fails(self):
        self.assertEqual(fast_check("/missing", "image").level, "fail")

    def test_forbidden_image_fails_unlike_a_link(self):
        self.assertEqual(fast_check("/forbidden", "image").level, "fail")

    def test_html_served_as_image_fails_on_content_type(self):
        finding = fast_check("/page.html", "image")
        self.assertEqual(finding.level, "fail")
        self.assertIn("content-type", finding.detail)

    def test_error_badge_with_status_200_fails(self):
        finding = fast_check("/error-badge.svg", "image")
        self.assertEqual(finding.level, "fail")
        self.assertIn("error badge", finding.detail)

    def test_digits_inside_path_data_are_not_an_error_badge(self):
        self.assertEqual(fast_check("/coordinates.svg", "image").level, "ok")

    def test_rate_limited_badge_only_warns(self):
        finding = fast_check("/rate-limited-badge.svg", "image")
        self.assertEqual(finding.level, "warn")
        self.assertIn("rate limit", finding.detail)

    def test_rate_limited_badge_is_retried_and_can_recover(self):
        Handler.hits.pop("/recovering-badge.svg", None)
        finding = fast_check("/recovering-badge.svg", "image", retries=2)
        self.assertEqual(finding.level, "ok")
        self.assertEqual(Handler.hits["/recovering-badge.svg"], 2)

    def test_rate_limited_image_is_inconclusive_not_failed(self):
        self.assertEqual(fast_check("/limited", "image").level, "warn")

    def test_redirect_to_a_valid_image_passes(self):
        self.assertEqual(fast_check("/redirect-ok", "image").level, "ok")

    def test_redirect_to_a_non_http_scheme_is_refused(self):
        finding = fast_check("/redirect-ftp", "image")
        self.assertEqual(finding.level, "fail")

    def test_transient_503_is_retried_then_passes(self):
        Handler.hits.pop("/flaky.svg", None)
        finding = fast_check("/flaky.svg", "image", retries=2)
        self.assertEqual(finding.level, "ok")
        self.assertEqual(Handler.hits["/flaky.svg"], 2)

    def test_persistent_500_is_retried_then_fails(self):
        Handler.hits.pop("/broken", None)
        finding = fast_check("/broken", "image", retries=2)
        self.assertEqual(finding.level, "fail")
        self.assertEqual(Handler.hits["/broken"], 3)

    def test_4xx_is_not_retried(self):
        Handler.hits.pop("/missing", None)
        fast_check("/missing", "image", retries=2)
        self.assertEqual(Handler.hits["/missing"], 1)

    def test_timeout_fails(self):
        finding = fast_check("/slow", "image", timeout=0.2)
        self.assertEqual(finding.level, "fail")
        self.assertIn("timed out", finding.detail)

    def test_connection_refused_fails(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        finding = crl.check_url(
            f"http://127.0.0.1:{port}/x.svg",
            "image",
            timeout=1.0,
            retries=0,
            backoff=0.0,
            soft_hosts=(),
        )
        self.assertEqual(finding.level, "fail")


class CheckLinkTests(unittest.TestCase):
    def test_ok_page_passes(self):
        self.assertEqual(fast_check("/page.html", "link").level, "ok")

    def test_404_and_410_fail(self):
        for path in ("/missing", "/gone"):
            with self.subTest(path=path):
                self.assertEqual(fast_check(path, "link").level, "fail")

    def test_5xx_fails(self):
        self.assertEqual(fast_check("/broken", "link").level, "fail")

    def test_bot_walls_only_warn(self):
        for path in ("/forbidden", "/unauthorized", "/linkedin", "/limited"):
            with self.subTest(path=path):
                self.assertEqual(fast_check(path, "link").level, "warn")

    def test_timeout_fails_on_a_normal_host(self):
        self.assertEqual(fast_check("/slow", "link", timeout=0.2).level, "fail")

    def test_timeout_only_warns_on_a_soft_host(self):
        finding = fast_check("/slow", "link", timeout=0.2, soft_hosts=("127.0.0.1",))
        self.assertEqual(finding.level, "warn")

    def test_subdomain_of_a_soft_host_is_soft(self):
        self.assertTrue(crl.is_soft_host("www.medium.com", ("medium.com",)))
        self.assertFalse(crl.is_soft_host("notmedium.com", ("medium.com",)))


class LocalImageTests(unittest.TestCase):
    def test_existing_file_passes_and_missing_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "assets" / "demo.gif").write_bytes(b"GIF89a")
            self.assertEqual(
                crl.check_local_image("./assets/demo.gif", root).level, "ok"
            )
            self.assertEqual(
                crl.check_local_image("assets/nope.gif", root).level, "fail"
            )

    def test_path_escaping_the_repo_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                crl.check_local_image("../outside.gif", Path(tmp)).level, "fail"
            )


class CheckReadmeTests(unittest.TestCase):
    def _readme(self, tmp, body):
        path = Path(tmp) / "README.md"
        path.write_text(body, encoding="utf-8")
        return path

    def test_mixed_readme_reports_each_url_once(self):
        Handler.hits.pop("/ok.svg", None)
        with tempfile.TemporaryDirectory() as tmp:
            readme = self._readme(
                tmp,
                f'<img src="{BASE}/ok.svg"/> ![again]({BASE}/ok.svg) '
                f'<img src="{BASE}/disabled.svg"/> [site]({BASE}/page.html) [wall]({BASE}/forbidden)',
            )
            findings = crl.check_readme(
                readme, timeout=2.0, retries=0, backoff=0.0, workers=4, soft_hosts=()
            )
        by_level = {
            level: sorted(f.url for f in findings if f.level == level)
            for level in ("ok", "warn", "fail")
        }
        self.assertEqual(by_level["fail"], [f"{BASE}/disabled.svg"])
        self.assertEqual(by_level["warn"], [f"{BASE}/forbidden"])
        self.assertEqual(
            by_level["ok"], sorted([f"{BASE}/ok.svg", f"{BASE}/page.html"])
        )
        self.assertEqual(Handler.hits["/ok.svg"], 1)

    def test_relative_image_is_checked_against_the_readme_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = self._readme(tmp, "![gone](./assets/missing.gif)")
            findings = crl.check_readme(
                readme, timeout=1.0, retries=0, backoff=0.0, workers=2, soft_hosts=()
            )
        self.assertEqual([f.level for f in findings], ["fail"])

    def test_report_lists_failures_and_collapses_warnings(self):
        findings = (
            crl.Finding("https://a.example/x.svg", "image", "fail", "HTTP 402"),
            crl.Finding("https://b.example/y", "link", "warn", "HTTP 403 (bot wall)"),
            crl.Finding("https://c.example/z", "link", "ok", "HTTP 200"),
        )
        report = crl.render_report(findings)
        self.assertIn("https://a.example/x.svg", report)
        self.assertIn("HTTP 402", report)
        self.assertIn("<details>", report)
        self.assertIn("https://b.example/y", report)
        self.assertNotIn("https://c.example/z", report)

    def test_report_for_a_clean_run_says_so(self):
        report = crl.render_report(
            (crl.Finding("https://c.example/z", "link", "ok", "HTTP 200"),)
        )
        self.assertIn("0 failures", report)

    def test_main_exit_codes_and_report_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = self._readme(tmp, f'<img src="{BASE}/disabled.svg"/>')
            report_path = Path(tmp) / "report.md"
            code = quiet_main(
                [
                    str(bad),
                    "--report",
                    str(report_path),
                    "--timeout",
                    "2",
                    "--retries",
                    "0",
                    "--soft-host",
                    "",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn(
                f"{BASE}/disabled.svg", report_path.read_text(encoding="utf-8")
            )

            good = self._readme(
                tmp, f'<img src="{BASE}/ok.svg"/> [wall]({BASE}/forbidden)'
            )
            self.assertEqual(
                quiet_main(
                    [str(good), "--timeout", "2", "--retries", "0", "--soft-host", ""]
                ),
                0,
            )

    def test_main_rejects_a_missing_readme(self):
        self.assertEqual(quiet_main(["/nonexistent/README.md"]), 2)


if __name__ == "__main__":
    unittest.main()
