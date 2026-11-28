"""Tests for the divine-pronoun stage: he/him of GOD or JESUS -> He[JESUS] / Him[JESUS]."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import divine_pronouns as dp  # noqa: E402
import jesus_centric_kjv_processor as jk  # noqa: E402

BOOKS = ("Ge", "Ps", "Isa", "Mt", "Joh", "Heb")


@pytest.fixture(scope="module")
def run():
    """Process a few whole books like the real pipeline (common words come from the whole Bible)."""
    verses, _ = jk.load_pce()
    common = dp.common_words(jk.render_text(v["text"]) for v in verses)
    items = []
    for v in verses:
        if v["abbr"] not in BOOKS:
            continue
        ref = f"{v['abbr']} {v['chapter']}:{v['verse']}"
        line = jk.process_line(f"{v['chapter']}:{v['verse']}: {jk.render_text(v['text'])}", ref)
        items.append((ref, v["abbr"], line.partition(": ")[2], jk.render_text(v["text"])))
    overrides = [o for o in jk.PRONOUN_OVERRIDES if o["ref"].split()[0] in BOOKS]
    texts, decisions = jk.mark_divine_pronouns(items, overrides=overrides, common=common)
    by_ref = {ref: t for (ref, _, _, _), t in zip(items, texts)}
    return by_ref, decisions


def test_genesis_1_27_god_marked_man_not(run):
    t, _ = run
    assert "in the image of GOD created He[JESUS] him; male and female created He[JESUS] them." in t["Ge 1:27"]


def test_john_1_3_by_him(run):
    t, _ = run
    assert t["Joh 1:3"].startswith("All things were made by Him[JESUS]; and without Him[JESUS] was not")


def test_psalm_23_shepherd(run):
    t, _ = run
    assert t["Ps 23:2"].startswith("He[JESUS] makes me to lie down")
    assert "he[JESUS]" not in t["Ps 23:2"]


def test_spirit_of_truth_apposition(run):
    t, _ = run
    assert t["Joh 16:13"].startswith("However when He[JESUS], the Spirit of truth, is come, He[JESUS] will guide")


def test_humans_stay_lowercase(run):
    t, _ = run
    assert t["Ge 4:8"].endswith("rose up against Abel his brother, and slew him.")
    assert "lest any finding him should kill him." in t["Ge 4:15"]
    assert t["Mt 8:4"].startswith("And JESUS says to him, See")         # him = the leper
    assert "[JESUS]" not in t["Ge 4:17"]                                 # Cain built a city


def test_jesus_in_the_gospels(run):
    t, _ = run
    assert "JESUS stretched forth his hand, and caught him" in t["Mt 14:31"]   # him = Peter
    assert t["Joh 8:20"].startswith("These words spoke JESUS in the treasury, as He[JESUS] taught")


def test_overrides_applied(run):
    t, _ = run
    assert "then would he not afterward" in t["Heb 4:8"]                # JESUS = Joshua here
    assert t["Isa 53:5"].startswith("But He[JESUS] was wounded for our transgressions")


def test_no_double_or_lowercase_markers(run):
    t, _ = run
    for ref, text in t.items():
        assert "[JESUS][JESUS]" not in text, ref
        assert "he[JESUS]" not in text and "him[JESUS]" not in text, ref


def test_swaps_still_apply(run):
    t, _ = run
    assert "for He[JESUS] has done marvellous things" in t["Ps 98:1"]


def test_resolver_capitalizes_existing_type_marker():
    r = dp.Resolver(set())
    new, ds = r.verse("1Ch 17:14", "1Ch", "But I will settle him[JESUS] in my house", False)
    assert new == "But I will settle Him[JESUS] in my house"
    assert ds[0]["already"] and ds[0]["status"] == "include"


def test_decisions_have_referent_and_confidence(run):
    _, ds = run
    changed = [d for d in ds if d["status"] == "include" and not d["already"]]
    assert changed and all(d["confidence"] in ("high", "medium") for d in changed)
    assert {d["referent"] for d in changed} >= {"God", "Jesus", "Holy Spirit"}


def test_default_overrides_load():
    entries = dp.load_overrides(jk.DEFAULT_PRONOUNS_PATH, jk.BOOK_INDEX)
    assert entries == jk.PRONOUN_OVERRIDES and entries
    assert {e["action"] for e in entries} <= {"include", "exclude"}


@pytest.mark.parametrize("row, msg", [
    ("Ps 23:2\tshe\t1\tinclude", "word must be"),
    ("Ps 23:2\the\tx\tinclude", "occurrence must be a number"),
    ("Ps 23:2\the\t1\tmaybe", "action must be"),
    ("Xx 1:1\the\t1\tinclude", "bad ref"),
    ("Ps 23:2\the\t1", "expected 4 or 5"),
])
def test_bad_override_rows(tmp_path, row, msg):
    p = tmp_path / "o.tsv"
    p.write_text("# c\n" + row + "\n", encoding="utf-8")
    with pytest.raises(dp.OverridesError, match=msg):
        dp.load_overrides(p, jk.BOOK_INDEX)


def test_unmatched_override_fails():
    items = [("Ps 23:1", "Ps", "The LORD is my shepherd; I shall not want.", None)]
    bad = [{"ref": "Ps 23:1", "word": "he", "occurrence": 1, "action": "include", "note": "", "line": 3}]
    with pytest.raises(dp.OverridesError, match="no matching he/him"):
        jk.mark_divine_pronouns(items, overrides=bad)


def test_review_files(tmp_path, run):
    _, ds = run
    md, csv = dp.write_review(ds, tmp_path / "rev", [b[0] for b in jk.BOOKS])
    assert "## By referent" in md.read_text(encoding="utf-8")
    assert csv.read_text(encoding="utf-8").startswith("ref,word,occurrence,status")
