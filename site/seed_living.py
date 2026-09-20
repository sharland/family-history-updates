"""One-off: seed the private living-people list from a GEDCOM export.

Everyone with no DEAT and a birth after the cutoff is listed as an active
line; everyone with no DEAT and no birth year is listed commented-out under
an UNDATED heading (probably dead). Display form is first name plus surname
initial, for Brian to correct by hand. Never overwrites an existing list.
"""
import re
import sys
from pathlib import Path

SHARED = "Sharland, Crowe, Ferreira, Gresty, Solomon, Mattocks, Rixom, Tiran, Truscott"
MINOR_FROM = 2008
MINOR_MARK = "—"
HEADER = (
    "# Living people — full name | how they appear in posts. Comments start with #.\n"
    "# Display form for a minor is a single em dash: —  (meaning: do not mention at all).\n"
    "# Married women: change the initial to the CURRENT surname's initial.\n"
    f"shared-surnames: {SHARED}\n"
)
UNDATED_HEADING = "# UNDATED — probably dead; uncomment any who are alive\n"


NONAME_HEADING = "# NO SURNAME OR GIVEN NAME IN THE TREE — review by hand\n"


class Candidate(tuple):
    """A (full name, display form) pair that also carries section flags.

    .undated: no birth year known. .nameless: the tree gives no surname or
    no given name, so it can only be listed for review by hand.
    """

    undated: bool
    nameless: bool

    def __new__(cls, full: str, display: str, undated: bool = False,
                nameless: bool = False):
        self = super().__new__(cls, (full, display))
        self.undated = undated
        self.nameless = nameless
        return self


def _year(date_line: str):
    years = re.findall(r"(?<!\d)\d{4}(?!\d)", date_line)
    return int(years[-1]) if years else None


def _birth_year(lines: list[str]):
    """Year from the first BIRT block: lines after `1 BIRT` up to the next level 0/1 line."""
    for i, line in enumerate(lines):
        if re.match(r"1 BIRT(?: |$)", line):
            for sub in lines[i + 1:]:
                if re.match(r"[01] ", sub):
                    break
                m = re.match(r"2 DATE (.+)$", sub)
                if m:
                    return _year(m.group(1))
            return None
    return None


def candidates(ged_text: str, cutoff_year: int = 1926) -> list[Candidate]:
    out = []
    for rec in re.split(r"\n(?=0 @)", ged_text.replace("\r\n", "\n")):
        lines = rec.splitlines()
        if not lines or " INDI" not in lines[0]:
            continue
        name = re.search(r"^1 NAME (.+)$", rec, re.M)
        if not name:
            continue
        raw = name.group(1).strip()
        given, _, rest = raw.partition("/")
        surname = rest.split("/")[0].strip()
        given = given.strip()
        if re.search(r"^1 DEAT", rec, re.M):
            continue
        year = _birth_year(lines)
        if year is not None and year <= cutoff_year:
            continue
        if not given or not surname:
            out.append(Candidate(raw, "?", undated=year is None, nameless=True))
            continue
        full = f"{given} {surname}"
        if year is not None and year >= MINOR_FROM:
            display = MINOR_MARK
        else:
            display = f"{given.split()[0]} {surname[0]}."
        out.append(Candidate(full, display, undated=year is None))
    return out


def render(cands) -> str:
    def flag(c, name):
        return getattr(c, name, False)

    dated = [c for c in cands if not flag(c, "undated") and not flag(c, "nameless")]
    undated = [c for c in cands if flag(c, "undated") and not flag(c, "nameless")]
    nameless = [c for c in cands if flag(c, "nameless")]
    text = HEADER + "".join(f"{full} | {display}\n" for full, display in dated)
    if undated:
        text += "\n" + UNDATED_HEADING
        text += "".join(f"# {full} | {display}\n" for full, display in undated)
    if nameless:
        text += "\n" + NONAME_HEADING
        text += "".join(f"# {full} | {display}\n" for full, display in nameless)
    return text


def _free_seed_path(out: Path) -> Path:
    path = out.with_suffix(".seed.txt")
    n = 1
    while path.exists():
        n += 1
        path = out.with_suffix(f".seed{n}.txt")
    return path


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: seed_living.py <file.ged> <living-people.txt>")
        return 2
    ged, out = Path(argv[0]), Path(argv[1])
    cands = candidates(ged.read_text(encoding="utf-8", errors="replace"))
    if not cands:
        print("WARNING: no people found - check the GEDCOM encoding")
        return 1
    text = render(cands)
    if out.exists():
        out = _free_seed_path(out)
        print("target exists; writing", out)
    while True:
        try:
            with open(out, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            break
        except FileExistsError:
            out = _free_seed_path(out)
    n_nameless = sum(c.nameless for c in cands)
    n_undated = sum(c.undated and not c.nameless for c in cands)
    n_minor = sum(c[1] == MINOR_MARK for c in cands)
    n_dated = len(cands) - n_undated - n_nameless
    print("wrote", out, f"- {n_dated} dated, {n_undated} undated (commented out), "
          f"{n_nameless} nameless (commented out), {n_minor} minors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
