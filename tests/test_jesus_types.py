"""Tests for jesus_types.tsv: per-verse [JESUS] markers and JESUS_TYPES.md generation."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import jesus_centric_kjv_processor as jk  # noqa: E402

TABLE_ROW = re.compile(r"^\| (.+?) \| (\d+:\d+) \| `(.+?)` \| (\d+) \| (\w+) \| .* \|$", re.M)


@pytest.fixture(scope="module")
def verse_text():
    verses, _ = jk.load_pce()
    by_ref = {f"{v['abbr']} {v['chapter']}:{v['verse']}": v for v in verses}
    return lambda ref: f"{by_ref[ref]['chapter']}:{by_ref[ref]['verse']}: " + jk.render_text(by_ref[ref]["text"])


def _base(line):
    """The verse after every rule except jesus_types.tsv."""
    return jk.process_line(line)


def test_types_load_and_cover_all_66_books():
    entries = jk.load_types(jk.DEFAULT_TYPES_PATH)
    assert entries == jk.TYPES and len(entries) == 69
    assert {e["abbr"] for e in entries} == {b[0] for b in jk.BOOKS}


@pytest.mark.parametrize("entry", jk.TYPES, ids=lambda e: f"{e['ref']}:{e['target']}")
def test_target_found_and_marked_exactly_once(entry, verse_text):
    line = verse_text(entry["ref"])
    base = _base(line)
    full = jk.process_line(line, entry["ref"])
    text = full.partition(": ")[2]
    base_text = base.partition(": ")[2]
    pattern = re.compile(r"(?<!\w)" + re.escape(entry["target"]) + r"(?!\w)", re.I)
    matches = list(pattern.finditer(text))
    assert len(matches) >= entry["occurrence"], "target not found in its verse"
    end = matches[entry["occurrence"] - 1].end()
    assert text.startswith("[JESUS]", end), "marker must follow the target"
    # markers added by this entry: exactly one, unless the general rules had already marked the word
    added = text.count("[JESUS]") - base_text.count("[JESUS]")
    already = base_text.startswith("[JESUS]", end) if len(base_text) > end else False
    assert added == (0 if already else 1)
    # an applied entry never doubles up a marker
    assert "[JESUS][JESUS]" not in text


def test_genesis_3_15_example(verse_text):
    out = jk.process_line(verse_text("Ge 3:15"), "Ge 3:15")
    assert out == ("3:15: And I will put enmity between you and the woman, and between your seed "
                   "and her seed[JESUS]; it shall bruise your head, and you shall bruise his heel.")
    assert "seed[JESUS]" not in _base(verse_text("Ge 3:15")).replace("her seed[JESUS]", "")


def test_marker_only_in_listed_verses(verse_text):
    # the same words elsewhere are untouched: Ge 3:15 is listed, Ge 22:18 ("your seed") is not
    line = "22:18: And in your seed shall all the nations of the earth be blessed;"
    assert jk.process_line(line, "Ge 22:18") == line
    # without a ref (legacy files) the types file is not applied
    assert "[JESUS]" not in jk.process_line("3:15: and between your seed and her seed;")


def test_already_marked_entry_adds_nothing():
    line = "1:1: In the beginning was the Word."
    entry = {"ref": "Joh 1:1", "target": "Word", "occurrence": 1}
    base = jk.process_line(line)
    assert base.endswith("WORD[JESUS].")
    assert jk.apply_type_marker(base.partition(": ")[2], entry)[1] == "already"
    assert jk.process_line(line, "Joh 1:1") == base


def test_missing_target_is_an_error():
    with pytest.raises(jk.TypesError, match="not found"):
        jk.apply_type_marker("In the beginning GOD created.", {"ref": "Ge 1:1", "target": "seed", "occurrence": 1})
    with pytest.raises(jk.TypesError, match="occurrence #2"):
        jk.apply_type_marker("her seed", {"ref": "Ge 3:15", "target": "seed", "occurrence": 2})


@pytest.mark.parametrize("row, msg", [
    ("Ge 3:15\tseed\t1\tstrong", "5 tab-separated"),
    ("Xx 3:15\tseed\t1\tstrong\tt", "bad ref"),
    ("Ge 3:15\t\t1\tstrong\tt", "empty target"),
    ("Ge 3:15\tseed\tx\tstrong\tt", "occurrence"),
    ("Ge 3:15\tseed\t0\tstrong\tt", "occurrence"),
    ("Ge 3:15\tseed\t1\tgreat\tt", "match must be"),
])
def test_load_types_rejects_bad_rows(tmp_path, row, msg):
    p = tmp_path / "t.tsv"
    p.write_text(row + "\n", encoding="utf-8")
    with pytest.raises(jk.TypesError, match=msg):
        jk.load_types(p)


def test_load_types_duplicate_and_blank_occurrence(tmp_path):
    p = tmp_path / "t.tsv"
    p.write_text("# c\n\nGe 3:15\tseed\t\tstrong\tt\n", encoding="utf-8")
    assert jk.load_types(p)[0]["occurrence"] == 1
    p.write_text("Ge 3:15\tseed\t1\tstrong\tt\nGe 3:15\tSeed\t1\tweak\tt\n", encoding="utf-8")
    with pytest.raises(jk.TypesError, match="duplicate"):
        jk.load_types(p)


def test_jesus_types_md_matches_tsv():
    md = jk.DEFAULT_TYPES_MD.read_text(encoding="utf-8")
    rows = TABLE_ROW.findall(md)
    assert len(rows) == len(jk.TYPES)
    assert sorted((r[1], r[2], r[3], r[4]) for r in rows) == sorted(
        (f"{e['chapter']}:{e['verse']}", e["target"], str(e["occurrence"]), e["match"]) for e in jk.TYPES)
    assert f"Total: **{len(jk.TYPES)}**" in md


def test_write_types_md_roundtrip(tmp_path):
    out = jk.write_types_md(jk.TYPES, tmp_path / "T.md")
    assert out.read_text(encoding="utf-8") == jk.DEFAULT_TYPES_MD.read_text(encoding="utf-8")


@pytest.mark.parametrize("text, expected", [
    ("the man Christ Jesus;", "the man CHRIST JESUS;"),
    ("the man CHRIST JESUS;", "the man CHRIST JESUS;"),
    ("in christ  jesus our Lord", "in CHRIST JESUS our LORD"),
    ("our Lord Jesus Christ, the Son", "our LORD JESUS CHRIST, the Son"),
    ("Christ is risen; Christ Jesus came", "CHRIST[JESUS] is risen; CHRIST JESUS came"),
    ("Jesus, the Christ", "JESUS, the CHRIST[JESUS]"),
])
def test_christ_jesus_is_protected_like_jesus_christ(text, expected):
    # Pipeline order: swaps, divine caps, uppercase_jesus, then add_jesus_marker
    assert jk.process_line("1:1: " + text) == "1:1: " + expected


def test_1ti_2_5_marks_the_mediator_not_christ_jesus(verse_text):
    out = jk.process_line(verse_text("1Ti 2:5"), "1Ti 2:5")
    assert out == "2:5: For there is one GOD, and one mediator[JESUS] between GOD and men, the man CHRIST JESUS;"


def test_no_christ_jesus_marker_anywhere_in_processed_text():
    verses, _ = jk.load_pce()
    for v in verses:
        if re.search(r"christ\s+jesus", v["text"], re.I):
            ref = f"{v['abbr']} {v['chapter']}:{v['verse']}"
            out = jk.process_line(f"{v['chapter']}:{v['verse']}: " + jk.render_text(v["text"]), ref)
            assert "CHRIST[JESUS] JESUS" not in out, ref
