from scripts.open_prs import disallowed, labels_for, parse_porcelain, pr_body, pr_title


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
