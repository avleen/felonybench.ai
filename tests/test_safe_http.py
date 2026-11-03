import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from scripts import fetch_trackers, pdf_text
from scripts.safe_http import NoDrainRedirects

BODY_MB = 200


# urllib only follows a 308 from Python 3.11, which is what CI and the workflows use.
needs_308 = pytest.mark.skipif(sys.version_info < (3, 11), reason="urllib doesn't follow 308 before 3.11")


@pytest.mark.parametrize("code", [301, 302, 303, 307, pytest.param(308, marks=needs_308)])
def test_a_huge_redirect_body_is_not_read(code):
    sent = {"bytes": 0}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/final":
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"ok")
                return
            self.send_response(code)
            self.send_header("Location", "/final")
            self.send_header("Content-Length", str(BODY_MB * 1024 * 1024))
            self.end_headers()
            chunk = b"x" * (1024 * 1024)
            try:
                for _ in range(BODY_MB):
                    self.wfile.write(chunk)
                    sent["bytes"] += len(chunk)
            except OSError:
                self.close_connection = True

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        opener = urllib.request.build_opener(NoDrainRedirects())
        with opener.open(f"http://127.0.0.1:{server.server_port}/start", timeout=30) as resp:
            assert resp.read() == b"ok"
    finally:
        server.shutdown()
        server.server_close()
    assert sent["bytes"] < 50 * 1024 * 1024


def _spy_on_openers(monkeypatch):
    built = []

    def build_opener(*handlers):
        built.extend(handlers)
        raise ConnectionError("stop before any network")

    monkeypatch.setattr(urllib.request, "build_opener", build_opener)
    return built


def test_fetch_org_uses_the_no_drain_handler_by_default(monkeypatch, tmp_path):
    built = _spy_on_openers(monkeypatch)
    with pytest.raises(ConnectionError):
        fetch_trackers.fetch_org(tmp_path)
    assert any(isinstance(h, NoDrainRedirects) for h in built)


def test_pdf_load_uses_the_no_drain_handler_by_default(monkeypatch):
    built = _spy_on_openers(monkeypatch)
    with pytest.raises(ConnectionError):
        pdf_text.load("https://example.com/r.pdf", resolve=lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))])
    assert any(isinstance(h, NoDrainRedirects) for h in built)
