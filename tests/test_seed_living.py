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
