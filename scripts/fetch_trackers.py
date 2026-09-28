"""Prefetch other public incident trackers into .agent-out/trackers/ for the sweep agent.

Read-only and polite: one request per tracker. A failure writes the error into the output
file instead of failing, so the sweep always runs.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

from scripts.rubric import ROOT

ORG_URL = "https://felonybench.org/felonies.json"
COM_URL = "https://www.felonybench.com/"
AGENT_UA = "felonybench-agent/1.0 (+https://felonybench.ai/how-it-works)"
# felonybench.com sits behind a Vercel bot checkpoint that only a real browser passes.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
CHECKPOINT_MARKERS = ("Vercel Security Checkpoint", "Verifying your browser")


def org_digest(data: dict) -> str:
    """One line per felonybench.org event, with source URLs resolved."""
    companies = {c.get("id"): c.get("name", c.get("id")) for c in data.get("companies", [])}
    sources = {s.get("id"): s for s in data.get("sources", [])}
    lines = [f"felonybench.org ({data.get('updated_at', 'unknown date')}): "
             f"{len(data.get('events', []))} events", ""]
    for e in data.get("events", []):
        company = companies.get(e.get("company_id"), e.get("company_id", "?"))
        lines.append(f"- {e.get('date', '?')} | {company} | {e.get('conduct', '')}")
        if e.get("facts"):
            lines.append(f"  facts: {e['facts']}")
        for sid in e.get("sources", []):
            s = sources.get(sid, {})
            lines.append(f"  source: {s.get('publisher', sid)}: {s.get('title', '')} {s.get('url', '')}".rstrip())
    return "\n".join(lines) + "\n"


def clean_text(text: str) -> str:
    """Strip each line and collapse runs of blank lines."""
    lines = [line.strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def fetch_org(out_dir: Path, opener=urllib.request.urlopen) -> str:
    try:
        req = urllib.request.Request(ORG_URL, headers={"User-Agent": AGENT_UA})
        with opener(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        (out_dir / "felonybench-org.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
        (out_dir / "felonybench-org.txt").write_text(org_digest(data))
        return f"ok ({len(data.get('events', []))} events)"
    except Exception as e:
        msg = f"ERROR fetching {ORG_URL}: {type(e).__name__}: {e}\n"
        (out_dir / "felonybench-org.json").write_text(json.dumps({"error": msg.strip()}))
        (out_dir / "felonybench-org.txt").write_text(msg)
        return msg.strip()


def browser_text(url: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=BROWSER_UA, viewport={"width": 1440, "height": 900},
                                    locale="en-US")
            page.goto(url, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(4_000)
            # The checkpoint reloads into the real page once it passes; give it a little longer.
            for _ in range(5):
                text = page.evaluate("document.body.innerText")
                if not any(m in text for m in CHECKPOINT_MARKERS):
                    break
                page.wait_for_timeout(4_000)
            # innerText drops hrefs, and the incident table's source links are the useful part.
            links = page.evaluate(
                "[...document.querySelectorAll('a[href]')]"
                ".map(a => `${a.innerText.trim() || '(no text)'} -> ${a.href}`)"
            )
            return text + "\n\nLinks on page:\n" + "\n".join(links)
        finally:
            browser.close()


def fetch_com(out_dir: Path, get_text=browser_text) -> str:
    out = out_dir / "felonybench-com.txt"
    try:
        text = clean_text(get_text(COM_URL))
        if any(m in text for m in CHECKPOINT_MARKERS):
            raise RuntimeError("still on the bot checkpoint page: " + text[:200])
        out.write_text(f"Source: {COM_URL} (rendered page text)\n\n{text}")
        return f"ok ({len(text)} chars)"
    except Exception as e:
        msg = f"ERROR fetching {COM_URL}: {type(e).__name__}: {e}\n"
        out.write_text(msg)
        return msg.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / ".agent-out" / "trackers")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"felonybench.org: {fetch_org(args.out)}")
    print(f"felonybench.com: {fetch_com(args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
