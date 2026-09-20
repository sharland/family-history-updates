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


class Candidate(tuple):
    """A (full name, display form) pair that also carries an .undated flag."""

    undated: bool

    def __new__(cls, full: str, display: str, undated: bool = False):
        self = super().__new__(cls, (full, display))
        self.undated = undated
        return self


def _year(date_line: str):
    m = re.search(r"(\d{4})", date_line)
    return int(m.group(1)) if m else None


def candidates(ged_text: str, cutoff_year: int = 1926) -> list[Candidate]:
    out = []
    for rec in re.split(r"\n(?=0 @)", ged_text.replace("\r\n", "\n")):
        lines = rec.splitlines()
        if not lines or " INDI" not in lines[0]:
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
        if year is not None and year >= MINOR_FROM:
            display = MINOR_MARK
        else:
            display = f"{given.split()[0]} {surname[0]}."
        out.append(Candidate(full, display, undated=year is None))
    return out


def render(cands) -> str:
    dated = [c for c in cands if not getattr(c, "undated", False)]
    undated = [c for c in cands if getattr(c, "undated", False)]
    text = HEADER + "".join(f"{full} | {display}\n" for full, display in dated)
    if undated:
        text += "\n" + UNDATED_HEADING
        text += "".join(f"# {full} | {display}\n" for full, display in undated)
    return text


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: seed_living.py <file.ged> <living-people.txt>")
        return 2
    ged, out = Path(argv[0]), Path(argv[1])
    cands = candidates(ged.read_text(encoding="utf-8", errors="replace"))
    text = render(cands)
    if out.exists():
        out = out.with_suffix(".seed.txt")
        print("target exists; wrote", out)
    out.write_text(text, encoding="utf-8", newline="\n")
    n_undated = sum(c.undated for c in cands)
    n_minor = sum(c[1] == MINOR_MARK for c in cands)
    print("wrote", out, f"- {len(cands) - n_undated} dated, {n_undated} undated (commented out), {n_minor} minors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
