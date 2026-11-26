"""Tests for the Pure Cambridge Edition (PCE) source loader in jesus_centric_kjv_processor.py."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import jesus_centric_kjv_processor as jk  # noqa: E402


@pytest.fixture(scope="module")
def verses():
    v, origin = jk.load_pce()
    assert Path(origin) == jk.DEFAULT_PCE_PATH  # local repo copy is preferred over the URL
    return v


@pytest.fixture(scope="module")
def ref(verses):
    return {(v["abbr"], v["chapter"], v["verse"]): v for v in verses}


def test_counts(verses):
    assert len(verses) == 31102
    assert len({v["abbr"] for v in verses}) == 66
    assert len({(v["abbr"], v["chapter"]) for v in verses}) == 1189


def test_canonical_order(verses):
    order = []
    for v in verses:
        if not order or order[-1] != v["abbr"]:
            order.append(v["abbr"])
    assert order == [b[0] for b in jk.BOOKS]
    assert verses[0]["book"] == "Genesis" and verses[-1]["book"] == "Revelation"


def test_sample_verses(ref):
    assert ref[("Ge", 1, 1)]["text"] == "In the beginning God created the heaven and the earth."
    assert ref[("Joh", 3, 16)]["text"].startswith("For God so loved the world, that he gave his only begotten Son")
    assert "Ruth" in ref[("Ru", 1, 4)]["text"]
    assert "the Father, the Word, and the Holy Ghost" in ref[("1Jo", 5, 7)]["text"]


def test_pce_spelling_and_punctuation_preserved(ref):
    # curly apostrophe kept as published (the repo file is Windows-1252; 0x92 -> U+2019)
    assert "wife\u2019s" in ref[("Ge", 3, 20)]["text"]
    assert "Beersheba" in ref[("Ge", 21, 14)]["text"]
    assert "inquire" in ref[("Ge", 25, 22)]["text"]
    assert "sin\u2014;" in ref[("Ex", 32, 32)]["text"]


def test_titles_are_metadata_not_text(ref, verses):
    ps3 = ref[("Ps", 3, 1)]
    assert ps3["titles_before"] == ["A Psalm of David, when he fled from Absalom his son."]
    assert "<<" not in ps3["text"] and ps3["text"].startswith("LORD, how are they increased")
    assert ref[("Re", 22, 21)]["titles_after"] == ["THE END."]
    assert len(jk.titles_metadata(verses)) == 132
    assert all("<<" not in v["text"] for v in verses)


def test_italics_modes(ref):
    t = ref[("Ge", 1, 2)]["text"]
    assert "[was]" in t
    assert "darkness was upon" in jk.render_text(t)
    assert "darkness [was] upon" in jk.render_text(t, "keep")
    assert "darkness <i>was</i> upon" in jk.render_text(t, "html")
    with pytest.raises(ValueError):
        jk.render_text(t, "bogus")


def test_output_lines_format(verses):
    lines = list(jk.pce_to_lines(verses))
    assert lines[0] == "GENESIS" and lines[1] == "1:1: In the beginning God created the heaven and the earth."
    assert len(lines) == 31102 + 66
    assert lines[-1].startswith("22:21: The grace of our Lord Jesus Christ be with you all. Amen.")
    assert lines[-1].endswith("Amen.")


def test_processing_pipeline(ref):
    out = jk.process_line("3:16: " + jk.render_text(ref[("Joh", 3, 16)]["text"]))
    assert out.startswith("3:16: For GOD so loved the world")
    assert "whoever believes" in out
    assert "WORD[JESUS]" in jk.process_line(jk.render_text(ref[("1Jo", 5, 7)]["text"]))


def test_decode_utf8_and_cp1252():
    assert jk.decode_pce("Ge 1:1 wife\u2019s".encode("utf-8-sig")) == "Ge 1:1 wife\u2019s"
    assert jk.decode_pce(b"Ge 1:1 wife\x92s") == "Ge 1:1 wife\u2019s"


def _mini(lines):
    return "\r\n".join(lines) + "\r\n"


def test_parser_rejects_bad_input():
    with pytest.raises(jk.PCEError, match="validation failed"):
        jk.parse_pce(_mini(["Ge 1:1 In the beginning.", "Ge 1:2 And the earth."]))
    with pytest.raises(jk.PCEError, match="duplicate"):
        jk.parse_pce(_mini(["Ge 1:1 a", "Ge 1:1 b"]))
    with pytest.raises(jk.PCEError, match="unknown book"):
        jk.parse_pce(_mini(["Xx 1:1 a"]))
    with pytest.raises(jk.PCEError, match="not a PCE verse line"):
        jk.parse_pce(_mini(["GENESIS", "1:1: a"]))
    with pytest.raises(jk.PCEError, match="out of canonical order"):
        jk.parse_pce(_mini(["Ex 1:1 a", "Ge 1:1 b"]))


def test_missing_local_file_and_bad_url(tmp_path):
    with pytest.raises(jk.PCEError, match="file not found"):
        jk.load_pce(tmp_path / "nope.txt")
    with pytest.raises(jk.PCEError, match="download failed"):
        jk.load_pce("http://127.0.0.1:9/TEXT-PCE.txt", timeout=2)


def test_cli_two_arg_pce_and_titles(tmp_path, monkeypatch):
    # Full text is parsed and validated; the slow modernization pipeline is stubbed for speed.
    monkeypatch.setattr(jk, "process_line", lambda s: s)
    out, tj = tmp_path / "out.txt", tmp_path / "titles.json"
    jk.main([str(jk.DEFAULT_PCE_PATH), str(out), "--titles-json", str(tj)])
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "GENESIS" and len(lines) == 31168
    assert len(json.loads(tj.read_text(encoding="utf-8"))) == 132


def test_cli_legacy_plain_input(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text("JOHN\r\n3:16: For God so loved the world, that whosoever believeth in him\r\n", encoding="utf-8")
    out = tmp_path / "out.txt"
    jk.main([str(src), str(out)])
    assert out.read_text(encoding="utf-8") == "JOHN\n3:16: For GOD so loved the world, that whoever believes in him\n"


def test_general_eth_rule_removed():
    # Unlisted -eth words keep their KJV form (the old general rule produced "compasss").
    # (compasseth, crieth... now have explicit entries; the generic rule must still not mangle unknown words)
    for w in ["Nazareth", "teeth", "twentieth", "zzzeth"]:
        assert jk.modernize_line(f"he {w} it") == f"he {w} it"
    assert "compasss" not in jk.process_line("2:11: that is it which compasseth the whole land")


def test_explicit_eth_mappings_kept():
    # loveth/believeth/saith are explicit REPLACEMENTS entries, separate from the removed general rule.
    assert jk.modernize_line("he that loveth") == "he that loves"
    assert jk.modernize_line("whosoever believeth") == "whoever believes"
    assert jk.modernize_line("thus saith the LORD") == "thus says the LORD"


def test_explicit_eth_verb_swaps():
    for old, new in [("endureth", "endures"), ("crieth", "cries"), ("committeth", "commits"),
                     ("compasseth", "compasses"), ("judgeth", "judges"), ("fleeth", "flees"), ("smiteth", "smites")]:
        assert jk.modernize_line(f"he {old} it") == f"he {new} it"
    # names, ordinals and teeth are not verbs and stay as they are
    for word in ["Nazareth", "teeth", "twentieth", "Japheth", "BETH."]:
        assert jk.modernize_line(f"of {word} and") == f"of {word} and"
