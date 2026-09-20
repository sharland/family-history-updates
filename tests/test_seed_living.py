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


def _ged(*people):
    """Build a tiny GEDCOM from lists of lines (one list per INDI)."""
    out = ["0 HEAD", "1 CHAR UTF-8"]
    for i, lines in enumerate(people, 1):
        out.append(f"0 @I{i}@ INDI")
        out.extend(lines)
    out.append("0 TRLR")
    return "\n".join(out) + "\n"


def test_nameless_parts_go_in_a_third_commented_section():
    text = render(candidates(_ged(
        ["1 NAME Alice", "1 SEX F"],
        ["1 NAME Bertram //", "1 SEX M"],
        ["1 NAME /Rowe/", "1 SEX F"],
        ["1 NAME Peter /Trevithick/"],
        ["1 NAME Ghost", "1 DEAT"],
    )))
    head = "# NO SURNAME OR GIVEN NAME IN THE TREE — review by hand\n"
    assert "\n" + head in text
    assert text.index("\n# UNDATED") < text.index(head)
    tail = text.split(head)[1]
    assert "# Alice | ?\n" in tail
    assert "# Bertram // | ?\n" in tail
    assert "# /Rowe/ | ?\n" in tail
    assert "Ghost" not in text
    assert "\nAlice |" not in text and "\nBertram" not in text


def test_birt_block_with_deep_sublines_still_gives_the_date():
    got = candidates(_ged(
        ["1 NAME Alice /Penrose/", "1 BIRT", "2 PLAC Truro", "3 MAP",
         "4 LATI N50", "2 DATE 1980"],
        ["1 NAME Peter /Trevithick/", "1 BIRT Y"],
    ))
    flags = {full: c.undated for c in got for full in [c[0]]}
    assert flags == {"Alice Penrose": False, "Peter Trevithick": True}


def test_birt_date_not_taken_from_a_later_event():
    got = candidates(_ged(
        ["1 NAME Alice /Penrose/", "1 BIRT", "2 PLAC Truro",
         "1 RESI", "2 DATE 1900"],
    ))
    assert got[0].undated is True


def test_year_ranges_use_the_last_year():
    got = dict(candidates(_ged(
        ["1 NAME Alice /Penrose/", "1 BIRT", "2 DATE BET 1920 AND 1930"],
        ["1 NAME Tamsin /Rowe/", "1 BIRT", "2 DATE BET 2005 AND 2010"],
        ["1 NAME Peter /Trevithick/", "1 BIRT", "2 DATE Abt 1930"],
    )))
    assert got == {"Alice Penrose": "Alice P.", "Tamsin Rowe": "—",
                   "Peter Trevithick": "Peter T."}


def test_minor_boundary_is_2008():
    got = dict(candidates(_ged(
        ["1 NAME Tamsin /Rowe/", "1 BIRT", "2 DATE 1 Jan 2008"],
        ["1 NAME Alice /Penrose/", "1 BIRT", "2 DATE 31 Dec 2007"],
    )))
    assert got["Tamsin Rowe"] == "—"
    assert got["Alice Penrose"] == "Alice P."


def test_main_never_overwrites_the_seed_file_either(tmp_path):
    out = tmp_path / "living-people.txt"
    out.write_text("keep me\n", encoding="utf-8")
    (tmp_path / "living-people.seed.txt").write_text("keep too\n", encoding="utf-8")
    assert main([str(FIX), str(out)]) == 0
    assert out.read_text(encoding="utf-8") == "keep me\n"
    assert (tmp_path / "living-people.seed.txt").read_text(encoding="utf-8") == "keep too\n"
    assert "Alice" in (tmp_path / "living-people.seed2.txt").read_text(encoding="utf-8")
    assert main([str(FIX), str(out)]) == 0
    assert (tmp_path / "living-people.seed3.txt").exists()


def test_main_warns_and_writes_nothing_when_no_people(tmp_path, capsys):
    bad = tmp_path / "bad.ged"
    bad.write_bytes("0 HEAD\n1 CHAR UTF-8\n0 TRLR\n".encode("utf-16"))
    out = tmp_path / "living-people.txt"
    assert main([str(bad), str(out)]) == 1
    assert "WARNING: no people found - check the GEDCOM encoding" in capsys.readouterr().out
    assert list(tmp_path.glob("living-people*")) == []


def test_crlf_gives_the_same_candidates():
    lf = FIX.read_text(encoding="utf-8")
    crlf = lf.replace("\n", "\r\n")
    assert [(tuple(c), c.undated) for c in candidates(crlf)] == \
           [(tuple(c), c.undated) for c in candidates(lf)]
