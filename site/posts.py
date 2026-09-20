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
