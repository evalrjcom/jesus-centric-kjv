"""Tests for swaps.tsv loading and REPLACEMENTS.md generation."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import jesus_centric_kjv_processor as jk  # noqa: E402

TABLE_ROW = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \|$", re.M)


def _tsv_pairs(path=jk.DEFAULT_SWAPS_PATH):
    """Return (old, new) pairs in file order, ignoring comments and blanks."""
    pairs = []
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        old, new = [p.strip() for p in line.split("\t")]
        pairs.append((old, new))
    return pairs


def test_swaps_tsv_loads_733_entries():
    swaps = jk.load_swaps(jk.DEFAULT_SWAPS_PATH)
    assert len(swaps) == 733
    assert len(jk.REPLACEMENTS) == 733
    assert len(jk.COMPILED_REPLACEMENTS) == 733
    assert swaps == jk.REPLACEMENTS


def test_replacements_md_table_matches_swaps_tsv():
    md = jk.DEFAULT_REPLACEMENTS_MD.read_text(encoding="utf-8")
    md_pairs = TABLE_ROW.findall(md)
    tsv_pairs = _tsv_pairs()
    assert len(md_pairs) == len(tsv_pairs) == 733
    assert dict(md_pairs) == dict(tsv_pairs)
    # The generated table is the TSV pairs sorted case-insensitively by source word
    assert md_pairs == sorted(tsv_pairs, key=lambda kv: kv[0].lower())
    # Hand-written context-rule prose is preserved when the markdown is regenerated
    assert "## Context rule: `art`" in md
    assert md[md.index("## Context rule: `art`"):] == jk.ART_RULE_MD


def test_load_swaps_rejects_bad_lines(tmp_path):
    def write(name, body):
        p = tmp_path / name
        p.write_text(body, encoding="utf-8")
        return p

    p = write("three.tsv", "old\tnew\textra\n")
    with pytest.raises(jk.SwapsError, match=r"three\.tsv:1:.*exactly 2 fields"):
        jk.load_swaps(p)

    p = write("one.tsv", "onlyold\n")
    with pytest.raises(jk.SwapsError, match=r"one\.tsv:1:.*exactly 2 fields"):
        jk.load_swaps(p)

    p = write("empty.tsv", "old\t\n")
    with pytest.raises(jk.SwapsError, match=r"empty\.tsv:1:.*empty field"):
        jk.load_swaps(p)

    p = write("dups.tsv", "# comment\nfoo\tbar\nfoo\tbaz\n")
    with pytest.raises(jk.SwapsError, match=r"dups\.tsv:3:.*duplicate swap key 'foo'"):
        jk.load_swaps(p)

    missing = tmp_path / "nope.tsv"
    with pytest.raises(jk.SwapsError, match="file not found"):
        jk.load_swaps(missing)

    p = write("blank.tsv", "# only comments\n\n")
    with pytest.raises(jk.SwapsError, match="no swap entries found"):
        jk.load_swaps(p)


def test_load_swaps_strips_crlf_and_allows_comments(tmp_path):
    p = tmp_path / "mini.tsv"
    p.write_bytes(b"# header\r\n\r\nhath\thas\r\nunto\tto\r\n")
    assert jk.load_swaps(p) == {"hath": "has", "unto": "to"}


def test_write_replacements_md_and_swaps_flag(tmp_path):
    src = tmp_path / "swaps.tsv"
    src.write_text("# test\nunto\tto\nwhosoever\twhoever\n", encoding="utf-8")
    md = tmp_path / "REPLACEMENTS.md"
    try:
        jk.main(["--swaps", str(src), "--write-replacements-md", str(md)])
        text = md.read_text(encoding="utf-8")
        assert "Total: **2**" in text
        assert TABLE_ROW.findall(text) == [("unto", "to"), ("whosoever", "whoever")]
        assert text.endswith(jk.ART_RULE_MD)
    finally:
        # restore process-wide defaults so later tests still see the real swaps
        jk.apply_swaps(jk.load_swaps(jk.DEFAULT_SWAPS_PATH))
