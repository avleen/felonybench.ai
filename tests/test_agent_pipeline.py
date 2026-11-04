import html
import json
import os
from pathlib import Path

import pytest
import yaml

from scripts.apply_agent_output import apply_output
from scripts.closed_prs import closing_reason, rejected, render, snapshot_name
from scripts.open_prs import labels_for, pr_body, pr_title
from scripts.rubric import load_incident_yaml
from scripts import run_report
from scripts.run_report import agent_result, describe, failed, failure_body, neutralize
from scripts.validate import NEWS_REQUIRED

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


def test_no_agent_text_in_a_pr_body_can_mention_people(make_incident):
    body = pr_body(make_incident(org="@org"), "@notes", None, "| @diff |", ["@error"])
    for handle in ("@org", "@notes", "@diff", "@error"):
        assert handle not in body


def test_two_rejections_of_one_incident_keep_separate_snapshots():
    first = {"headRefName": "agent/x", "number": 10}
    second = {"headRefName": "agent/x", "number": 20}
    assert snapshot_name(first) != snapshot_name(second)
    assert "/" not in snapshot_name({"headRefName": "agent/a/b", "number": 1})


def test_a_rejected_incident_needs_review_even_while_awaiting_news(make_incident):
    assert labels_for(make_incident(), [NEWS_REQUIRED], previously_closed=7) == ["agent", "awaiting-news", "needs-review"]
    assert labels_for(make_incident(), [], previously_closed=7) == ["agent", "needs-review"]
    assert labels_for(make_incident(), [NEWS_REQUIRED]) == ["agent", "awaiting-news"]


@pytest.mark.parametrize("agent, publish, expected", [
    ("success", "success", False),
    ("skipped", "success", False),
    ("failure", "success", True),
    ("success", "failure", True),
    ("success", "skipped", True),  # setup failed, so nothing was published: not a recovery
])
def test_only_a_real_publish_counts_as_success(agent, publish, expected):
    assert failed(agent, publish) is expected


def test_seen_leads_are_only_saved_after_publishing():
    jobs = yaml.safe_load((ROOT / ".github/workflows/watch.yml").read_text())["jobs"]
    uses = [s.get("uses", "") for s in jobs["publish"]["steps"]]
    assert not any("cache/save" in s.get("uses", "") for s in jobs["agent"]["steps"])
    assert uses.index("./.github/actions/publish-run") < next(i for i, u in enumerate(uses) if "cache/save" in u)
    assert not any("if" in s for s in jobs["publish"]["steps"] if "cache/save" in s.get("uses", ""))
    agent = jobs["agent"]["steps"]
    upload = next(i for i, s in enumerate(agent) if "upload-artifact" in s.get("uses", ""))
    assert upload < next(i for i, s in enumerate(agent) if "run-agent" in s.get("uses", ""))


def test_a_failed_download_is_not_treated_as_no_output():
    steps = yaml.safe_load((ROOT / ".github/actions/publish-run/action.yml").read_text())["runs"]["steps"]
    open_prs = next(s for s in steps if s.get("id") == "open_prs")
    assert "$EXPECT_OUTPUT" in open_prs["run"] and "OUTPUT_DOWNLOAD" in open_prs["env"]
    assert next(s for s in steps if s.get("name") == "Report the run")["if"] == "always()"


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


def _record_issues(monkeypatch, open_issue=None):
    calls = []
    monkeypatch.setattr(run_report, "_find_issue", lambda title: open_issue)
    monkeypatch.setattr(run_report, "_gh", lambda *args: calls.append(args) or "")
    return calls


def test_dead_feeds_open_their_own_issue(monkeypatch):
    calls = _record_issues(monkeypatch)
    run_report.report_feeds("URL", "A, B")
    assert calls[0][:2] == ("issue", "create") and run_report.FEEDS_ISSUE in calls[0]
    assert "A, B" in calls[0][-1]


def test_healthy_feeds_close_the_issue(monkeypatch):
    calls = _record_issues(monkeypatch, open_issue=7)
    run_report.report_feeds("URL", "none")
    assert calls[0][:3] == ("issue", "close", "7")


def test_a_workflow_that_did_not_check_feeds_leaves_the_issue_alone(monkeypatch):
    calls = _record_issues(monkeypatch, open_issue=7)
    run_report.report_feeds("URL", "")
    assert calls == []


def test_a_feed_outage_does_not_fail_the_watch_job():
    jobs = yaml.safe_load((ROOT / ".github/workflows/watch.yml").read_text())["jobs"]
    assert not any("dead_feeds" in str(s.get("if", "")) for s in jobs["agent"]["steps"])
    publish = next(s for s in jobs["publish"]["steps"] if "publish-run" in s.get("uses", ""))
    assert "dead_feeds" in publish["with"]


