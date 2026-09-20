import shutil
from pathlib import Path

import build
from build import SITE_URL, TITLES

FIX = Path(__file__).parent / "fixtures" / "repo"


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    (root / "site").mkdir()
    shutil.copy(Path(build.__file__).parent / "template.html", root / "site" / "template.html")
    return root


def test_branch_page_lists_sent_posts_newest_first_with_anchors_and_dates(tmp_path):
    root = make_repo(tmp_path)
    pages = build.build(root)
    html = pages[root / "docs" / "sharland-crowe" / "index.html"]
    assert html.index('id="2026-09-15"') < html.index('id="2026-09-01"')
    assert "Sent on Wednesday 16 September 2026" in html
    assert "<h2>Family history — 15 September</h2>" in html
    assert "<strong>Something newer.</strong> With <em>emphasis</em>." in html
    assert TITLES["sharland-crowe"] in html


def test_unsent_post_never_appears(tmp_path):
    root = make_repo(tmp_path)
    pages = build.build(root)
    joined = "".join(pages.values())
    assert "never sent" not in joined
    assert "8 September" not in joined


def test_escaping(tmp_path):
    root = make_repo(tmp_path)
    html = build.build(root)[root / "docs" / "sharland-crowe" / "index.html"]
    assert "An early post &amp; a test of escaping &lt;here&gt;." in html


def test_empty_branch_page_is_valid_and_says_so(tmp_path):
    root = make_repo(tmp_path)
    html = build.build(root)[root / "docs" / "ferreira-gresty" / "index.html"]
    assert "<p>No updates yet.</p>" in html
    assert TITLES["ferreira-gresty"] in html
    assert html.startswith("<!DOCTYPE html>")


def test_landing_links_to_both_branches(tmp_path):
    root = make_repo(tmp_path)
    html = build.build(root)[root / "docs" / "index.html"]
    assert f'href="{SITE_URL}sharland-crowe/"' in html
    assert f'href="{SITE_URL}ferreira-gresty/"' in html


def test_no_javascript_images_or_external_requests(tmp_path):
    root = make_repo(tmp_path)
    for html in build.build(root).values():
        assert "<script" not in html and "<img" not in html
        assert 'href="http' not in html.replace(f'href="{SITE_URL}', "").replace('href="https://sharland.github.io/family-history-updates/', "")
        assert 'lang="en-GB"' in html


def test_build_is_deterministic_and_write_creates_files(tmp_path):
    root = make_repo(tmp_path)
    first = build.build(root)
    build.write(first)
    second = build.build(root)
    assert first == second
    for path, content in second.items():
        assert path.read_text(encoding="utf-8") == content
