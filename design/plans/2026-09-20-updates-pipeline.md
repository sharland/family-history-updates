# Family History Updates Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the queue, checker, static-site build and first content for Brian's two-stream family history updates, so that a WhatsApp post is drafted from queued items, checked against the living-people rule, pasted by Brian, and then published to GitHub Pages.

**Architecture:** Plain Markdown files in per-branch folders are the whole data model (`queue\items`, `queue\ready`, `queue\used`, `posts`). Four small standard-library Python modules under `site\` do everything: `frontmatter.py` parses the file header, `wa.py` converts WhatsApp formatting to HTML, `posts.py` loads sent posts, `build.py` renders `docs\`, and `check.py` lints a draft. GitHub Pages serves `docs\` straight from `main`.

**Tech Stack:** Python 3.14 (standard library only), pytest 9, git, `gh` CLI (logged in as `sharland`), GitHub Pages.

**Spec:** `design\2026-09-20-updates-pipeline-design.md` — read it first; every task below cites the section it implements.

## Global Constraints

- Python **standard library only** in `site\` — no third-party imports (spec §8). `pytest` is dev-only.
- Repository is **public**. Nothing private goes in it: no living-people list, no style notes naming relatives, no research-folder paths in post bodies (spec §4). The list and notes live in `D:\Dropbox\Family\family history\.claude\`.
- Branch keys are exactly `sharland-crowe` and `ferreira-gresty`; **branch is the folder**, never a field (spec §4).
- Post bodies use **WhatsApp formatting** — `*bold*`, `_italic_`, blank-line paragraphs, no Markdown — and end with `Read past updates: https://sharland.github.io/family-history-updates/<branch>/` (spec §5.2).
- A post **without a `sent:` date is never rendered**; a sent post is **never edited** (spec §3).
- Living people: **first name and current-surname initial only**; **no minors** (spec §3, §6).
- Used items are **moved to `queue\used\<branch>\`**, never deleted (spec §3).
- `build.py` output must be **deterministic** — no timestamps, no environment-dependent content (spec §8).
- Page: **no JavaScript, no external requests, no images, no email address**; body 20px, line-height 1.6, max-width 38em, `lang="en-GB"` (spec §8).
- Every commit message ends with the trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. Run all git commands from `D:\Claude-work\family-history-updates` in Git Bash with forward slashes.
- Run tests with `python -m pytest -q` from the repo root; `pytest.ini` puts `site\` on the path so modules import each other by bare name (`from wa import inline`).

## Rulings made at preflight (20 Sep 2026) — binding on every task below

1. **Work on `main` directly.** A fresh, solo repository whose plan must publish from `main`; no worktree.
2. **Nothing private in this repository, ever — including test fixtures.** Fixtures use *fictional* people only (Alice Margaret Penrose, Peter Trevithick, Tamsin Heather Rowe, Walter Noel Penrose, John Trewin). No real living relative's name appears in any file here. Item `source:` values that would contain a living person's name are written in display form (`... Conversation with Alice P.md`).
3. **Unsent drafts are never committed.** `queue/items/*` and `queue/ready/*` are git-ignored (only `.gitkeep` is tracked); `queue/used/*` and `posts/*` are committed **at the moment of sending**. This is the spec's "nothing unsent is ever published" applied to a public repository.
4. **The repository is currently PRIVATE** (an earlier draft of the design and plan named living people, including a minor; that history must be cleaned before the repo goes public). **No `git push` and no GitHub Pages enablement in this run** — Task 7 is held; commits are local. Brian decides how the history is cleaned.
5. **`check.py` exposes `count_words(body)`** as the single word-count rule, so tests can build drafts of exact length.
6. **Commit trailer:** `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` (the session's model), replacing the trailer shown in the task snippets.

---

## File structure

```
family-history-updates\
  README.md                      Task 1 — what this is, how a post gets out
  pytest.ini                     Task 1 — testpaths=tests, pythonpath=site
  requirements-dev.txt           Task 1 — pytest
  queue\items\{sharland-crowe,ferreira-gresty}\.gitkeep     Task 1
  queue\ready\{sharland-crowe,ferreira-gresty}\.gitkeep     Task 1
  queue\used\{sharland-crowe,ferreira-gresty}\.gitkeep      Task 1
  posts\{sharland-crowe,ferreira-gresty}\.gitkeep           Task 1
  site\frontmatter.py            Task 2 — parse(text) -> (meta, body)
  site\wa.py                     Task 3 — inline(), blocks(), render_post()
  site\posts.py                  Task 4 — BRANCHES, Post, load_posts(), long_date()
  site\template.html             Task 5 — the one page template
  site\build.py                  Task 5 — build(), write(), TITLES, SITE_URL
  site\check.py                  Task 6 — load_living(), problems(), main()
  site\seed_living.py            Task 8 — one-off GEDCOM → living-people list
  docs\index.html, docs\<branch>\index.html                 Task 5 (generated), Task 7 (published)
  tests\test_frontmatter.py, test_wa.py, test_posts.py, test_build.py, test_check.py, test_seed_living.py
  tests\fixtures\                Tasks 4–6, 8
```

Private, in `D:\Dropbox\Family\family history\.claude\`: `living-people.txt` (Task 8), `digest-style.md` (Task 8), the nudge memory (Task 10, in Claude's memory directory).

---

### Task 1: Repository scaffold

**Files:**
- Create: `README.md`, `pytest.ini`, `requirements-dev.txt`, the twelve `.gitkeep` files listed above.

**Interfaces:**
- Produces: the folder layout every later task writes into; `pytest.ini` so `tests\` can import `site\` modules by bare name.

- [ ] **Step 1: Create the folders and pytest config**

```bash
cd /d/Claude-work/family-history-updates
for b in sharland-crowe ferreira-gresty; do
  mkdir -p "queue/items/$b" "queue/ready/$b" "queue/used/$b" "posts/$b"
  touch "queue/items/$b/.gitkeep" "queue/ready/$b/.gitkeep" "queue/used/$b/.gitkeep" "posts/$b/.gitkeep"
done
mkdir -p site tests/fixtures docs
printf '[pytest]\ntestpaths = tests\npythonpath = site\n' > pytest.ini
printf 'pytest>=8\n' > requirements-dev.txt
cat >> .gitignore <<'EOF'
.superpowers/
queue/items/*/*
queue/ready/*/*
!queue/items/*/.gitkeep
!queue/ready/*/.gitkeep
EOF
```

- [ ] **Step 2: Write README.md**

```markdown
# Family history updates

Short posts from Brian about what he has been finding out about the family — sent first to a family WhatsApp group, then kept here so they can be read again.

**Read them:** <https://sharland.github.io/family-history-updates/>

There are two streams, one for each side of the family, named for Brian's grandparents:

- **Sharland and Crowe** — <https://sharland.github.io/family-history-updates/sharland-crowe/>
- **Ferreira and Gresty** — <https://sharland.github.io/family-history-updates/ferreira-gresty/>

Living relatives are referred to by first name and initial only. Replies go to the WhatsApp group, not here.

## How a post gets out

1. As things are found, a short note goes into `queue/items/<branch>/` — one file per finding.
2. When there are three or more, they are assembled into a post in `queue/ready/<branch>/`, checked (`python site/check.py <file>`), and handed to Brian.
3. Brian pastes it into WhatsApp. Only then does the file move to `posts/<branch>/` with its `sent:` date, the items it used move to `queue/used/<branch>/`, and `python site/build.py` regenerates `docs/`, which GitHub Pages serves.

Posts without a `sent:` date are never published. Sent posts are never edited; corrections go in the next post.

The design is in `design/`. Tests: `python -m pytest -q`.
```

- [ ] **Step 3: Confirm pytest runs with nothing to collect**

Run: `python -m pytest -q`
Expected: `no tests ran` (exit code 5 is fine here).

- [ ] **Step 4: Commit**

```bash
git add README.md pytest.ini requirements-dev.txt .gitignore queue posts
git commit -q -m "$(cat <<'EOF'
Scaffold the repository layout

Per-branch queue and posts folders, pytest config putting site/ on the
path, and a README describing how a post gets out.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Front matter parser

**Files:**
- Create: `site/frontmatter.py`
- Test: `tests/test_frontmatter.py`

**Interfaces:**
- Produces: `parse(text: str) -> tuple[dict[str, str | list[str]], str]` — `meta` maps keys to strings, except keys followed by `- ` list lines, which map to `list[str]`; `body` is everything after the closing `---`, with leading blank lines removed. Text with no front matter returns `({}, text)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_frontmatter.py
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_frontmatter.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'frontmatter'`

- [ ] **Step 3: Implement**

```python
# site/frontmatter.py
"""Read the front matter at the top of an item or post file.

The format is deliberately tiny: a block between two lines of '---',
'key: value' lines, and list values as following lines starting '- '.
No YAML library, so no surprises.
"""


def parse(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta: dict = {}
    key = None
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            i += 1
            break
        stripped = line.strip()
        if stripped.startswith("- ") and key is not None:
            current = meta.get(key, "")
            if isinstance(current, str):
                current = [current] if current else []
            current.append(stripped[2:].strip())
            meta[key] = current
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            meta[key] = value.strip()
        i += 1
    body = "\n".join(lines[i:]).lstrip("\n")
    if text.endswith("\n") and body and not body.endswith("\n"):
        body += "\n"
    return meta, body
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_frontmatter.py -q`
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add site/frontmatter.py tests/test_frontmatter.py
git commit -q -m "$(cat <<'EOF'
Add the front matter parser

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: WhatsApp dialect to HTML

**Files:**
- Create: `site/wa.py`
- Test: `tests/test_wa.py`

**Interfaces:**
- Produces: `inline(text: str) -> str` (escaped HTML with `<strong>`, `<em>`, `<a>`), `blocks(body: str) -> list[str]` (paragraph blocks split on blank lines), `render_post(body: str) -> tuple[str, str]` returning `(title, html)` where `title` is the first block with its asterisks stripped and `html` is the remaining blocks as `<p>` elements; the block beginning `Read past updates:` gets `class="link"`. Line breaks inside a block become `<br>`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wa.py
from wa import inline, blocks, render_post


def test_bold_and_italic():
    assert inline("*Bold* and _italic_.") == "<strong>Bold</strong> and <em>italic</em>."


def test_html_is_escaped_before_formatting():
    assert inline("Tom & *Jerry* <3") == "Tom &amp; <strong>Jerry</strong> &lt;3"


def test_asterisk_with_space_after_is_not_bold():
    assert inline("2 * 3 = 6") == "2 * 3 = 6"


def test_url_becomes_link_and_underscores_inside_it_are_safe():
    out = inline("see https://example.org/a_b_c now")
    assert out == 'see <a href="https://example.org/a_b_c">https://example.org/a_b_c</a> now'


def test_blocks_split_on_blank_lines_and_trim():
    assert blocks("a\n\n\n b \n\nc\n") == ["a", "b", "c"]


def test_render_post_title_and_paragraphs():
    body = "*Family history — 21 September*\n\nFirst para.\nsecond line\n\nRead past updates: https://x.test/y/\n"
    title, html = render_post(body)
    assert title == "Family history — 21 September"
    assert html == (
        "<p>First para.<br>\nsecond line</p>\n"
        '<p class="link">Read past updates: <a href="https://x.test/y/">https://x.test/y/</a></p>'
    )


def test_render_post_empty():
    assert render_post("") == ("", "")
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_wa.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'wa'`

- [ ] **Step 3: Implement**

```python
# site/wa.py
"""Convert WhatsApp's own text formatting to HTML.

Posts are written the way they are pasted into WhatsApp: *bold*,
_italic_, paragraphs separated by blank lines, a bare URL at the end.
This module turns exactly that, and nothing more, into HTML.
"""
import html
import re

BOLD = re.compile(r"\*(\S(?:[^*\n]*?\S)?)\*")
ITALIC = re.compile(r"_(\S(?:[^_\n]*?\S)?)_")
URL = re.compile(r"https?://[^\s<>\"]+")


def _format(segment: str) -> str:
    out = html.escape(segment, quote=True)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    out = ITALIC.sub(r"<em>\1</em>", out)
    return out


def inline(text: str) -> str:
    parts = []
    pos = 0
    for m in URL.finditer(text):
        parts.append(_format(text[pos:m.start()]))
        url = html.escape(m.group(0), quote=True)
        parts.append(f'<a href="{url}">{url}</a>')
        pos = m.end()
    parts.append(_format(text[pos:]))
    return "".join(parts)


def blocks(body: str) -> list[str]:
    return [b.strip() for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]


def render_post(body: str) -> tuple[str, str]:
    bs = blocks(body)
    if not bs:
        return "", ""
    title = bs[0].strip().strip("*").strip()
    paragraphs = []
    for b in bs[1:]:
        cls = ' class="link"' if b.startswith("Read past updates:") else ""
        paragraphs.append(f"<p{cls}>{inline(b).replace(chr(10), '<br>' + chr(10))}</p>")
    return title, "\n".join(paragraphs)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_wa.py -q`
Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add site/wa.py tests/test_wa.py
git commit -q -m "$(cat <<'EOF'
Convert WhatsApp formatting to HTML

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Loading sent posts

**Files:**
- Create: `site/posts.py`
- Create: `tests/fixtures/repo/posts/sharland-crowe/2026-09-01.md`, `.../2026-09-15.md`, `.../2026-09-08-unsent.md`, `tests/fixtures/repo/posts/ferreira-gresty/.gitkeep`
- Test: `tests/test_posts.py`

**Interfaces:**
- Consumes: `frontmatter.parse`.
- Produces: `BRANCHES = ("sharland-crowe", "ferreira-gresty")`; `@dataclass Post(branch: str, date: str, sent: str, items: list[str], body: str, path: Path)`; `load_posts(root: Path, branch: str) -> list[Post]` — only files with a non-empty `sent:`, newest first by `(sent, date, filename)`; `long_date(iso: str) -> str` → `"Sunday 21 September 2026"` (no leading zero on the day).

- [ ] **Step 1: Create the fixtures**

`tests/fixtures/repo/posts/sharland-crowe/2026-09-01.md`:

```
---
date: 2026-09-01
items:
  - 2026-08-30-first
sent: 2026-09-02
---
*Family history — 1 September*

An early post & a test of escaping <here>.

Read past updates: https://sharland.github.io/family-history-updates/sharland-crowe/
```

`tests/fixtures/repo/posts/sharland-crowe/2026-09-15.md`:

```
---
date: 2026-09-15
items:
  - 2026-09-10-second
  - 2026-09-12-third
sent: 2026-09-16
---
*Family history — 15 September*

*Something newer.* With _emphasis_.

Read past updates: https://sharland.github.io/family-history-updates/sharland-crowe/
```

`tests/fixtures/repo/posts/sharland-crowe/2026-09-08-unsent.md`:

```
---
date: 2026-09-08
items:
  - 2026-09-05-draft
sent:
---
*Family history — 8 September*

This one was never sent and must not appear anywhere.

Read past updates: https://sharland.github.io/family-history-updates/sharland-crowe/
```

Plus an empty `tests/fixtures/repo/posts/ferreira-gresty/.gitkeep`.

- [ ] **Step 2: Write the failing tests**

```python
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
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_posts.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'posts'`

- [ ] **Step 4: Implement**

```python
# site/posts.py
"""Load the sent posts of a branch, newest first."""
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from frontmatter import parse

BRANCHES = ("sharland-crowe", "ferreira-gresty")


@dataclass
class Post:
    branch: str
    date: str
    sent: str
    items: list[str] = field(default_factory=list)
    body: str = ""
    path: Path = Path()


def load_posts(root: Path, branch: str) -> list[Post]:
    folder = Path(root) / "posts" / branch
    found: list[Post] = []
    for path in sorted(folder.glob("*.md")):
        meta, body = parse(path.read_text(encoding="utf-8"))
        sent = str(meta.get("sent", "")).strip()
        if not sent:
            continue
        items = meta.get("items", [])
        if isinstance(items, str):
            items = [items] if items else []
        found.append(Post(branch, str(meta.get("date", path.stem)), sent, list(items), body, path))
    found.sort(key=lambda p: (p.sent, p.date, p.path.name), reverse=True)
    return found


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_posts.py -q`
Expected: `4 passed`

- [ ] **Step 6: Commit**

```bash
git add site/posts.py tests/test_posts.py tests/fixtures
git commit -q -m "$(cat <<'EOF'
Load sent posts per branch, newest first

Unsent posts are skipped at load time, which is what keeps them off
the page.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: The page build

**Files:**
- Create: `site/template.html`, `site/build.py`
- Test: `tests/test_build.py`
- Generates: `docs/index.html`, `docs/sharland-crowe/index.html`, `docs/ferreira-gresty/index.html`

**Interfaces:**
- Consumes: `posts.BRANCHES`, `posts.load_posts`, `posts.long_date`, `wa.render_post`.
- Produces: `SITE_URL = "https://sharland.github.io/family-history-updates/"`; `TITLES: dict[str, str]`; `build(root: Path) -> dict[Path, str]` mapping output paths to page HTML; `write(files: dict[Path, str]) -> None`; running `python site/build.py` writes `docs\`.

- [ ] **Step 1: Write the template**

`site/template.html` (the `$name` tokens are `string.Template` placeholders):

```html
<!DOCTYPE html>
<html lang="$lang">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
  html { background: #fff; }
  body { margin: 0 auto; padding: 1.5rem 1rem 3rem; max-width: 38em;
         font: 20px/1.6 -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
         color: #1a1a1a; }
  h1 { font-size: 1.6em; line-height: 1.25; margin: 0 0 .5em; }
  h2 { font-size: 1.25em; line-height: 1.3; margin: 2.2em 0 .2em; }
  p { margin: 0 0 1em; }
  p.intro { color: #333; border-bottom: 1px solid #ccc; padding-bottom: 1.2em; }
  p.when { color: #555; font-size: .9em; margin-top: 0; }
  article { border-bottom: 1px solid #e3e3e3; padding-bottom: .5em; }
  a { color: #0b4f9c; }
  a:focus, a:hover { text-decoration-thickness: 2px; }
  footer { margin-top: 3em; font-size: .9em; color: #555; }
  ul { padding-left: 1.2em; } li { margin: .4em 0; }
</style>
</head>
<body>
<h1>$heading</h1>
<p class="intro">$intro</p>
<main>
$content
</main>
<footer><a href="$home">All family history updates</a></footer>
</body>
</html>
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_build.py
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
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_build.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 4: Implement**

```python
# site/build.py
"""Render the sent posts of both branches into docs/ for GitHub Pages.

No arguments, no dependencies, deterministic: the same posts produce
byte-identical pages.
"""
import html as htmlmod
import sys
from pathlib import Path
from string import Template

from posts import BRANCHES, load_posts, long_date
from wa import render_post

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://sharland.github.io/family-history-updates/"

TITLES = {
    "sharland-crowe": "Sharland and Crowe family history — updates from Brian",
    "ferreira-gresty": "Ferreira and Gresty family history — updates from Brian",
}

INTRO = (
    "Short updates from Brian on what he has been finding out about the family, "
    "posted first to the family WhatsApp group and kept here so they can be read again. "
    "Living relatives are referred to by first name and initial only. "
    "Replies are welcome on WhatsApp."
)

LANDING_TITLE = "Family history updates from Brian"
LANDING_INTRO = (
    "Brian’s family history updates, kept in two streams — one for each side of the family, "
    "named for his grandparents. Pick yours."
)


def render_article(post) -> str:
    title, body_html = render_post(post.body)
    return (
        f'<article id="{htmlmod.escape(post.date)}">\n'
        f"<h2>{htmlmod.escape(title)}</h2>\n"
        f'<p class="when">Sent on {long_date(post.sent)}</p>\n'
        f"{body_html}\n</article>"
    )


def render_branch_page(branch: str, posts: list, template: str) -> str:
    content = "\n".join(render_article(p) for p in posts) or "<p>No updates yet.</p>"
    return Template(template).substitute(
        lang="en-GB", title=TITLES[branch], heading=TITLES[branch],
        intro=INTRO, content=content, home=SITE_URL,
    )


def render_landing(template: str) -> str:
    items = "".join(f'<li><a href="{SITE_URL}{b}/">{TITLES[b]}</a></li>' for b in BRANCHES)
    return Template(template).substitute(
        lang="en-GB", title=LANDING_TITLE, heading=LANDING_TITLE,
        intro=LANDING_INTRO, content=f"<ul>{items}</ul>", home=SITE_URL,
    )


def build(root: Path = ROOT) -> dict[Path, str]:
    root = Path(root)
    template = (root / "site" / "template.html").read_text(encoding="utf-8")
    pages = {root / "docs" / "index.html": render_landing(template)}
    for branch in BRANCHES:
        pages[root / "docs" / branch / "index.html"] = render_branch_page(
            branch, load_posts(root, branch), template
        )
    return pages


def write(files: dict[Path, str]) -> None:
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    pages = build()
    write(pages)
    for path in pages:
        print("wrote", path.relative_to(ROOT))
    sys.exit(0)
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_build.py -q`
Expected: `7 passed`

- [ ] **Step 6: Build the real (empty) site and check it**

Run: `python site/build.py`
Expected: three `wrote docs/...` lines. Open `docs/sharland-crowe/index.html` in a browser (or `preview_start`) and confirm: large type, "No updates yet.", the footer link, nothing else.

- [ ] **Step 7: Commit**

```bash
git add site/template.html site/build.py tests/test_build.py docs
git commit -q -m "$(cat <<'EOF'
Build the two branch pages and the landing page

Standard library only, deterministic, no JavaScript or external
requests; unsent posts are never rendered.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: The draft checker

**Files:**
- Create: `site/check.py`, `tests/fixtures/living.txt`
- Test: `tests/test_check.py`

**Interfaces:**
- Consumes: `frontmatter.parse`, `posts.BRANCHES`, `build.SITE_URL`.
- Produces: `READ_PAST = "Read past updates: "`; `count_words(body: str) -> int` (the body's whitespace-separated tokens, where the closing `Read past updates: <url>` line counts as **one** word); `load_living(path) -> tuple[list[tuple[str, str]], set[str]]` (people as `(full name, display)`, and the lower-cased `shared-surnames:` set); `problems(draft: Path, people, shared) -> list[str]`; `main(argv=None) -> int` (0 clean, 1 problems, 2 usage). CLI: `python site/check.py <draft.md> [--living <file>]`; default living file `D:\Dropbox\Family\family history\.claude\living-people.txt`.
- **Refinement of spec §6 rule 1, agreed:** a *bare surname* is flagged only when it is not in the file's `shared-surnames:` line. Family-line surnames (Sharland, Crowe, Ferreira, Gresty) are borne by the dead and by the page titles, so flagging them bare would fail every draft; a surname carried only by living people (Penrose in the fixture) is still caught.

- [ ] **Step 1: Write the fixture** (fictional people only — see the rulings)

`tests/fixtures/living.txt`:

```
# Living people — full name | how they appear in posts. Comments start with #.
shared-surnames: Sharland, Crowe, Ferreira, Gresty
Alice Margaret Penrose | Alice P.
Peter Trevithick | Peter T.
Tamsin Heather Rowe | —
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_check.py
from pathlib import Path

from build import SITE_URL
from check import READ_PAST, count_words, load_living, main, problems
from frontmatter import parse

FIX = Path(__file__).parent / "fixtures"
TITLE = "*Family history — 21 September*"
OPENING = "Great-grandfather John Trewin kept the Royal Pier Hotel at Weston."


def people():
    return load_living(FIX / "living.txt")


def draft_text(words=200, branch="sharland-crowe", opening=OPENING, extra=(), link=None):
    """A draft whose counted length is exactly `words` (the closing link counts as one)."""
    fixed = [TITLE, opening, *extra]
    filler = " ".join(["Indeed."] * (words - sum(len(p.split()) for p in fixed) - 1))
    paragraphs = [TITLE, opening] + ([filler] if filler else []) + list(extra)
    closing = READ_PAST + SITE_URL + branch + "/" if link is None else link
    body = "\n\n".join(paragraphs) + "\n\n" + closing + "\n"
    return "---\ndate: 2026-09-21\nitems:\n  - x\nsent:\n---\n" + body


def write(tmp_path, text, branch="sharland-crowe"):
    folder = tmp_path / "queue" / "ready" / branch
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "draft.md"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def found(tmp_path, **kw):
    return problems(write(tmp_path, draft_text(**kw), kw.get("branch", "sharland-crowe")), *people())


def test_helper_builds_exact_word_counts():
    for n in (150, 200, 250):
        assert count_words(parse(draft_text(words=n))[1]) == n


def test_parser_reads_people_and_shared_surnames_and_ignores_comments():
    persons, shared = people()
    assert ("Alice Margaret Penrose", "Alice P.") in persons
    assert ("Tamsin Heather Rowe", "—") in persons
    assert shared == {"sharland", "crowe", "ferreira", "gresty"}


def test_clean_draft_passes(tmp_path):
    assert found(tmp_path) == []


def test_full_name_and_short_form_fail(tmp_path):
    assert any("Alice Margaret Penrose" in p for p in found(tmp_path, opening="Alice Margaret Penrose remembers it."))
    assert any("Alice Penrose" in p for p in found(tmp_path / "b", opening="Alice Penrose remembers it."))


def test_bare_unshared_surname_fails_but_shared_surname_passes(tmp_path):
    assert any("Penrose" in p for p in found(tmp_path, opening="The Penrose family kept the hotel."))
    assert found(tmp_path / "b", opening="The Sharland family kept the hotel.") == []


def test_minor_first_name_fails(tmp_path):
    assert any("minor" in p for p in found(tmp_path, opening="Tamsin and Alice P. came too."))


def test_word_count_bounds(tmp_path):
    for i, (n, ok) in enumerate([(150, True), (149, False), (250, True), (251, False)]):
        result = found(tmp_path / str(i), words=n)
        assert (result == []) is ok, (n, result)
        if not ok:
            assert any("words" in p for p in result)


def test_missing_or_wrong_branch_link_fails(tmp_path):
    assert any("last line" in p for p in found(tmp_path, link="Goodbye."))
    wrong = write(tmp_path / "b", draft_text(branch="sharland-crowe"), branch="ferreira-gresty")
    assert any("last line" in p for p in problems(wrong, *people()))


def test_markdown_and_leaked_source_fail(tmp_path):
    cases = [("**Bold**", "**"), ("# A heading", "#"), ("[text](https://x.test)", "link"), ("source: Documents\\x.md", "source:")]
    for i, (line, needle) in enumerate(cases):
        result = found(tmp_path / str(i), extra=(line,))
        assert any(needle in p.lower() or needle in p for p in result), (line, result)


def test_draft_outside_a_branch_folder_fails(tmp_path):
    path = tmp_path / "elsewhere" / "draft.md"
    path.parent.mkdir()
    path.write_text(draft_text(), encoding="utf-8", newline="\n")
    assert any("branch folder" in p for p in problems(path, *people()))


def test_cli_exit_codes(tmp_path, capsys):
    good = write(tmp_path / "g", draft_text())
    assert main([str(good), "--living", str(FIX / "living.txt")]) == 0
    bad = write(tmp_path / "b", draft_text(opening="Alice Penrose remembers it."))
    assert main([str(bad), "--living", str(FIX / "living.txt")]) == 1
    assert "PROBLEM" in capsys.readouterr().out
    assert main([]) == 2
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_check.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'check'`

- [ ] **Step 4: Implement**

```python
# site/check.py
"""Lint one draft post against the rules before Brian sees it.

Usage: python site/check.py <draft.md> [--living <living-people.txt>]
Exit 0 when clean, 1 with problems printed, 2 on usage error.
"""
import re
import sys
from pathlib import Path

from build import SITE_URL
from frontmatter import parse
from posts import BRANCHES

DEFAULT_LIVING = Path(r"D:\Dropbox\Family\family history\.claude\living-people.txt")
MIN_WORDS, MAX_WORDS = 150, 250
READ_PAST = "Read past updates: "


def load_living(path) -> tuple[list[tuple[str, str]], set[str]]:
    people: list[tuple[str, str]] = []
    shared: set[str] = set()
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("shared-surnames:"):
            shared |= {s.strip().lower() for s in line.split(":", 1)[1].split(",") if s.strip()}
            continue
        if "|" not in line:
            continue
        full, display = (s.strip() for s in line.split("|", 1))
        people.append((full, display))
    return people, shared


def count_words(body: str) -> int:
    lines = [l for l in body.strip().splitlines() if l.strip()]
    if lines and lines[-1].strip().startswith(READ_PAST):
        return len(re.findall(r"\S+", "\n".join(lines[:-1]))) + 1
    return len(re.findall(r"\S+", body))


def _word_re(phrase: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + r"\s+".join(map(re.escape, phrase.split())) + r"(?!\w)", re.IGNORECASE)


def name_forms(full: str) -> set[str]:
    parts = full.split()
    forms = {full}
    if len(parts) >= 3:
        forms.add(f"{parts[0]} {parts[-1]}")
        forms.add(f"{parts[0]} {parts[1][0]}. {parts[-1]}")
    return forms


def problems(draft: Path, people, shared) -> list[str]:
    draft = Path(draft)
    _, body = parse(draft.read_text(encoding="utf-8"))
    out: list[str] = []
    branch = draft.parent.name
    if branch not in BRANCHES:
        out.append(f"not in a branch folder (parent is {draft.parent.name!r})")

    for full, display in people:
        parts = full.split()
        for form in sorted(name_forms(full)):
            if _word_re(form).search(body):
                out.append(f"living person named in full: {form!r} — use {display!r}")
        if parts[-1].lower() not in shared and _word_re(parts[-1]).search(body):
            out.append(f"bare surname of a living person: {parts[-1]!r}")
        if display == "—" and _word_re(parts[0]).search(body):
            out.append(f"minor mentioned: {parts[0]!r} — do not mention minors")

    lines = [l for l in body.strip().splitlines() if l.strip()]
    last = lines[-1].strip() if lines else ""
    expected = f"{READ_PAST}{SITE_URL}{branch}/"
    if last != expected:
        out.append(f"last line must be exactly: {expected}")
    words = count_words(body)
    if not MIN_WORDS <= words <= MAX_WORDS:
        out.append(f"{words} words — need {MIN_WORDS}–{MAX_WORDS}")

    if "**" in body:
        out.append("Markdown bold '**' — WhatsApp uses single *asterisks*")
    if re.search(r"^\s*#", body, re.MULTILINE):
        out.append("Markdown heading '#' — WhatsApp has no headings")
    if re.search(r"\[[^\]]+\]\([^)]+\)", body):
        out.append("Markdown link [text](url) — write the bare URL")
    if re.search(r"^\s*source:", body, re.MULTILINE):
        out.append("a 'source:' line has leaked from an item into the body")
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        print("usage: check.py <draft.md> [--living <living-people.txt>]")
        return 2
    living = DEFAULT_LIVING
    if "--living" in argv:
        i = argv.index("--living")
        living = Path(argv[i + 1])
        del argv[i:i + 2]
    people, shared = load_living(living)
    found = problems(Path(argv[0]), people, shared)
    for p in found:
        print("PROBLEM:", p)
    if not found:
        print("clean")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_check.py -q`
Expected: `11 passed`

- [ ] **Step 6: Run the whole suite**

Run: `python -m pytest -q`
Expected: all green (frontmatter 5, wa 7, posts 4, build 7, check 11 = 34 passed).

- [ ] **Step 7: Commit**

```bash
git add site/check.py tests/test_check.py tests/fixtures/living.txt
git commit -q -m "$(cat <<'EOF'
Check a draft against the living-people rule and the post format

Bare surnames are flagged only when not in the list's shared-surnames
line, so family-line names borne by the dead do not fail every draft.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Publish the empty site

> **HELD — do not execute in this run (ruling 4).** The repository is private and its earlier history must be cleaned before it goes public and before anything is pushed. Brian decides; the steps below stay as the record of what to do afterwards.

**Files:**
- Modify: nothing in the tree; GitHub repository settings.

**Interfaces:**
- Produces: `https://sharland.github.io/family-history-updates/` live, serving `docs\` from `main`.

- [ ] **Step 1: Push everything so far**

Run: `git push`
Expected: `main -> main`.

- [ ] **Step 2: Enable GitHub Pages from main:/docs**

```bash
gh api -X POST repos/sharland/family-history-updates/pages \
  -f "source[branch]=main" -f "source[path]=/docs" 2>&1 | head -20
```

Expected: JSON containing `"html_url": "https://sharland.github.io/family-history-updates/"`. If it returns 409 (already enabled), run `gh api repos/sharland/family-history-updates/pages` and confirm `source.path` is `/docs`; if not, `gh api -X PUT repos/sharland/family-history-updates/pages -f "source[branch]=main" -f "source[path]=/docs"`.

- [ ] **Step 3: Wait for the first deploy and verify all three pages**

```bash
for i in 1 2 3 4 5 6 7 8 9 10; do
  code=$(curl -s -o /dev/null -w '%{http_code}' https://sharland.github.io/family-history-updates/sharland-crowe/)
  echo "attempt $i: $code"; [ "$code" = "200" ] && break; sleep 30
done
curl -s https://sharland.github.io/family-history-updates/ | grep -c "Ferreira and Gresty"
curl -s https://sharland.github.io/family-history-updates/ferreira-gresty/ | grep -c "No updates yet"
```

Expected: a `200` within a few minutes; the two `grep -c` lines print `1`. Do not proceed to Task 9 until the URL is live — the first post's closing link must resolve when Brian pastes it.

---

### Task 8: The private files — living-people list and style notes

**Files:**
- Create: `site/seed_living.py`, `tests/fixtures/mini.ged`
- Test: `tests/test_seed_living.py`
- Create (private, outside the repo): `D:\Dropbox\Family\family history\.claude\living-people.txt`, `D:\Dropbox\Family\family history\.claude\digest-style.md`

**Interfaces:**
- Produces: `candidates(ged_text: str, cutoff_year: int = 1926) -> list[tuple[str, str]]` — `(full name, display form)` for every INDI with no `DEAT` and a birth year > cutoff, **and** for undated people, which `render` writes as *commented-out* lines under an `# UNDATED — probably dead; uncomment any who are alive` heading so the active list holds only clear cases; anyone born in **2008 or later is treated as a minor** and gets the display form `—`; `render(candidates) -> str` — the file text with the header and a prefilled `shared-surnames:` line. CLI: `python site/seed_living.py <file.ged> <out.txt>`; **refuses to overwrite an existing `out.txt`** (writes `<out>.seed.txt` instead) — the research folder's nothing-deleted rule.

- [ ] **Step 1: Write the fixture and the failing tests**

`tests/fixtures/mini.ged`:

```
0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Alice Margaret /Penrose/
1 SEX F
1 BIRT
2 DATE 1943
0 @I2@ INDI
1 NAME Walter Noel /Penrose/
1 SEX M
1 BIRT
2 DATE 17 Dec 1917
1 DEAT
2 DATE 19 Jul 1944
0 @I3@ INDI
1 NAME John /Trewin/
1 SEX M
1 BIRT
2 DATE 1 Apr 1846
0 @I4@ INDI
1 NAME Peter /Trevithick/
1 SEX M
0 @I5@ INDI
1 NAME Tamsin Heather /Rowe/
1 SEX F
1 BIRT
2 DATE 6 Sep 2011
0 TRLR
```

```python
# tests/test_seed_living.py
from pathlib import Path
from seed_living import candidates, render, main

FIX = Path(__file__).parent / "fixtures" / "mini.ged"


def test_children_get_the_do_not_mention_marker():
    got = dict(candidates(FIX.read_text(encoding="utf-8")))
    assert got["Tamsin Heather Rowe"] == "—"


def test_render_comments_out_the_undated():
    text = render(candidates(FIX.read_text(encoding="utf-8")))
    assert "\n# UNDATED" in text
    assert "\n# Peter Trevithick | Peter T.\n" in text
    assert "\nAlice Margaret Penrose | Alice P.\n" in text


def test_candidates_are_the_undead_born_after_cutoff_or_undated():
    got = candidates(FIX.read_text(encoding="utf-8"))
    names = [full for full, _ in got]
    assert "Alice Margaret Penrose" in names      # born 1943, no death
    assert "Peter Trevithick" in names                  # no birth, no death
    assert "Tamsin Heather Rowe" in names           # born 2011
    assert "Walter Noel Penrose" not in names       # dead
    assert "John Trewin" not in names                  # born 1846


def test_display_form_is_first_name_and_surname_initial():
    got = dict(candidates(FIX.read_text(encoding="utf-8")))
    assert got["Alice Margaret Penrose"] == "Alice P."
    assert got["Peter Trevithick"] == "Peter T."


def test_render_has_header_and_shared_surnames_line():
    text = render(candidates(FIX.read_text(encoding="utf-8")))
    assert text.startswith("# Living people")
    assert "\nshared-surnames: Sharland, Crowe, Ferreira, Gresty" in text
    assert "Alice Margaret Penrose | Alice P.\n" in text


def test_main_never_overwrites(tmp_path):
    out = tmp_path / "living-people.txt"
    out.write_text("keep me\n", encoding="utf-8")
    assert main([str(FIX), str(out)]) == 0
    assert out.read_text(encoding="utf-8") == "keep me\n"
    assert (tmp_path / "living-people.seed.txt").exists()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_seed_living.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'seed_living'`

- [ ] **Step 3: Implement**

```python
# site/seed_living.py
"""One-off: seed the private living-people list from a GEDCOM export.

Everyone with no DEAT and a birth after the cutoff (or no birth at all)
is listed with a first-name-and-initial display form for Brian to
correct by hand. Never overwrites an existing list.
"""
import re
import sys
from pathlib import Path

SHARED = "Sharland, Crowe, Ferreira, Gresty, Solomon, Mattocks, Rixom, Tiran, Truscott"
HEADER = (
    "# Living people — full name | how they appear in posts. Comments start with #.\n"
    "# Display form for a minor is a single em dash: —  (meaning: do not mention at all).\n"
    "# Married women: change the initial to the CURRENT surname's initial.\n"
    f"shared-surnames: {SHARED}\n"
)


def _year(date_line: str):
    m = re.search(r"(\d{4})", date_line)
    return int(m.group(1)) if m else None


def candidates(ged_text: str, cutoff_year: int = 1926) -> list[tuple[str, str]]:
    out = []
    for rec in re.split(r"\n(?=0 @)", ged_text):
        if " INDI" not in rec.splitlines()[0]:
            continue
        name = re.search(r"^1 NAME (.+)$", rec, re.M)
        if not name:
            continue
        given, _, rest = name.group(1).partition("/")
        surname = rest.split("/")[0].strip()
        given = given.strip()
        if not given or not surname:
            continue
        if re.search(r"^1 DEAT", rec, re.M):
            continue
        birt = re.search(r"^1 BIRT\n(?:2 .*\n)*?2 DATE (.+)$", rec, re.M)
        year = _year(birt.group(1)) if birt else None
        if year is not None and year <= cutoff_year:
            continue
        full = f"{given} {surname}"
        display = f"{given.split()[0]} {surname[0]}."
        out.append((full, display))
    return out


def render(cands) -> str:
    return HEADER + "".join(f"{full} | {display}\n" for full, display in cands)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: seed_living.py <file.ged> <living-people.txt>")
        return 2
    ged, out = Path(argv[0]), Path(argv[1])
    text = render(candidates(ged.read_text(encoding="utf-8", errors="replace")))
    if out.exists():
        out = out.with_suffix(".seed.txt")
        print("target exists; wrote", out)
    out.write_text(text, encoding="utf-8", newline="\n")
    print("wrote", out, "-", text.count("\n") - 4, "people")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_seed_living.py -q`
Expected: `4 passed`

- [ ] **Step 5: Seed the real list (private) and hand it to Brian**

```bash
python site/seed_living.py "D:/Dropbox/Family/family history/Tree (ged) files/Sharland family Tree v3.ged" \
  "D:/Dropbox/Family/family history/.claude/living-people.txt"
```

Then open the file and, before showing Brian: set the display form of everyone known to be a **minor** (Brian's children and any other child) to `—`; correct the initials of **married women** you already know (e.g. `Alice Margaret Penrose | Alice P.`). Show Brian the list and ask him to mark anyone who has died and correct any married surnames; note that the file is private and never leaves the Dropbox folder.

- [ ] **Step 6: Write the style notes (private)**

`D:\Dropbox\Family\family history\.claude\digest-style.md` — copy the rules from spec §3 and §5 into working form, then add two example items in the agreed voice (one for each branch) and the list of what is *not* tellable. Keep it under a page; it is read before every assembly.

- [ ] **Step 7: Commit the script (not the private files)**

```bash
git add site/seed_living.py tests/test_seed_living.py tests/fixtures/mini.ged
git commit -q -m "$(cat <<'EOF'
Seed the private living-people list from a GEDCOM export

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: September's items and the two catch-up posts

**Files:**
- Create: eight files in `queue/items/sharland-crowe/`, four in `queue/items/ferreira-gresty/`; one post in each `queue/ready/<branch>/`.

**Interfaces:**
- Consumes: `check.py` (Task 6) and the private living list (Task 8).
- Produces: two checked drafts for Brian; the queue populated so the nudge (Task 10) has real data.

- [ ] **Step 1: Write the eight Sharland–Crowe items**

Each file has the item front matter of spec §5.1 (`date`, `weight`, `source`) and a body of two to four sentences in WhatsApp dialect, first person, living people shortened. Sources are research-folder paths and stay in the front matter. Write them **from the dossiers, not from memory** — open each source and take the facts from it.

| File | weight | source | The point of it |
|---|---|---|---|
| `2026-09-17-crowe-1911-census.md` | 2 | `Dossiers\Crowe\Richard John Southwell Crowe\Richard John Southwell Crowe - Research Dossier.md` §2 (1911 row) | The whole Crowe household found at the Royal Pier Hotel in 1911: great-great-grandfather John a consulting engineer, Laura the hotel keeper, all four children at home |
| `2026-09-17-bunny-dolly-birth-years.md` | 1 | `Tree_Task_List.md` B4 | The 1891 and 1911 censuses fix two great-great-aunts' birth years the tree had wrong: Bunny 1 July 1891; Dolly January 1890 |
| `2026-09-17-bird-wedding.md` | 3 | `Documents\Crowe family history\Crowe Family History (1977 typescript) - index and extracts.md`, "Uncle Ted Crowe" note | Bunny married Ted Crowe in 1924 — her second cousin — with his father the Rector of Cavan officiating; the family called it "The Bird Wedding"; Grandpa Crowe signed as witness |
| `2026-09-17-amberley-1881.md` | 2 | `Documents\Research notes\Mayor Mattocks.md`, 1881 section | The 1881 census at Amberley, Bournemouth: great-great-grandmother Hannah, 30, keeping house for her widowed mother Hannah Hill, 72, lodging-house keeper; William Claridge Sharland a farmer |
| `2026-09-19-chough.md` | 2 | `Documents\Family correspondence\2026-09-19 Conversation with Alice P.md` §1; `Images\20th Century\1950s\Chough christening (album page) - record.md` | "Chough", the nickname; the boat Grandad built in Rhodesia; Gran christening it in June 1958 |
| `2026-09-19-tap-and-die.md` | 2 | `Dossiers\Crowe\Richard John Southwell Crowe\2026-09-19 R J S Crowe tap and die set - record.md`; the Alice conversation §5 | Alice P. has passed on Grandpa Crowe's tap and die set; his Celtic Fields inventions — the gate switch in the road, the foot-pump taps |
| `2026-09-20-sybil-dossier.md` | 2 | `Dossiers\Rixom\Sybil Maud Rixom (Crowe)\Sybil Maud Rixom (Crowe) - Research Dossier.md` §4 | Great-granny Sybil now has a file of her own: top of all England in Pitman's shorthand and typing; ran the Royal Pier Hotel for sixteen years |
| `2026-09-20-tree-corrections.md` | 1 | `Ancestry tree corrections - September 2026.md` | A batch of corrections going into the Ancestry tree — say briefly what kind, and that a fresh export follows |

Example — `queue/items/sharland-crowe/2026-09-19-chough.md`:

```
---
date: 2026-09-19
weight: 2
source: Documents\Family correspondence\2026-09-19 Conversation with Alice P.md
---
*Grandpa Crowe's nickname was "Chough".* Alice P. told me it was because a chough is "the least objectionable bird of the crow family". In 1958 Grandad built a small sailing boat in Rhodesia and named it after him — there's a photograph in Alice's album of Gran breaking a bottle on the bow, with Dad, aged 13, standing between them.
```

- [ ] **Step 2: Write the four Ferreira–Gresty items**

| File | weight | source | The point of it |
|---|---|---|---|
| `2026-09-20-percy-dossier.md` | 3 | `Dossiers\Ferreira\Julien Percy Ferreira\Julien Percy Ferreira - Research Dossier.md` §1, §3 | Great-uncle Percy: volunteered from school in April 1917, a pilot by May 1918, joined 57 Squadron on 21 July 1918, shot down in flames near Marcoing on 16 September 1918 with his observer Leslie Simmonds; no known grave; nineteen |
| `2026-09-20-percy-service-record.md` | 2 | same dossier §5.4 | His RAF service record has turned up online, free — the family home was **Milner House**, Humansdorp; and a photograph of his name cut into the Arras memorial |
| `2026-09-17-gwendoline-truscott.md` | 2 | `Tree_Task_List.md` B1; `Dossiers\Gresty\Doreen Mercy Gresty (Ferreira)\...` §2 | The 1891 census settles that great-great-grandmother Gwendoline Truscott really was William Thomas and Ann Truscott's daughter — 142 ancestors on Nan's side confirmed in one line |
| `2026-09-20-doreen-dossier.md` | 2 | the Doreen dossier §6 | Nan now has a file of her own; how little is documented; an open ask for memories and photographs of her young |

- [ ] **Step 3: Assemble the Sharland–Crowe catch-up post**

`queue/ready/sharland-crowe/2026-09-21.md`: front matter listing the items used (choose four: the Bird Wedding, the 1911 census, the Chough, Sybil — the two weight-1 items and Amberley wait for the next post); first line `*Family history — 21 September*`; an opening sentence acknowledging the gap ("I've been busy since the summer, so a catch-up:"); the four items lightly edited to read as one message; the closing link. Aim for 200–230 words.

Run: `python site/check.py queue/ready/sharland-crowe/2026-09-21.md`
Expected: `clean`. Fix anything it reports before showing Brian.

- [ ] **Step 4: Assemble the Ferreira–Gresty catch-up post**

`queue/ready/ferreira-gresty/2026-09-21.md`: all four items (Percy's dossier and service record read as one), the same shape, 200–250 words, closing link for `ferreira-gresty`.

Run: `python site/check.py queue/ready/ferreira-gresty/2026-09-21.md`
Expected: `clean`.

- [ ] **Step 5: Commit the queue and hand over**

```bash
git add queue
git commit -q -m "$(cat <<'EOF'
Queue September's items and two catch-up drafts

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
git push
```

Then give Brian the Sharland–Crowe draft in a fenced code block, tell him the Ferreira–Gresty one is ready in the queue for a few days later, and stop. **Nothing moves to `posts\` until he says "sent".**

---

### Task 10: The nudge and the pointers

**Files:**
- Create: `C:\Users\sharl\.claude\projects\D--Dropbox-Family-family-history\memory\family-history-updates-nudge.md`
- Modify: `C:\Users\sharl\.claude\projects\D--Dropbox-Family-family-history\memory\MEMORY.md` (one index line)
- Modify: `D:\Dropbox\Family\family history\INDEX.md` (one bullet in the Conventions section), `D:\Dropbox\Family\family history\Resource Links.md` (one row)

**Interfaces:**
- Produces: the standing rule that makes the nudge happen at the start of every family-history session.

- [ ] **Step 1: Write the memory file**

```markdown
---
name: family-history-updates-nudge
description: Standing rule — at the start of every session in the family history folder, count the untold items per branch in D:\Claude-work\family-history-updates\queue\items and nudge Brian to assemble a WhatsApp post when 3+ items (or 1 item and 21+ days since that branch's last post)
metadata:
  type: feedback
---

**The rule (Brian, 20 Sep 2026):** at the start of every session in `D:\Dropbox\Family\family history`, before anything else, count the files in `D:\Claude-work\family-history-updates\queue\items\sharland-crowe\` and `...\ferreira-gresty\` (ignore `.gitkeep`) and read the newest filename in `posts\<branch>\`. For any branch with **three or more items**, or **one or more items and 21+ days** since its last post (or no post ever), tell Brian how many, since when, which branch, and offer to assemble now or at the end. Repeat at the end of a session that added items. **Write items the moment something tellable happens**, not at session end. Never assemble unasked; never move anything to `posts\` until Brian says "sent".

**Why:** the relatives who want updates (one in her eighties, WhatsApp and email only) get them only if someone remembers; a scheduler can't see this disk, so the reminder has to be me. Content-based, not weekly, so every post is worth reading.

**How to apply:** the design is `D:\Claude-work\family-history-updates\design\2026-09-20-updates-pipeline-design.md`; the working rules and the private living-people list are in `D:\Dropbox\Family\family history\.claude\` (`digest-style.md`, `living-people.txt`). Run `python site/check.py <draft>` before showing any draft. See [[family-history-edit-rules]] and [[family-history-ticket-bundling]].
```

- [ ] **Step 2: Index it**

Append to `MEMORY.md`:

```
- [Family history updates nudge](family-history-updates-nudge.md) — count queue/items per branch at session start; 3+ items or 1 item + 21 days → offer a WhatsApp post; never publish unsent
```

- [ ] **Step 3: Pointers in the research folder**

`INDEX.md`, Conventions list, add:

```
- **Updates to relatives**: short WhatsApp posts, drafted from a queue of findings in `D:\Claude-work\family-history-updates\` (outside Dropbox), checked against the private living-people list in `.claude\living-people.txt`, and published after sending at <https://sharland.github.io/family-history-updates/> — one page per side of the family. Design and rules in that repo's `design\`.
```

`Resource Links.md`, general table, add a row:

```
| Family history updates (this project's own page) | <https://sharland.github.io/family-history-updates/> | Public archive of the WhatsApp updates, two streams | All | Built from `D:\Claude-work\family-history-updates\`; only posts Brian has actually sent appear; living relatives by first name and initial |
```

- [ ] **Step 4: Run the nudge once by hand to prove it**

From a shell in the research folder:

```bash
for b in sharland-crowe ferreira-gresty; do
  n=$(ls "D:/Claude-work/family-history-updates/queue/items/$b" | grep -vc '^\.gitkeep$')
  last=$(ls "D:/Claude-work/family-history-updates/posts/$b" | grep -v '^\.gitkeep$' | sort | tail -1)
  echo "$b: $n items; last post: ${last:-none}"
done
```

Expected: `sharland-crowe: 8 items; last post: none` and `ferreira-gresty: 4 items; last post: none` — both over the trigger, which is the state Brian is being handed.

---

## Self-review against the spec

- **§2 two branches** — Tasks 1, 4, 5 (folders, `BRANCHES`, two pages). **§3 fixed decisions** — copy-paste (Task 9 stops at hand-over); trigger (Task 10 rule); length/format/link (Task 6 rules 3–5); no images/JS/email (Task 5 template and test); unsent never rendered (Task 4 + Task 5 test); used items archived (Task 10 rule text; the move is a manual step in the send flow, spec §7); nudge in memory (Task 10). **§4 layout** — Task 1; private files — Task 8. **§5 file formats** — Tasks 2, 4, 9. **§6 check rules 1–6** — Task 6, with rule 1's bare-surname refinement stated in the task and enforced by `shared-surnames:`. **§7 flow** — Task 9 (assemble/hand over) and the memory rule; the send steps are operational, not code. **§8 build/page/hosting** — Tasks 5, 7. **§9 tests** — Tasks 2–6, 8 (32 + 4 tests). **§10 first run** — Tasks 7–10 in that order. **§11 out of scope** — nothing here builds RSS, per-post pages, email or images.
- **Placeholders:** none; every code step has its code, every content step names its file, source and content.
- **Names:** `parse`, `inline`/`blocks`/`render_post`, `BRANCHES`/`Post`/`load_posts`/`long_date`, `SITE_URL`/`TITLES`/`build`/`write`, `load_living`/`problems`/`main`, `candidates`/`render`/`main` are used identically across tasks. `check.py` imports `SITE_URL` from `build`, which imports `posts` and `wa` — no cycle.
