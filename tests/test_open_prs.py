import sys
import subprocess

import pytest

from scripts.open_prs import _run, disallowed, labels_for, main, parse_porcelain, pr_body, pr_title


def test_parse_porcelain():
    out = "?? incidents/new.yaml\0 M incidents/old.yaml\0 D incidents/gone.yaml\0R  incidents/b.yaml\0a.yaml\0"
    assert parse_porcelain(out) == [
        ("??", "incidents/new.yaml"),
        ("M", "incidents/old.yaml"),
        ("D", "incidents/gone.yaml"),
        ("R", "incidents/b.yaml"),
        ("D", "a.yaml"),
    ]


def test_parse_porcelain_is_not_fooled_by_arrows_in_a_filename():
    assert parse_porcelain("?? scripts/a -> incidents/x.yaml\0") == [("??", "scripts/a -> incidents/x.yaml")]


def test_parse_porcelain_keeps_non_ascii_names():
    assert parse_porcelain("?? incidents/é.yaml\0") == [("??", "incidents/é.yaml")]


def test_disallowed_paths():
    assert disallowed(["incidents/x.yaml", ".github/workflows/watch.yml", "README.md"]) == [
        ".github/workflows/watch.yml", "README.md"]


def test_titles(make_incident):
    incident = make_incident()
    assert pr_title(incident, is_new=True) == "New felony: OpenAI — Hugging Face"
    assert pr_title(incident, is_new=False) == f"Update: {incident['id']}"


def test_labels(make_incident):
    assert labels_for(make_incident(), []) == ["agent"]
    assert labels_for(make_incident(confidence="low"), []) == ["agent", "needs-review"]
    assert labels_for(make_incident(), ["boom"]) == ["agent", "needs-review"]


def test_body_includes_validation_failure(make_incident):
    body = pr_body(make_incident(), "Notes here.", None, "## Leaderboard impact\n", ["bad thing"])
    assert "Notes here." in body
    assert "❌" in body and "- bad thing" in body


def test_body_includes_score(make_incident, rubric):
    from scripts.scoring import breakdown
    body = pr_body(make_incident(), "", breakdown(make_incident(), rubric), "", [])
    assert "| **Total** | **87** |" in body
    assert "✅" in body


def test_body_is_capped_at_65000_chars(make_incident):
    body = pr_body(make_incident(), "x" * 200_000, None, "", [])
    assert len(body) <= 65000
    assert body.endswith("_…truncated._")


def test_run_prints_command_and_stderr_on_failure(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.open_prs.ROOT", tmp_path)

    def fake_run(cmd, check, text, capture_output, cwd):
        raise subprocess.CalledProcessError(
            1, cmd, output="stdout stuff", stderr="boom: something went wrong"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        _run("git", "status")
    err = capsys.readouterr().err
    assert "git status" in err
    assert "boom: something went wrong" in err


def test_body_for_accomplice_incident(make_accomplice, rubric):
    from scripts.scoring import breakdown
    body = pr_body(make_accomplice(), "", breakdown(make_accomplice(), rubric), "", [])
    assert "| × Contribution | 1.5 |" in body
    assert "| + Guardrails | 10 |" in body
    assert "Autonomy" not in body and "Pettiness" not in body
    assert "| **Total** | **42** |" in body


def test_missing_news_only_opens_a_draft(make_incident):
    from scripts.open_prs import awaiting_news
    from scripts.validate import NEWS_REQUIRED
    assert awaiting_news([NEWS_REQUIRED]) is True
    assert awaiting_news([NEWS_REQUIRED, "reported: earlier than date"]) is False
    assert awaiting_news([]) is False
    assert labels_for(make_incident(), [NEWS_REQUIRED]) == ["agent", "awaiting-news"]


def test_draft_becomes_ready_once_news_arrives():
    from scripts.open_prs import becomes_ready
    from scripts.validate import NEWS_REQUIRED
    assert becomes_ready({"isDraft": True}, []) is True
    assert becomes_ready({"isDraft": True}, [NEWS_REQUIRED]) is False
    assert becomes_ready({"isDraft": True}, ["something else"]) is False
    assert becomes_ready({"isDraft": False}, []) is False


def test_run_cleans_arguments_the_os_would_refuse():
    assert _run(sys.executable, "-c", "import sys; print(sys.argv[1])", "a\0b\ud800c").strip() == "ab?c"
