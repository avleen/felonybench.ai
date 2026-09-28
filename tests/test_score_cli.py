import json

import yaml

from scripts.score import main


def test_cli_writes_scores(tmp_path, make_incident):
    incidents = tmp_path / "incidents"
    incidents.mkdir()
    incident = make_incident()
    (incidents / f"{incident['id']}.yaml").write_text(yaml.safe_dump(incident))
    out = tmp_path / "out" / "scores.json"

    assert main(["--incidents", str(incidents), "--out", str(out)]) == 0

    scores = json.loads(out.read_text())
    assert scores["boards"]["open"]["verified"]["orgs"][0]["score"] == 87


def test_cli_handles_missing_incident_dir(tmp_path):
    out = tmp_path / "scores.json"
    assert main(["--incidents", str(tmp_path / "nope"), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["incidents"] == []
