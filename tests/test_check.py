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
    cases = [
        ("**Bold**", "Markdown bold"),
        ("# A heading", "Markdown heading"),
        ("[text](https://x.test)", "Markdown link"),
        ("source: Documents\\x.md", "'source:' line"),
    ]
    for i, (line, message) in enumerate(cases):
        result = found(tmp_path / str(i), extra=(line,))
        assert any(message in p for p in result), (line, result)


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


def living_file(tmp_path, text):
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "living.txt"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def found_with(tmp_path, living_text, **kw):
    living = load_living(living_file(tmp_path, living_text))
    return problems(write(tmp_path, draft_text(**kw)), *living)


SHARED = "shared-surnames: Sharland, Crowe\n"


def test_underscore_italics_do_not_hide_names(tmp_path):
    assert any("Alice Penrose" in p for p in found(tmp_path, opening="_Alice Penrose_ remembers it."))
    assert any("Penrose" in p and "bare" in p for p in found(tmp_path / "b", opening="_Penrose_ kept it."))


def test_surname_inside_another_surname_is_not_flagged(tmp_path):
    result = found_with(tmp_path, "Tamsin Rowe | Tamsin R.\n", opening="The Crowe family kept the hotel.")
    assert not any("Rowe" in p for p in result), result


def test_surname_first_form_fails_for_shared_surname(tmp_path):
    living = SHARED + "Alice Sharland | Alice S.\n"
    assert any("Sharland, Alice" in p for p in found_with(tmp_path, living, opening="Sharland, Alice came."))


def test_middle_initial_without_period_fails(tmp_path):
    living = SHARED + "Alice Margaret Sharland | Alice S.\n"
    assert any("Alice M Sharland" in p for p in found_with(tmp_path, living, opening="Alice M Sharland came."))


def test_minor_marker_accepts_hyphen_and_en_dash(tmp_path):
    for i, mark in enumerate(["-", "–", "—", " - "]):
        result = found_with(tmp_path / str(i), f"Tamsin Heather Rowe | {mark}\n", opening="Tamsin came too.")
        assert any("minor" in p for p in result), (mark, result)


def test_curly_apostrophe_and_accents_are_normalised(tmp_path):
    result = found_with(tmp_path, "Conor O'Brien | Conor O.\n", opening="Conor O’Brien came.")
    assert any("Conor" in p for p in result), result
    result = found_with(tmp_path / "b", SHARED + "Zoë Penrose | Zoë P.\n", opening="Zoe Penrose came.")
    assert any("Penrose" in p for p in result), result


def test_word_count_uses_original_body_after_normalisation(tmp_path):
    assert found_with(tmp_path, SHARED + "Alice Penrose | Alice P.\n", opening="Café ’quoted’ hotel.", words=150) == []


def test_empty_name_line_is_skipped(tmp_path):
    persons, _ = load_living(living_file(tmp_path, " | Nobody\nPeter Trevithick | Peter T.\n"))
    assert persons == [("Peter Trevithick", "Peter T.")]


def test_cli_fails_closed_on_missing_or_empty_list(tmp_path, capsys):
    good = write(tmp_path / "g", draft_text())
    assert main([str(good), "--living", str(tmp_path / "nope.txt")]) == 2
    assert "living-people list not found" in capsys.readouterr().out
    empty = living_file(tmp_path, "# nothing\nshared-surnames: Sharland\n")
    assert main([str(good), "--living", str(empty)]) == 2
    assert "has no people" in capsys.readouterr().out


def test_email_or_handle_fails(tmp_path):
    assert any("email address or handle" in p for p in found(tmp_path, extra=("Write to me at brian@example.com.",)))
    assert any("email address or handle" in p for p in found(tmp_path / "h", extra=("Find me @brian on it.",)))


def test_phone_number_fails(tmp_path):
    for i, num in enumerate(("+44 7700 900123", "01234 567890", "(01934) 555-0142")):
        assert any("phone number" in p for p in found(tmp_path / str(i), extra=(f"Ring {num} any time.",))), num


def test_years_and_counts_do_not_look_like_phone_numbers(tmp_path):
    extra = ("The tree now has 142 ancestors, born 16 September 1918, between 1891 and 1911.",)
    assert found(tmp_path, extra=extra) == []


def test_living_flag_without_value_is_usage_error(tmp_path, capsys):
    good = write(tmp_path, draft_text())
    assert main([str(good), "--living"]) == 2
    assert "usage" in capsys.readouterr().out
