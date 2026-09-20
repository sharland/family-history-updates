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
