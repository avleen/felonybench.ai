import io
import socket
import urllib.request

import pytest

from scripts import pdf_text
from scripts.pdf_text import extract_text, load, parse_pages


def make_pdf(pages: list[str]) -> bytes:
    """A minimal PDF with one line of Helvetica text per page, built by hand."""
    n = len(pages)
    font_id, pages_id = 3 + 2 * n, 2
    objects = {1: b"<< /Type /Catalog /Pages 2 0 R >>"}
    kids = []
    for i, text in enumerate(pages):
        page_id, content_id = 3 + 2 * i, 4 + 2 * i
        kids.append(f"{page_id} 0 R")
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        objects[page_id] = (f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                            f"/Contents {content_id} 0 R >>").encode()
        objects[content_id] = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
    objects[pages_id] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {n} >>".encode()
    objects[font_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    out = io.BytesIO(b"%PDF-1.4\n")
    offsets = {}
    for num in sorted(objects):
        offsets[num] = out.tell()
        out.write(b"%d 0 obj\n" % num + objects[num] + b"\nendobj\n")
    xref = out.tell()
    size = max(objects) + 1
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % size)
    for num in range(1, size):
        out.write(b"%010d 00000 n \n" % offsets[num])
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (size, xref))
    return out.getvalue()


PDF = make_pdf(["First page", "Second page", "Third page"])


def test_extracts_every_page_with_headers():
    text = extract_text(PDF)
    assert "--- page 1 of 3 ---" in text
    assert "First page" in text and "Third page" in text
    assert text.index("First page") < text.index("Second page") < text.index("Third page")


def test_page_range_limits_output():
    text = extract_text(PDF, pages=(2, 3))
    assert "First page" not in text
    assert "--- page 2 of 3 ---" in text and "Third page" in text


def test_page_range_is_clamped_to_the_document():
    text = extract_text(PDF, pages=(3, 10))
    assert "Third page" in text and "Second page" not in text


def test_max_chars_truncates_with_a_note():
    text = extract_text(PDF, max_chars=20)
    assert text.startswith("--- page 1 of 3 ---")
    assert "[truncated at 20 characters" in text
    assert "Third page" not in text


@pytest.mark.parametrize("spec, expected", [("3-10", (3, 10)), ("5", (5, 5)), (" 2 - 4 ", (2, 4))])
def test_parse_pages(spec, expected):
    assert parse_pages(spec) == expected


@pytest.mark.parametrize("spec", ["0-2", "5-3", "a-b", "-3", ""])
def test_parse_pages_rejects_bad_ranges(spec):
    with pytest.raises(ValueError):
        parse_pages(spec)


def test_load_reads_a_local_file(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(PDF)
    assert load(str(path)) == PDF


def resolver(ip):
    """A getaddrinfo stand-in that resolves every host to `ip`, so tests never touch DNS."""
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    return lambda host, port, *a, **k: [(family, socket.SOCK_STREAM, 6, "", (ip, port or 443))]


PUBLIC = resolver("93.184.216.34")


def test_load_fetches_urls_with_a_browser_user_agent():
    seen = {}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def opener(req, timeout):
        seen["ua"] = req.get_header("User-agent")
        return Resp(PDF)

    assert load("https://example.com/report.pdf", opener=opener, resolve=PUBLIC) == PDF
    assert seen["ua"] == pdf_text.BROWSER_UA


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.1.2.3", "192.168.0.5", "169.254.169.254", "::1", "fd00::1"])
def test_load_refuses_hosts_that_resolve_to_non_public_addresses(ip):
    def opener(req, timeout):
        raise AssertionError("must not connect")

    with pytest.raises(ValueError, match="non-public"):
        load("https://internal.example/report.pdf", opener=opener, resolve=resolver(ip))


@pytest.mark.parametrize("url", ["ftp://example.com/r.pdf", "file:///etc/hosts", "gopher://example.com/"])
def test_check_url_refuses_other_schemes(url):
    with pytest.raises(ValueError, match="http"):
        pdf_text.check_url(url, resolve=PUBLIC)


def test_redirects_are_checked_too():
    handler = pdf_text.PublicOnlyRedirects(resolve=resolver("169.254.169.254"))
    req = urllib.request.Request("https://example.com/r.pdf")
    with pytest.raises(ValueError, match="non-public"):
        handler.redirect_request(req, None, 302, "Found", {}, "http://metadata.internal/")


def test_public_redirects_are_followed():
    handler = pdf_text.PublicOnlyRedirects(resolve=PUBLIC)
    req = urllib.request.Request("https://example.com/r.pdf")
    new = handler.redirect_request(req, None, 302, "Found", {}, "https://cdn.example.com/r.pdf")
    assert new.full_url == "https://cdn.example.com/r.pdf"


@pytest.mark.parametrize("value", ["-1", "0"])
def test_main_rejects_non_positive_max_chars(value, tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(PDF)
    with pytest.raises(SystemExit) as exc:
        pdf_text.main([str(path), "--max-chars", value])
    assert exc.value.code == 2


def test_main_prints_text(tmp_path, capsys):
    path = tmp_path / "report.pdf"
    path.write_bytes(PDF)
    assert pdf_text.main([str(path), "--pages", "2"]) == 0
    out = capsys.readouterr().out
    assert "Second page" in out and "First page" not in out


def test_main_reports_errors_without_a_traceback(capsys):
    assert pdf_text.main(["/no/such/file.pdf"]) == 1
    assert "ERROR" in capsys.readouterr().err