@pytest.mark.parametrize("text", [
    "[source](https://medium.com/@researcher/report)",
    "see https://medium.com/@researcher/report.",
    "<https://medium.com/@researcher/report>",
])
def test_neutralize_keeps_links_working_by_encoding_the_at(text):
    assert "https://medium.com/%40researcher" in neutralize(text)


@pytest.mark.parametrize("text", [
    "@owner",
    "hi @owner.",
    "[a](https://x.com)@owner",
    "https://x.com/a|@owner",
    "https://@owner",
    "https://x.com@owner",
    "xhttps://x.com/@owner",
    "https://x.com/ @owner",
    "https://x.com/a\\@owner",
    "*https://x.com/*@owner",
    "~~https://x.com/~~@owner",
    "https://x.com/&#32;@owner",
    "<div>\nhttps://x.com/@owner\n</div>",
    "HTTPS://X.COM/@owner",
    "&#64;owner",
    "&#064;owner",
    "&#0064;owner",
    "&#x40;owner",
    "&#X40;owner",
    "&#x0040;owner",
    "&commat;owner",
    "<div>&#64owner</div>",
    "> &#64;owner",
    "https://x.com/&#64;owner",
])
def test_neutralize_leaves_no_bare_mention(text):
    assert "@owner" not in html.unescape(neutralize(text))


@pytest.mark.parametrize("text", ["&#640;", "&#x401;", "&amp;#64;", "AT&T"])
def test_neutralize_leaves_other_entities_alone(text):
    assert neutralize(text) == text


def test_a_pr_title_cant_mention_anyone():
    assert "@owner" not in pr_title({"org": "@owner", "victims": [{"name": "@other"}]}, is_new=True)
    assert "@other" not in pr_title({"org": "@owner", "victims": [{"name": "@other"}]}, is_new=True)
    assert "@owner" not in pr_title({"id": "@owner"}, is_new=False)


def test_incident_loading_refuses_aliases_but_reads_plain_yaml():
    assert load_incident_yaml("a: 1\n") == {"a": 1}
    with pytest.raises(yaml.YAMLError):
        load_incident_yaml("a: &a 1\nb: *a\n")
    with pytest.raises(yaml.YAMLError, match="line 2"):
        load_incident_yaml("a: &a 1\nb: *a\n")


def _real_gh_stub(tmp_path, monkeypatch):
    """A real subprocess, so an argument the OS would refuse fails here too."""
    log = tmp_path / "gh.log"
    gh = tmp_path / "bin" / "gh"
    gh.parent.mkdir()
    gh.write_text(f'#!/bin/sh\necho "$1 $2" >> "{log}"\necho "[]"\n')
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{gh.parent}:{os.environ['PATH']}")
    return log


@pytest.mark.parametrize("content", [b"caf\xff\n", b"caf\x00e\n", b"caf" + b"\xff" * 64000, "café".encode() * 40000])
def test_a_bad_sweep_report_is_still_posted_and_summarized(tmp_path, monkeypatch, content):
    log = _real_gh_stub(tmp_path, monkeypatch)
    report = tmp_path / "sweep.md"
    report.write_bytes(content)
    summary = tmp_path / "summary"
    for key, value in {"GITHUB_SERVER_URL": "s", "GITHUB_REPOSITORY": "r", "GITHUB_RUN_ID": "1", "GITHUB_WORKFLOW": "w", "GITHUB_STEP_SUMMARY": str(summary)}.items():
        monkeypatch.setenv(key, value)

    assert run_report.main(["--agent", "success", "--publish", "success", "--sweep-report", str(report)]) == 0

    assert "issue create" in log.read_text()
    assert "caf" in summary.read_text()


@pytest.mark.parametrize("text", ["\xff" * 64000, "\ufffd" * 64000, "😀" * 59000, "a" * 200000])
def test_postable_fits_in_one_argument_and_says_it_was_cut(text):
    out = run_report.postable(text)
    assert len(out.encode()) <= run_report.MAX_ARG_BYTES and len(out) <= run_report.COMMENT_LIMIT
    if len(text) > run_report.COMMENT_LIMIT or len(text.encode()) > run_report.MAX_ARG_BYTES:
        assert out.endswith("_…truncated._")


def test_postable_cuts_on_a_character_boundary_and_leaves_short_text_alone():
    assert "\ufffd" not in run_report.postable("😀" * 59000)
    assert run_report.postable("short") == "short"
    assert run_report.postable("a\0b @x") == "ab @\u200bx"
