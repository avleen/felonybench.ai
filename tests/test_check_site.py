import pytest

from scripts.check_site import broken_values, main, redirect_errors


def _site(tmp_path, redirects=""):
    (tmp_path / "index.html").write_text("<p>ok</p>")
    (tmp_path / "model" / "new").mkdir(parents=True)
    (tmp_path / "model" / "new" / "index.html").write_text("<p>ok</p>")
    (tmp_path / "og").mkdir()
    (tmp_path / "og" / "new.png").write_bytes(b"png")
    (tmp_path / "_redirects").write_text(redirects)
    return tmp_path


COMPLETE = "/model/old /model/new/ 301\n/model/old/ /model/new/ 301\n/og/old.png /og/new.png 301\n"


def test_complete_redirects_pass(tmp_path):
    assert redirect_errors(_site(tmp_path, f"# old links\n\n{COMPLETE}")) == []


def test_redirect_to_a_missing_page_fails(tmp_path):
    errors = redirect_errors(_site(tmp_path, "/model/old /model/gone/ 301\n/model/old/ /model/gone/ 301\n"))
    assert len(errors) == 2 and all("doesn't exist" in e for e in errors)


@pytest.mark.parametrize("rule, missing", [("/model/old /model/new/ 301", "/model/old/"), ("/model/old/ /model/new/ 301", "/model/old")])
def test_page_redirect_needs_both_slash_forms(tmp_path, rule, missing):
    assert redirect_errors(_site(tmp_path, rule)) == [f"_redirects: {rule.split()[0]} has no rule for {missing}"]


def test_files_dont_need_a_slash_form(tmp_path):
    assert redirect_errors(_site(tmp_path, "/og/old.png /og/new.png 301")) == []


def test_redirect_shadowed_by_a_real_page_fails(tmp_path):
    errors = redirect_errors(_site(tmp_path, "/model/new /index.html 301\n/model/new/ /index.html 301\n"))
    assert len(errors) == 2 and all("real page" in e for e in errors)


@pytest.mark.parametrize("text", ["Score: NaN", "by undefined", "Invalid Date", "[object Object]"])
def test_broken_values_are_found(tmp_path, text):
    _site(tmp_path)
    (tmp_path / "model" / "new" / "index.html").write_text(f"<p>{text}</p>")
    assert broken_values(tmp_path) == [f"model/new/index.html: contains ['{text.split()[-1] if text[0] in 'Sb' else text}']"]


@pytest.mark.parametrize("text", ["<script>if (x === undefined) y();</script>", "<p>undefinedness, Nancy</p>"])
def test_ordinary_text_and_scripts_are_not_broken_values(tmp_path, text):
    _site(tmp_path)
    (tmp_path / "index.html").write_text(text)
    assert broken_values(tmp_path) == []


def test_cli_fails_on_a_problem_and_passes_without_one(tmp_path):
    _site(tmp_path, COMPLETE)
    assert main(["--dist", str(tmp_path)]) == 0
    (tmp_path / "index.html").write_text("NaN")
    assert main(["--dist", str(tmp_path)]) == 1


def test_cli_fails_with_no_build(tmp_path):
    assert main(["--dist", str(tmp_path)]) == 1
