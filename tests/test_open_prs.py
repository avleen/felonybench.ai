import subprocess

import pytest

from scripts.open_prs import _run, disallowed, labels_for, main, parse_porcelain, pr_body, pr_title


def test_parse_porcelain():
    out = "?? incidents/new.yaml\n M incidents/old.yaml\n D incidents/gone.yaml\nR  a.yaml -> incidents/b.yaml\n"
    assert parse_porcelain(out) == [
        ("??", "incidents/new.yaml"),
        ("M", "incidents/old.yaml"),
        ("D", "incidents/gone.yaml"),
        ("R", "incidents/b.yaml"),
    ]


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
