"""Print the text of a PDF, for the agent in GitHub Actions (which has no other way to read one).

    python -m scripts.pdf_text <url-or-path> [--pages 3-10] [--max-chars N]

Government and lab reports are usually PDFs, and WebFetch times out on large ones. Pages are
numbered from 1 and each starts with a "--- page N of M ---" header, so citations can name
the page.
"""
import argparse
import io
import ipaddress
import socket
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from pypdf import PdfReader

# Some report hosts refuse non-browser clients.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
DEFAULT_MAX_CHARS = 200_000


def parse_pages(spec: str) -> tuple[int, int]:
    """'3-10' -> (3, 10); '5' -> (5, 5). Pages are 1-based and the range must be ascending."""
    first, _, last = spec.partition("-")
    try:
        start = int(first)
        end = int(last) if last.strip() else start
    except ValueError:
        raise ValueError(f"bad page range {spec!r}; use e.g. 3-10 or 5") from None
    if start < 1 or end < start:
        raise ValueError(f"bad page range {spec!r}; use e.g. 3-10 or 5")
    return start, end


def positive_int(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value}")
    return n


# The agent picks URLs from web pages, and this runs on a CI runner, so it only fetches
# public addresses (no loopback, private networks or cloud metadata), including after
# every redirect.
def check_url(url: str, resolve=socket.getaddrinfo) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"only http(s) URLs can be fetched: {url}")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    for *_, sockaddr in resolve(parts.hostname, port, proto=socket.IPPROTO_TCP):
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global or ip.is_multicast:
            raise ValueError(f"refusing to fetch {url}: {parts.hostname} resolves to non-public address {ip}")


class PublicOnlyRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, resolve=socket.getaddrinfo):
        self.resolve = resolve

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl, self.resolve)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def load(source: str, opener=None, resolve=socket.getaddrinfo) -> bytes:
    """Read a local file, or fetch a public http(s) URL."""
    if not source.startswith(("http://", "https://")):
        return Path(source).read_bytes()
    check_url(source, resolve)
    opener = opener or urllib.request.build_opener(PublicOnlyRedirects(resolve)).open
    req = urllib.request.Request(source, headers={"User-Agent": BROWSER_UA})
    with opener(req, timeout=120) as resp:
        return resp.read()


def extract_text(data: bytes, pages: tuple[int, int] | None = None, max_chars: int | None = None) -> str:
    reader = PdfReader(io.BytesIO(data))
    total = len(reader.pages)
    start, end = pages or (1, total)
    parts = []
    for n in range(start, min(end, total) + 1):
        parts.append(f"--- page {n} of {total} ---\n{(reader.pages[n - 1].extract_text() or '').strip()}\n")
    text = "\n".join(parts)
    if max_chars is not None and len(text) > max_chars:
        text = (text[:max_chars].rstrip()
                + f"\n\n[truncated at {max_chars} characters; use --pages to read further]\n")
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", help="PDF URL or local path")
    ap.add_argument("--pages", type=parse_pages, help="page range, e.g. 3-10 or 5 (1-based)")
    ap.add_argument("--max-chars", type=positive_int, default=DEFAULT_MAX_CHARS,
                    help=f"truncate output after this many characters (default {DEFAULT_MAX_CHARS})")
    args = ap.parse_args(argv)
    try:
        text = extract_text(load(args.source), args.pages, args.max_chars)
    except Exception as e:
        print(f"ERROR reading {args.source}: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
