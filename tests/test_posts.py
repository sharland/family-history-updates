# tests/test_posts.py
from pathlib import Path
from posts import BRANCHES, Post, load_posts, long_date

FIX = Path(__file__).parent / "fixtures" / "repo"


def test_branches_are_exactly_the_two():
    assert BRANCHES == ("sharland-crowe", "ferreira-gresty")


def test_loads_only_sent_posts_newest_first():
    posts = load_posts(FIX, "sharland-crowe")
    assert [p.date for p in posts] == ["2026-09-15", "2026-09-01"]
    assert all(isinstance(p, Post) for p in posts)
    assert posts[0].sent == "2026-09-16"
    assert posts[0].items == ["2026-09-10-second", "2026-09-12-third"]
    assert posts[0].branch == "sharland-crowe"
    assert posts[0].body.startswith("*Family history — 15 September*")


def test_empty_branch_loads_nothing():
    assert load_posts(FIX, "ferreira-gresty") == []


def test_long_date():
    assert long_date("2026-09-21") == "Monday 21 September 2026"
    assert long_date("2026-09-02") == "Wednesday 2 September 2026"


def branch_repo(tmp_path, files):
    folder = tmp_path / "posts" / "sharland-crowe"
    folder.mkdir(parents=True)
    for name, text in files.items():
        (folder / name).write_text(text, encoding="utf-8", newline="\n")
    return tmp_path


def test_whitespace_only_sent_is_not_loaded(tmp_path):
    root = branch_repo(tmp_path, {"a.md": "---\ndate: 2026-09-01\nsent:   \n---\nBody\n"})
    assert load_posts(root, "sharland-crowe") == []


def test_file_without_front_matter_is_not_loaded_and_does_not_crash(tmp_path):
    root = branch_repo(tmp_path, {"a.md": "Just some text, no header.\n"})
    assert load_posts(root, "sharland-crowe") == []


def test_same_day_posts_come_out_in_deterministic_order(tmp_path):
    same = "---\ndate: {d}\nsent: 2026-09-20\n---\nBody\n"
    root = branch_repo(tmp_path, {
        "2026-09-10-a.md": same.format(d="2026-09-10"),
        "2026-09-12-b.md": same.format(d="2026-09-12"),
        "2026-09-12-a.md": same.format(d="2026-09-12"),
    })
    assert [p.path.name for p in load_posts(root, "sharland-crowe")] == [
        "2026-09-12-b.md", "2026-09-12-a.md", "2026-09-10-a.md"]


def test_items_given_as_a_single_string_becomes_a_list(tmp_path):
    root = branch_repo(tmp_path, {"a.md": "---\ndate: 2026-09-01\nitems: 2026-08-30-only\nsent: 2026-09-02\n---\nBody\n"})
    assert load_posts(root, "sharland-crowe")[0].items == ["2026-08-30-only"]
