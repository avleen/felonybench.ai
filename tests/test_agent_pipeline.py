import json
from pathlib import Path

import pytest
import yaml

from scripts.apply_agent_output import apply_output
from scripts.closed_prs import closing_reason, rejected, render
from scripts.open_prs import pr_body, quote_notes
from scripts.run_report import agent_result, describe, failure_body, neutralize

ROOT = Path(__file__).resolve().parent.parent


def test_apply_copies_only_incidents_and_notes(tmp_path):
    source, target = tmp_path / "s", tmp_path / "t"
    (source / "incidents" / "sub").mkdir(parents=True)
    (source / ".agent-out" / "closed").mkdir(parents=True)
    (source / "scripts").mkdir()
    (source / "scripts" / "open_prs.py").write_text("evil")
    (source / "yaml.py").write_text("evil")
    (source / "incidents" / "ok.yaml").write_text("a")
    (source / "incidents" / "x.yml").write_text("no")
    (source / "incidents" / "LICENSE.md").write_text("no")
    (source / "incidents" / "sub" / "n.yaml").write_text("no")
    (source / ".agent-out" / "ok.md").write_text("n")
    (source / ".agent-out" / "closed" / "c.md").write_text("no")

    assert apply_output(source, target) == ["incidents/ok.yaml", ".agent-out/ok.md"]
    assert sorted(p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()) == [
        ".agent-out/ok.md", "incidents/ok.yaml"]


def test_apply_ignores_symlinks(tmp_path):
    source, target = tmp_path / "s", tmp_path / "t"
    (source / "incidents").mkdir(parents=True)
    secret = tmp_path / "secret"
    secret.write_text("token")
    (source / "incidents" / "link.yaml").symlink_to(secret)

    assert apply_output(source, target) == []


def test_apply_with_no_output_is_fine(tmp_path):
    assert apply_output(tmp_path / "missing", tmp_path / "t") == []


def test_rejected_keeps_only_unmerged_agent_prs():
    prs = [
        {"headRefName": "agent/a", "mergedAt": None},
        {"headRefName": "agent/b", "mergedAt": "2026-01-01"},
        {"headRefName": "person/c", "mergedAt": None},
    ]
    assert [p["headRefName"] for p in rejected(prs)] == ["agent/a"]


def test_closing_reason_is_the_last_comment_from_a_person():
    pr = {"comments": [
        {"author": {"login": "owner"}, "body": "Not a crime."},
        {"author": {"login": "github-actions"}, "body": "Agent updated"},
    ]}
    assert closing_reason(pr) == "Not a crime."
    assert closing_reason({"comments": []}) == ""
    assert "No reason recorded" in render({"title": "T", "number": 1})


def test_agent_result_reads_the_final_record(tmp_path):
    path = tmp_path / "t.json"
    path.write_text(json.dumps([{"type": "system"}, {"type": "result", "subtype": "success", "num_turns": 159}]))
    assert "`success` after 159 turns" in describe(agent_result(path))


@pytest.mark.parametrize("text", ["not json", "{}", "[]"])
def test_agent_result_survives_a_bad_transcript(tmp_path, text):
    path = tmp_path / "t.json"
    path.write_text(text)
    assert agent_result(path) is None


def test_agent_result_with_no_transcript():
    assert agent_result(None) is None
    assert "no result" in describe(None)


def test_describe_ignores_unexpected_types():
    assert "`unknown` after unknown turns" in describe({"subtype": 1, "num_turns": "9"})


def test_failure_body_names_both_outcomes():
    body = failure_body("http://run", "failure", "success", {"subtype": "success", "num_turns": 159})
    assert "http://run" in body and "`failure`" in body and "159" in body


def test_untrusted_text_cannot_mention_people():
    assert "@owner" not in neutralize("hi @owner")
    assert "@owner" not in quote_notes("hi @owner")


def test_notes_come_after_generated_sections(make_incident):
    body = pr_body(make_incident(), "## Validation\n\n✅ Passed\n", None, "## Leaderboard impact", ["bad"])
    assert body.index("❌ Failed") < body.index("Agent notes")
    assert "> ## Validation" in body
    assert body.count("\n## Validation") == 0 and body.startswith("## Validation")


def test_truncation_cannot_cut_the_generated_sections(make_incident):
    body = pr_body(make_incident(), "x" * 70000, None, "", ["bad"])
    assert len(body) <= 65000 and "❌ Failed" in body


def test_low_confidence_says_it_is_hidden(make_incident):
    assert "Hidden by default" in pr_body(make_incident(confidence="low"), "", None, "", [])
    assert "Hidden by default" not in pr_body(make_incident(confidence="high"), "", None, "", [])


@pytest.mark.parametrize("name", ["watch", "sweep"])
def test_the_agent_job_cannot_write(name):
    workflow = yaml.safe_load((ROOT / f".github/workflows/{name}.yml").read_text())
    assert set(workflow["permissions"].values()) == {"read"}
    agent = workflow["jobs"]["agent"]
    assert "permissions" not in agent
    assert agent["steps"][0]["with"]["persist-credentials"] is False
    assert workflow["jobs"]["publish"]["permissions"]["contents"] == "write"
    assert workflow["jobs"]["publish"]["if"] == "always()"
    secret_users = [s for s in workflow["jobs"]["publish"]["steps"] if "secrets." in str(s)]
    assert secret_users == []


def test_the_agent_cannot_edit_outside_its_output():
    args = yaml.safe_load((ROOT / ".github/actions/run-agent/action.yml").read_text())
    claude = next(s for s in args["runs"]["steps"] if s.get("name") == "Claude Code")["with"]["claude_args"]
    assert "--permission-mode dontAsk" in claude
    assert "acceptEdits" not in claude
    assert "Read(./.git/**)" in claude
