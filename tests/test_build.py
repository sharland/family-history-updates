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
    pages = build.build(root)
    assert f"{SITE_URL}sharland-crowe/" in pages[root / "docs" / "sharland-crowe" / "index.html"]
    for path, html in pages.items():
        if path.name == ".nojekyll":
            continue
        assert "<script" not in html and "<img" not in html
        for banned in ("src=", "@import", "url(", "mailto:"):
            assert banned not in html, banned
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


def test_build_emits_empty_nojekyll(tmp_path):
    root = make_repo(tmp_path)
    assert build.build(root)[root / "docs" / ".nojekyll"] == ""


def test_committed_docs_are_current():
    for path, content in build.build(build.ROOT).items():
        assert path.is_file(), f"{path} missing - run python site/build.py"
        assert path.read_text(encoding="utf-8") == content, f"{path} is stale - run python site/build.py"


# ---- publish gate ----
from check import load_living
from test_check import draft_text

LIVING = Path(__file__).parent / "fixtures" / "living.txt"


def gate_repo(tmp_path, text, branch="sharland-crowe", sent="2026-09-21"):
    root = make_repo(tmp_path)
    for old in (root / "posts").rglob("*.md"):
        old.unlink()
    folder = root / "posts" / branch
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "2026-09-21.md").write_text(text.replace("sent:\n", f"sent: {sent}\n", 1), encoding="utf-8", newline="\n")
    return root


def test_gate_passes_a_compliant_sent_post(tmp_path):
    root = gate_repo(tmp_path, draft_text())
    assert build.gate(root, LIVING) == []
    assert build.main(["--living", str(LIVING)], root=root) == 0
    assert (root / "docs" / "sharland-crowe" / "index.html").is_file()


def test_gate_does_not_apply_the_length_guide_to_a_sent_post(tmp_path):
    root = gate_repo(tmp_path, draft_text(words=251))
    assert build.gate(root, LIVING) == []


def test_gate_ignores_unsent_drafts(tmp_path):
    root = gate_repo(tmp_path, draft_text(opening="Alice Penrose remembers it."), sent="")
    assert build.gate(root, LIVING) == []


def test_hand_edited_living_name_is_refused_and_nothing_written(tmp_path, capsys):
    root = gate_repo(tmp_path, draft_text(opening="Alice Penrose remembers it."))
    assert build.main(["--living", str(LIVING)], root=root) == 1
    out = capsys.readouterr().out
    assert "PROBLEM: posts/sharland-crowe/2026-09-21.md:" in out.replace("\\", "/")
    assert not (root / "docs").exists()


def test_post_with_wrong_branch_link_is_refused(tmp_path, capsys):
    root = gate_repo(tmp_path, draft_text(link="Read past updates: " + SITE_URL + "ferreira-gresty/"))
    assert build.main(["--living", str(LIVING)], root=root) == 1
    assert "last line must be exactly" in capsys.readouterr().out
    assert not (root / "docs").exists()


def test_post_in_wrong_folder_is_refused(tmp_path):
    root = gate_repo(tmp_path, draft_text(), branch="ferreira-gresty")
    assert any("last line must be exactly" in p for p in build.gate(root, LIVING))


def test_missing_living_list_warns_but_still_enforces_list_free_rules(tmp_path, capsys):
    missing = tmp_path / "nope.txt"
    root = gate_repo(tmp_path, draft_text(link="Read past updates: https://example.com/"))
    assert build.main(["--living", str(missing)], root=root) == 1
    cap = capsys.readouterr()
    assert "WARNING: living-people list unavailable - name checks were SKIPPED" in cap.err
    assert "last line" in cap.out
    assert not (root / "docs").exists()
    ok = gate_repo(tmp_path / "ok", draft_text())
    assert build.main(["--living", str(missing)], root=ok) == 0
    assert "SKIPPED" in capsys.readouterr().err
