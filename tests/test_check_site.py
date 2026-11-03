import pytest

from scripts.check_site import broken_values, main, redirect_errors, sitemap_errors, structure_errors


GOOD_PAGE = "<main><h1>ok</h1></main>"


def _site(tmp_path, redirects=""):
    (tmp_path / "index.html").write_text(GOOD_PAGE)
    (tmp_path / "model" / "new").mkdir(parents=True)
    (tmp_path / "model" / "new" / "index.html").write_text(GOOD_PAGE)
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


@pytest.mark.parametrize("html, value", [
    ("<p>Score: NaN</p>", "NaN"),
    ("<td>undefined</td>", "undefined"),
    ('<a href="/model/undefined/">x</a>', "undefined"),
    ("<p>Invalid Date</p>", "Invalid Date"),
    ("<p>[object Object]</p>", "[object Object]"),
])
def test_broken_values_are_found(tmp_path, html, value):
    _site(tmp_path)
    (tmp_path / "model" / "new" / "index.html").write_text(html)
    assert broken_values(tmp_path) == [f"model/new/index.html: contains ['{value}']"]


@pytest.mark.parametrize("html", [
    "<script>if (x === undefined) y();</script>",
    "<p>undefinedness, Nancy</p>",
    "<p>The exploit relied on undefined behavior.</p>",
])
def test_ordinary_text_and_scripts_are_not_broken_values(tmp_path, html):
    _site(tmp_path)
    (tmp_path / "index.html").write_text(html)
    assert broken_values(tmp_path) == []


def test_missing_redirects_file_fails(tmp_path):
    _site(tmp_path)
    (tmp_path / "_redirects").unlink()
    assert "missing from the build" in redirect_errors(tmp_path)[0]


def test_duplicate_redirect_source_fails(tmp_path):
    errors = redirect_errors(_site(tmp_path, "/og/old.png /og/new.png 301\n/og/old.png /og/new.png 301\n"))
    assert errors == ["_redirects: /og/old.png is listed twice"]


def test_redirect_with_no_target_fails_without_crashing(tmp_path):
    assert redirect_errors(_site(tmp_path, "/x\n")) == ["_redirects: '/x' has no target"]


@pytest.mark.parametrize("rule", ["  # an indented comment", "/x.png https://example.com/ 301", "/blog/* /:splat 301", "/a/:id /b/:id 301"])
def test_comments_external_targets_and_patterns_are_allowed(tmp_path, rule):
    assert redirect_errors(_site(tmp_path, rule)) == []


def test_cli_fails_on_a_problem_and_passes_without_one(tmp_path):
    _site(tmp_path, COMPLETE)
    _sitemap(tmp_path)
    assert main(["--dist", str(tmp_path)]) == 0
    (tmp_path / "index.html").write_text("NaN")
    assert main(["--dist", str(tmp_path)]) == 1


def test_cli_fails_with_no_build(tmp_path):
    assert main(["--dist", str(tmp_path)]) == 1


def test_good_page_has_no_structure_errors(tmp_path):
    _site(tmp_path)
    assert structure_errors(tmp_path) == []


@pytest.mark.parametrize("html, error", [
    ("<noscript><style>x</style><main><h1>ok</h1></main>", "unclosed <noscript>"),  # swallowed the whole page once
    ("<script>x()<main><h1>ok</h1></main>", "unclosed <script>"),
    ("<main><p>no heading</p></main>", "no <h1> inside <main>"),
    ("<noscript><main><h1>only here</h1></main></noscript>", "no <h1> inside <main>"),
])
def test_page_structure_problems_are_found(tmp_path, html, error):
    _site(tmp_path)
    (tmp_path / "index.html").write_text(html)
    assert f"index.html: {error}" in structure_errors(tmp_path)


SITEMAP_INDEX = "<sitemapindex><sitemap><loc>https://felonybench.ai/sitemap-0.xml</loc></sitemap></sitemapindex>"


def _sitemap(dist, *paths):
    (dist / "sitemap-index.xml").write_text(SITEMAP_INDEX)
    if not (dist / "index.html").exists():
        (dist / "index.html").write_text("<html></html>")
    paths = ("/", *paths)
    urls = "".join(f"<url><loc>https://felonybench.ai{path}</loc></url>" for path in paths)
    (dist / "sitemap-0.xml").write_text(f"<urlset>{urls}</urlset>")


def test_sitemap_with_indexable_pages_is_fine(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "index.html").write_text("<html></html>")
    _sitemap(tmp_path, "/a/")
    assert sitemap_errors(tmp_path) == []


@pytest.mark.parametrize("meta", ['<meta name="robots" content="noindex" />', "<meta name=robots content=noindex>"])
def test_sitemap_cannot_list_a_noindex_page(tmp_path, meta):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "index.html").write_text(f"<html><head>{meta}</head></html>")
    _sitemap(tmp_path, "/a/")
    assert sitemap_errors(tmp_path) == ["sitemap-0.xml: /a/ is marked noindex"]


def test_sitemap_cannot_list_a_missing_page(tmp_path):
    _sitemap(tmp_path, "/gone/")
    assert sitemap_errors(tmp_path) == ["sitemap-0.xml: /gone/ has no page"]


def test_a_missing_sitemap_is_an_error(tmp_path):
    assert sitemap_errors(tmp_path) == ["sitemap-index.xml is missing, but robots.txt points at it"]


def test_a_sitemap_without_the_homepage_is_an_error(tmp_path):
    (tmp_path / "sitemap-index.xml").write_text(SITEMAP_INDEX)
    (tmp_path / "sitemap-0.xml").write_text("<urlset></urlset>")
    assert sitemap_errors(tmp_path) == ["the sitemap doesn't list the homepage"]


def test_an_index_pointing_at_a_missing_sitemap_is_an_error(tmp_path):
    (tmp_path / "sitemap-index.xml").write_text(SITEMAP_INDEX)
    assert "sitemap-index.xml: sitemap-0.xml is missing" in sitemap_errors(tmp_path)


def test_a_homepage_in_a_sitemap_the_index_doesnt_link_doesnt_count(tmp_path):
    _sitemap(tmp_path)
    (tmp_path / "sitemap-index.xml").write_text("<sitemapindex></sitemapindex>")
    assert sitemap_errors(tmp_path) == ["the sitemap doesn't list the homepage"]
