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
