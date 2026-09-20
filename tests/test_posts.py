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
