from frontmatter import parse


POST = """---
date: 2026-09-21
items:
  - 2026-09-17-crowe-1911-census
  - 2026-09-19-chough
sent:
---

*Family history — 21 September*

Body text.
"""


def test_parses_scalar_and_list_keys():
    meta, body = parse(POST)
    assert meta["date"] == "2026-09-21"
    assert meta["items"] == ["2026-09-17-crowe-1911-census", "2026-09-19-chough"]


def test_empty_value_is_empty_string():
    meta, _ = parse(POST)
    assert meta["sent"] == ""


def test_body_starts_after_closing_fence_without_leading_blank_lines():
    _, body = parse(POST)
    assert body.startswith("*Family history — 21 September*")
    assert body.endswith("Body text.\n")


def test_text_without_front_matter_is_all_body():
    meta, body = parse("just words\n")
    assert meta == {}
    assert body == "just words\n"


def test_empty_list_key():
    meta, _ = parse("---\nitems:\n---\nx\n")
    assert meta["items"] == ""
