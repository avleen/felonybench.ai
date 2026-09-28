import io
import json

from scripts import fetch_trackers
from scripts.fetch_trackers import clean_text, fetch_com, fetch_org, org_digest

ORG_DATA = {
    "updated_at": "2026-09-01",
    "companies": [{"id": "openai", "name": "OpenAI"}],
    "sources": [{"id": "s1", "publisher": "Reuters", "title": "Agent hacked a company",
                 "url": "https://example.com/r"}],
    "events": [{"id": "e1", "company_id": "openai", "date": "2026-07-09",
                "conduct": "Sandbox escape", "facts": "Escaped.", "sources": ["s1", "missing"]}],
}


def test_org_digest_resolves_companies_and_sources():
    text = org_digest(ORG_DATA)
    assert "1 events" in text
    assert "- 2026-07-09 | OpenAI | Sandbox escape" in text
    assert "source: Reuters: Agent hacked a company https://example.com/r" in text
    assert "source: missing" in text


def test_clean_text_collapses_blank_lines():
    assert clean_text("  a  \n\n\n\n b\n") == "a\n\nb\n"


def test_fetch_org_writes_json_and_digest(tmp_path):
    def opener(req, timeout):
        return io.BytesIO(json.dumps(ORG_DATA).encode())

    assert fetch_org(tmp_path, opener=opener).startswith("ok")
    assert json.loads((tmp_path / "felonybench-org.json").read_text()) == ORG_DATA
    assert "OpenAI" in (tmp_path / "felonybench-org.txt").read_text()


def test_fetch_org_records_errors(tmp_path):
    def opener(req, timeout):
        raise OSError("network down")

    assert "network down" in fetch_org(tmp_path, opener=opener)
    assert "network down" in json.loads((tmp_path / "felonybench-org.json").read_text())["error"]


def test_fetch_com_records_checkpoint_as_error(tmp_path):
    fetch_com(tmp_path, get_text=lambda url: "Vercel Security Checkpoint\nVerifying your browser")
    assert (tmp_path / "felonybench-com.txt").read_text().startswith("ERROR")


def test_fetch_com_writes_text(tmp_path):
    fetch_com(tmp_path, get_text=lambda url: "Incidents\n\n\n\nOpenAI  sandbox escape")
    text = (tmp_path / "felonybench-com.txt").read_text()
    assert "Incidents\n\nOpenAI  sandbox escape" in text


def test_main_never_fails(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("no browser")

    monkeypatch.setattr(fetch_trackers, "fetch_org",
                        lambda out: fetch_org(out, opener=boom))
    monkeypatch.setattr(fetch_trackers, "fetch_com",
                        lambda out: fetch_com(out, get_text=boom))
    assert fetch_trackers.main(["--out", str(tmp_path / "t")]) == 0
    assert (tmp_path / "t" / "felonybench-com.txt").read_text().startswith("ERROR")
