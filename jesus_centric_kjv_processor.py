#!/usr/bin/env python3
"""Jesus-centric KJV processor. See README for rules.

Processes the public-domain King James Version: modernizes archaic forms, capitalizes LORD/GOD,
uppercases JESUS, and adds [JESUS] markers.

Canonical source text: the Pure Cambridge Edition (PCE) of the KJV from https://www.bibleprotector.com,
stored in this repo as docs/TEXT-PCE.txt (one verse per line: "Abbrev C:V text").
"""
import argparse, json, re, sys
import urllib.error, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import divine_pronouns as dp  # noqa: E402

# ---------------------------------------------------------------------------
# Pure Cambridge Edition (PCE) source
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_PCE_PATH = REPO_ROOT / "docs" / "TEXT-PCE.txt"
PCE_RAW_URL = "https://raw.githubusercontent.com/evalrjcom/jesus-centric-kjv/main/docs/TEXT-PCE.txt"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "jesus_centric_kjv_all66.txt"
DEFAULT_SWAPS_PATH = REPO_ROOT / "swaps.tsv"
DEFAULT_REPLACEMENTS_MD = REPO_ROOT / "REPLACEMENTS.md"
DEFAULT_TYPES_PATH = REPO_ROOT / "jesus_types.tsv"
DEFAULT_TYPES_MD = REPO_ROOT / "JESUS_TYPES.md"
DEFAULT_PRONOUNS_PATH = REPO_ROOT / "divine_pronouns.tsv"

# Canonical 66-book order: (PCE abbreviation, full name, output header).
# Output headers match the book headers the viewer (docs/index.html) has always used.
BOOKS = [
    ("Ge", "Genesis", "GENESIS"), ("Ex", "Exodus", "EXODUS"), ("Le", "Leviticus", "LEVITICUS"),
    ("Nu", "Numbers", "NUMBERS"), ("De", "Deuteronomy", "DEUTERONOMY"), ("Jos", "Joshua", "JOSHUA"),
    ("Jg", "Judges", "JUDGES"), ("Ru", "Ruth", "RUTH"), ("1Sa", "1 Samuel", "FIRST SAMUEL"),
    ("2Sa", "2 Samuel", "SECOND SAMUEL"), ("1Ki", "1 Kings", "1 KINGS"), ("2Ki", "2 Kings", "2 KINGS"),
    ("1Ch", "1 Chronicles", "1 CHRONICLES"), ("2Ch", "2 Chronicles", "2 CHRONICLES"),
    ("Ezr", "Ezra", "EZRA"), ("Ne", "Nehemiah", "NEHEMIAH"), ("Es", "Esther", "ESTHER"),
    ("Job", "Job", "JOB"), ("Ps", "Psalms", "PSALMS"), ("Pr", "Proverbs", "PROVERBS"),
    ("Ec", "Ecclesiastes", "ECCLESIASTES"), ("Song", "Song of Solomon", "THE SONG OF SOLOMON"),
    ("Isa", "Isaiah", "ISAIAH"), ("Jer", "Jeremiah", "JEREMIAH"), ("La", "Lamentations", "LAMENTATIONS"),
    ("Eze", "Ezekiel", "EZEKIEL"), ("Da", "Daniel", "DANIEL"), ("Ho", "Hosea", "HOSEA"),
    ("Joe", "Joel", "JOEL"), ("Am", "Amos", "AMOS"), ("Ob", "Obadiah", "OBADIAH"),
    ("Jon", "Jonah", "JONAH"), ("Mic", "Micah", "MICAH"), ("Na", "Nahum", "NAHUM"),
    ("Hab", "Habakkuk", "HABAKKUK"), ("Zep", "Zephaniah", "ZEPHANIAH"), ("Hag", "Haggai", "HAGGAI"),
    ("Zec", "Zechariah", "ZECHARIAH"), ("Mal", "Malachi", "MALACHI"), ("Mt", "Matthew", "MATTHEW"),
    ("Mr", "Mark", "MARK"), ("Lu", "Luke", "LUKE"), ("Joh", "John", "JOHN"), ("Ac", "Acts", "ACTS"),
    ("Ro", "Romans", "ROMANS"), ("1Co", "1 Corinthians", "1 CORINTHIANS"),
    ("2Co", "2 Corinthians", "2 CORINTHIANS"), ("Ga", "Galatians", "GALATIANS"),
    ("Eph", "Ephesians", "EPHESIANS"), ("Php", "Philippians", "PHILIPPIANS"),
    ("Col", "Colossians", "COLOSSIANS"), ("1Th", "1 Thessalonians", "1 THESSALONIANS"),
    ("2Th", "2 Thessalonians", "2 THESSALONIANS"), ("1Ti", "1 Timothy", "1 TIMOTHY"),
    ("2Ti", "2 Timothy", "2 TIMOTHY"), ("Tit", "Titus", "TITUS"), ("Phm", "Philemon", "PHILEMON"),
    ("Heb", "Hebrews", "HEBREWS"), ("Jas", "James", "JAMES"), ("1Pe", "1 Peter", "1 PETER"),
    ("2Pe", "2 Peter", "2 PETER"), ("1Jo", "1 John", "1 JOHN"), ("2Jo", "2 John", "2 JOHN"),
    ("3Jo", "3 John", "3 JOHN"), ("Jude", "Jude", "JUDE"), ("Re", "Revelation", "REVELATION"),
]
BOOK_INDEX = {abbr: i for i, (abbr, _, _) in enumerate(BOOKS)}
EXPECTED_BOOKS, EXPECTED_CHAPTERS, EXPECTED_VERSES = 66, 1189, 31102

PCE_LINE = re.compile(r"^(\S+) (\d+):(\d+) (.*)$")
TITLE = re.compile(r"<<(.*?)>>")          # Psalm titles and epistle subscriptions/colophons
ITALIC = re.compile(r"\[([^\[\]]*)\]")    # words supplied by the translators (printed in italics)


class PCEError(ValueError):
    """Raised when the PCE source cannot be loaded or fails validation."""


class SwapsError(ValueError):
    """Raised when a swaps TSV cannot be loaded or fails validation."""


class TypesError(ValueError):
    """Raised when jesus_types.tsv cannot be loaded, or a target is not found in its verse."""


def decode_pce(data: bytes) -> str:
    """Decode PCE bytes. The bibleprotector.com file is Windows-1252; a UTF-8 copy is also accepted."""
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252")  # strict: undefined bytes raise instead of being replaced


def parse_pce(text: str) -> list:
    """Parse PCE text into a list of verse dicts in canonical order and validate it.

    Each verse: {"abbr", "book", "header", "chapter", "verse", "raw", "text", "titles_before", "titles_after"}
    - raw: the PCE line text exactly as published (with [italics] and <<titles>>)
    - text: raw minus <<titles>> (italic brackets still present; see render_text)
    """
    verses, seen = [], set()
    last = (-1, 0, 0)
    for n, line in enumerate(text.splitlines(), 1):  # handles CRLF / LF
        if not line.strip():
            continue
        m = PCE_LINE.match(line.rstrip())
        if not m:
            raise PCEError(f"line {n}: not a PCE verse line: {line[:60]!r}")
        abbr, ch, vs, body = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        if abbr not in BOOK_INDEX:
            raise PCEError(f"line {n}: unknown book abbreviation {abbr!r}")
        key = (BOOK_INDEX[abbr], ch, vs)
        if key in seen:
            raise PCEError(f"line {n}: duplicate verse {abbr} {ch}:{vs}")
        if key < last:
            raise PCEError(f"line {n}: verse {abbr} {ch}:{vs} is out of canonical order")
        seen.add(key); last = key
        before, after = [], []
        stripped = body
        lead = re.match(r"^\s*<<(.*?)>>\s*", stripped)
        if lead:
            before.append(lead.group(1)); stripped = stripped[lead.end():]
        trail = re.search(r"\s*<<(.*?)>>\s*$", stripped)
        if trail:
            after.append(trail.group(1)); stripped = stripped[:trail.start()]
        if "<<" in stripped or ">>" in stripped:
            raise PCEError(f"line {n}: unexpected title marker inside {abbr} {ch}:{vs}")
        _, name, header = BOOKS[BOOK_INDEX[abbr]]
        verses.append({"abbr": abbr, "book": name, "header": header, "chapter": ch, "verse": vs,
                       "raw": body, "text": stripped.strip(), "titles_before": before, "titles_after": after})
    validate(verses)
    return verses


def validate(verses: list) -> None:
    books = {v["abbr"] for v in verses}
    chapters = {(v["abbr"], v["chapter"]) for v in verses}
    counts = (len(books), len(chapters), len(verses))
    expected = (EXPECTED_BOOKS, EXPECTED_CHAPTERS, EXPECTED_VERSES)
    if counts != expected:
        raise PCEError("PCE validation failed: got %d books / %d chapters / %d verses, expected %d / %d / %d"
                       % (counts + expected))
    for v in verses:
        if not v["text"]:
            raise PCEError(f"empty verse text at {v['abbr']} {v['chapter']}:{v['verse']}")


def load_pce(source=None, timeout: float = 30.0):
    """Load and validate the PCE text. Returns (verses, origin).

    source: a local path or http(s) URL. Default: docs/TEXT-PCE.txt next to this script, falling
    back to PCE_RAW_URL when the local file is missing.
    """
    candidates = [str(source)] if source else [str(DEFAULT_PCE_PATH), PCE_RAW_URL]
    errors = []
    for cand in candidates:
        if re.match(r"^https?://", cand):
            try:
                with urllib.request.urlopen(cand, timeout=timeout) as r:
                    data = r.read()
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                errors.append(f"{cand}: download failed ({e})")
                continue
        else:
            p = Path(cand)
            if not p.is_file():
                errors.append(f"{p}: file not found")
                continue
            data = p.read_bytes()
        return parse_pce(decode_pce(data)), cand
    raise PCEError("could not load the PCE source text:\n  " + "\n  ".join(errors))


def render_text(text: str, italics: str = "strip") -> str:
    """Render PCE verse text. italics: 'strip' (default, drop [ ] but keep the words),
    'keep' (leave PCE [ ] brackets), or 'html' (<i>…</i>, which the GitHub Pages viewer renders)."""
    if italics == "strip":
        text = ITALIC.sub(r"\1", text)
    elif italics == "html":
        text = ITALIC.sub(r"<i>\1</i>", text)
    elif italics != "keep":
        raise ValueError(f"unknown italics mode {italics!r}")
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def pce_to_lines(verses: list, italics: str = "strip"):
    """Yield the viewer's plain format: a book header line, then 'C:V: text' lines."""
    current = None
    for v in verses:
        if v["abbr"] != current:
            current = v["abbr"]
            yield v["header"]
        yield f"{v['chapter']}:{v['verse']}: {render_text(v['text'], italics)}"


def titles_metadata(verses: list) -> list:
    return [{"book": v["book"], "abbr": v["abbr"], "chapter": v["chapter"], "verse": v["verse"],
             "position": pos, "text": t}
            for v in verses for pos, key in (("before", "titles_before"), ("after", "titles_after"))
            for t in v[key]]


# Restored: this pattern was dropped in ab264e7, which made every CI run fail with NameError.
LORD_GOD_PATTERN = re.compile(r"\b(Lord|LORD|God|GOD)\b")

# Word/phrase replacements are loaded from swaps.tsv (see load_swaps).
# Longer phrases are applied first when the list is compiled below.

def load_swaps(path) -> dict:
    """Parse a TSV of old<TAB>new pairs. Comments (#) and blank lines are ignored.

    path is read as UTF-8 (a leading BOM is accepted); CR/LF endings are both fine.
    Raises SwapsError with a line number for a bad row or a duplicate key.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise SwapsError(f"{path}: file not found") from None
    except UnicodeDecodeError as e:
        raise SwapsError(f"{path}: not valid UTF-8 ({e})") from e
    replacements = {}
    for n, line in enumerate(raw.splitlines(), 1):  # splitlines strips the CR in CRLF
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = [part.strip() for part in line.split("\t")]
        if len(fields) != 2:
            raise SwapsError(
                f"{path}:{n}: expected exactly 2 fields (old<TAB>new), "
                f"got {len(fields)}: {line[:80]!r}"
            )
        old, new = fields
        if not old or not new:
            raise SwapsError(f"{path}:{n}: empty field in old<TAB>new: {line[:80]!r}")
        if old in replacements:
            raise SwapsError(
                f"{path}:{n}: duplicate swap key {old!r} "
                f"(already mapped to {replacements[old]!r})"
            )
        replacements[old] = new
    if not replacements:
        raise SwapsError(f"{path}: no swap entries found")
    return replacements


def compile_replacements(mapping: dict):
    """Precompile replacement patterns, longest source phrase first."""
    sorted_items = sorted(mapping.items(), key=lambda x: -len(x[0]))
    return sorted_items, [(make_pattern(old), new) for old, new in sorted_items]


def apply_swaps(mapping: dict) -> None:
    """Install a swaps mapping as the process-wide REPLACEMENTS / COMPILED_REPLACEMENTS."""
    global REPLACEMENTS, SORTED_REPLACEMENTS, COMPILED_REPLACEMENTS
    REPLACEMENTS = mapping
    SORTED_REPLACEMENTS, COMPILED_REPLACEMENTS = compile_replacements(mapping)


# Boundary that treats punctuation as non-word
def make_pattern(word):
    return re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.I)


# Load defaults at import so tests and callers can use modernize_line immediately.
# --swaps in main() can point at a different file and call apply_swaps again.
REPLACEMENTS = load_swaps(DEFAULT_SWAPS_PATH)
# Sort by length descending so phrases win over single words.
# Compiled once: with 700+ entries, compiling per line overflowed Python's regex cache (512)
# and made a full run take many minutes.
SORTED_REPLACEMENTS, COMPILED_REPLACEMENTS = compile_replacements(REPLACEMENTS)


# ---------------------------------------------------------------------------
# Jesus-type markers (jesus_types.tsv): [JESUS] after a chosen word in a chosen verse
# ---------------------------------------------------------------------------
JESUS_MARK = "[JESUS]"
TYPE_MATCH_LEVELS = ("strong", "moderate", "weak")
REF_RE = re.compile(r"^(\S+) (\d+):(\d+)$")


def load_types(path) -> list:
    """Parse jesus_types.tsv: ref<TAB>target<TAB>occurrence<TAB>match<TAB>theme.

    Returns a list of dicts (ref, abbr, chapter, verse, target, occurrence, match, theme, line).
    Comments (#) and blank lines are ignored. Raises TypesError with a line number on a bad row.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise TypesError(f"{path}: file not found") from None
    except UnicodeDecodeError as e:
        raise TypesError(f"{path}: not valid UTF-8 ({e})") from e
    entries, seen = [], set()
    for n, line in enumerate(raw.splitlines(), 1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        f = [part.strip() for part in line.split("\t")]
        if len(f) != 5:
            raise TypesError(f"{path}:{n}: expected 5 tab-separated fields "
                             f"(ref, target, occurrence, match, theme), got {len(f)}: {line[:80]!r}")
        ref, target, occ, match, theme = f
        m = REF_RE.match(ref)
        if not m or m.group(1) not in BOOK_INDEX:
            raise TypesError(f"{path}:{n}: bad ref {ref!r} (expected e.g. 'Ge 3:15')")
        if not target:
            raise TypesError(f"{path}:{n}: empty target")
        try:
            occ_n = int(occ) if occ else 1
        except ValueError:
            raise TypesError(f"{path}:{n}: occurrence must be a number, got {occ!r}") from None
        if occ_n < 1:
            raise TypesError(f"{path}:{n}: occurrence must be >= 1")
        if match not in TYPE_MATCH_LEVELS:
            raise TypesError(f"{path}:{n}: match must be one of {TYPE_MATCH_LEVELS}, got {match!r}")
        key = (ref, target.lower(), occ_n)
        if key in seen:
            raise TypesError(f"{path}:{n}: duplicate entry for {ref} {target!r} #{occ_n}")
        seen.add(key)
        entries.append({"ref": ref, "abbr": m.group(1), "chapter": int(m.group(2)), "verse": int(m.group(3)),
                        "target": target, "occurrence": occ_n, "match": match, "theme": theme, "line": n})
    if not entries:
        raise TypesError(f"{path}: no entries found")
    return entries


def index_types(entries: list) -> dict:
    by_ref = {}
    for e in entries:
        by_ref.setdefault(e["ref"], []).append(e)
    return by_ref


def apply_type_marker(text: str, entry: dict):
    """Put [JESUS] after the entry's Nth occurrence of its target in `text` (already processed).

    Returns (new_text, status): "added", or "already" when that occurrence is already followed by
    [JESUS] (so nothing is added). Raises TypesError if the target (or that occurrence) is not found.
    """
    pattern = re.compile(r"(?<!\w)" + re.escape(entry["target"]) + r"(?!\w)", re.I)
    matches = list(pattern.finditer(text))
    if len(matches) < entry["occurrence"]:
        raise TypesError(f"{entry['ref']}: target {entry['target']!r} occurrence #{entry['occurrence']} "
                         f"not found ({len(matches)} match(es)) in: {text!r}")
    end = matches[entry["occurrence"] - 1].end()
    if text.startswith(JESUS_MARK, end):
        return text, "already"
    return text[:end] + JESUS_MARK + text[end:], "added"


TYPES = load_types(DEFAULT_TYPES_PATH)
TYPES_BY_REF = index_types(TYPES)


def apply_types(entries: list) -> None:
    """Install a list of type entries as the process-wide TYPES / TYPES_BY_REF."""
    global TYPES, TYPES_BY_REF
    TYPES = entries
    TYPES_BY_REF = index_types(entries)


# ---------------------------------------------------------------------------
# Divine pronouns (divine_pronouns.py): he/him that refer to GOD or JESUS -> He[JESUS] / Him[JESUS]
# divine_pronouns.tsv holds manual include/exclude overrides for the heuristic.
# ---------------------------------------------------------------------------
PRONOUN_OVERRIDES = dp.load_overrides(DEFAULT_PRONOUNS_PATH, BOOK_INDEX)


def apply_pronoun_overrides(entries: list) -> None:
    global PRONOUN_OVERRIDES
    PRONOUN_OVERRIDES = entries


def mark_divine_pronouns(items, overrides=None, common=None):
    """Run the divine-pronoun stage over processed verses in canonical order.

    items: list of (ref, abbr, text, raw) where text is the processed verse (no 'C:V: ' prefix) and raw is
    the KJV verse text (italic brackets stripped) or None. common: words seen in lowercase (default: from
    items), used to tell proper names from sentence-initial words. Returns (new_texts, decisions).
    Raises dp.OverridesError when an override does not match a he/him in its verse.
    """
    overrides = PRONOUN_OVERRIDES if overrides is None else overrides
    if common is None:
        common = dp.common_words(t for _, _, t, _ in items)
    resolver = dp.Resolver(common, dp.index_overrides(overrides))
    nt_start = BOOK_INDEX["Mt"]
    out, decisions, book = [], [], None
    for ref, abbr, text, raw in items:
        if abbr != book:
            book = abbr
            resolver.reset()
        new, ds = resolver.verse(ref, abbr, text, BOOK_INDEX[abbr] >= nt_start, raw)
        for d in ds:
            d["before"], d["after"] = text, new
        decisions.extend(ds)
        out.append(new)
    unused = [o for o in overrides if (o["ref"], o["word"], o["occurrence"]) not in resolver.used_overrides]
    if unused:
        raise dp.OverridesError("divine_pronouns.tsv: no matching he/him for " + ", ".join(
            f"line {o['line']} ({o['ref']} {o['word']} #{o['occurrence']})" for o in unused))
    return out, decisions


# Static prose appended when regenerating REPLACEMENTS.md from swaps.tsv.
# Keep this in sync with the hand-written context-rule section of that file.
ART_RULE_MD = (
    "## Context rule: `art`\n"
    "\n"
    "`art` → `are` only when it is the verb (*thou art*, *art thou*, *which art*). It is **not** in the table above,\n"
    "so the noun stays: \"the art of the apothecary\" (Ex 30:25, 30:35), \"the apothecaries’ art\" (2Ch 16:14) and\n"
    "\"graven by art\" (Ac 17:29). The rule skips any `art` right after \"the \", \"by \" or a possessive apostrophe.\n"
)


def write_replacements_md(swaps=None, path=None) -> Path:
    """Generate REPLACEMENTS.md from a swaps mapping or TSV path. Returns the written path."""
    if swaps is None:
        swaps = REPLACEMENTS
    elif not isinstance(swaps, dict):
        swaps = load_swaps(swaps)
    path = Path(path) if path is not None else DEFAULT_REPLACEMENTS_MD
    lines = [
        "# Word replacements",
        "",
        "All modernization word swaps applied by `jesus_centric_kjv_processor.py`.",
        "The source of truth is `swaps.tsv` (one `old<TAB>new` pair per line). This file is generated from it:",
        "",
        "```bash",
        "python3 jesus_centric_kjv_processor.py --write-replacements-md",
        "```",
        "",
        "Context rules that are not simple word pairs (currently the verb `art`) stay in the processor, not in `swaps.tsv`.",
        "",
        f"Total: **{len(swaps)}**",
        "",
        "| From | To |",
        "|------|----|",
    ]
    for old, new in sorted(swaps.items(), key=lambda kv: kv[0].lower()):
        lines.append(f"| `{old}` | `{new}` |")
    lines.append("")
    lines.append(ART_RULE_MD.rstrip("\n"))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_types_md(entries=None, path=None) -> Path:
    """Generate JESUS_TYPES.md from a list of entries or a TSV path. Returns the written path."""
    if entries is None:
        entries = TYPES
    elif not isinstance(entries, list):
        entries = load_types(entries)
    path = Path(path) if path is not None else DEFAULT_TYPES_MD
    names = {abbr: name for abbr, name, _ in BOOKS}
    entries = sorted(entries, key=lambda e: (BOOK_INDEX[e["abbr"]], e["chapter"], e["verse"], e["line"]))
    counts = {lvl: sum(1 for e in entries if e["match"] == lvl) for lvl in TYPE_MATCH_LEVELS}
    esc = lambda t: t.replace("|", "\\|")
    lines = [
        "# Jesus-type markers",
        "",
        "Verses where the processor adds `[JESUS]` right after a word that points to Christ, taken from the",
        "\"books of the Bible reveal Christ\" chart. The source of truth is `jesus_types.tsv`. This file is generated from it:",
        "",
        "```bash",
        "python3 jesus_centric_kjv_processor.py --write-types-md",
        "```",
        "",
        "The target is matched in the processed (modernized) verse. If it already carries `[JESUS]` from the",
        "Word / Lamb / Christ / Son of Man / Son of God rules, nothing more is added.",
        "",
        f"Total: **{len(entries)}** (strong {counts['strong']}, moderate {counts['moderate']}, weak {counts['weak']})",
        "",
        "| Book | Verse | Target | # | Match | Theme |",
        "|------|-------|--------|---|-------|-------|",
    ]
    for e in entries:
        lines.append(f"| {names[e['abbr']]} | {e['chapter']}:{e['verse']} | `{esc(e['target'])}` | "
                     f"{e['occurrence']} | {e['match']} | {esc(e['theme'])} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def match_case(found, target):
    """Give `target` the capitalization of the matched KJV text `found`.
    lowercase -> target as written; ALL CAPS (2+ letters) -> TARGET; otherwise (Title or mixed case)
    -> target with only its first letter capitalized ("Unto" -> "To", "Thence" -> "From there")."""
    letters = [c for c in found if c.isalpha()]
    if not letters or found.islower():
        return target
    if len(letters) > 1 and found.isupper():
        return target.upper()
    if found[0].isupper():
        return target[:1].upper() + target[1:]
    return target

# "art" the verb (thou art, art thou, which art) -> "are", but NOT "art" the noun (craft/skill).
# In the PCE the noun appears only 4 times: "the art of the apothecary" (Ex 30:25, 30:35),
# "the apothecaries' art" (2Ch 16:14) and "graven by art" (Ac 17:29). Those are skipped by
# refusing a match right after "the ", "by " or a possessive apostrophe + space.
ART_VERB_PATTERN = re.compile(r"(?<![Tt]he )(?<![Bb]y )(?<![\u2019'] )(?<!\w)art(?!\w)", re.I)

def modernize_line(line):
    # Pass 1: explicit replacements (longest first), keeping the original word's capitalization
    for pattern, new in COMPILED_REPLACEMENTS:
        line = pattern.sub(lambda m, new=new: match_case(m.group(0), new), line)
    # Pass 2: verb "art" -> "are" (noun "art" left alone, see ART_VERB_PATTERN)
    line = ART_VERB_PATTERN.sub(lambda m: match_case(m.group(0), "are"), line)
    # The general "-eth -> -s" pass was removed: it mangled words such as compasseth -> "compasss".
    # Only -eth words listed explicitly in swaps.tsv / REPLACEMENTS are modernized; all others keep the KJV form.
    return line

def capitalize_divine(line):
    def repl(m):
        w = m.group(0)
        return w.upper() if w.lower() in ("lord", "god") else w
    return LORD_GOD_PATTERN.sub(repl, line)

def uppercase_jesus(line):
    return re.sub(r"\b[Jj]esus\b", "JESUS", line)

def add_jesus_marker(line):
    # Protect the compound names "JESUS CHRIST" and "CHRIST JESUS" (any case) so that neither is
    # marked as CHRIST[JESUS]: JESUS is already named in them. Both are restored in capitals.
    protected = []
    def protect(m):
        protected.append("CHRIST JESUS" if m.group(0).split()[0].lower() == "christ" else "JESUS CHRIST")
        return f"__JESUS_NAME_PROTECTED_{len(protected) - 1}__"
    line = re.sub(r"\b(?:JESUS\s+CHRIST|CHRIST\s+JESUS)\b", protect, line, flags=re.I)

    terms = [r"\bWord\b", r"\bLamb\b", r"\bChrist\b", r"\bMessiah\b", r"\bSon of Man\b", r"\bSon of God\b"]
    def repl(m):
        t = m.group(0).upper()
        return t if t == "JESUS" else f"{t}[JESUS]"

    for term in terms:
        line = re.compile(term, re.I).sub(repl, line)

    # Restore protected names
    for i, name in enumerate(protected):
        line = line.replace(f"__JESUS_NAME_PROTECTED_{i}__", name)
    return line

def apply_type_markers(line, ref):
    """Apply jesus_types.tsv entries for verse `ref` ("Ge 3:15") to a processed 'C:V: text' line."""
    entries = TYPES_BY_REF.get(ref)
    if not entries:
        return line
    head, sep, text = line.partition(": ")      # keep the 'C:V: ' prefix out of the target search
    for entry in entries:
        text, _status = apply_type_marker(text, entry)
    return head + sep + text


def process_line(line, ref=None):
    """Full pipeline for one verse line. `ref` (PCE style, e.g. "Ge 3:15") enables the per-verse
    jesus_types.tsv markers; without it (legacy files) only the general marker rules run."""
    line = modernize_line(line)
    line = capitalize_divine(line)
    line = uppercase_jesus(line)
    line = add_jesus_marker(line)
    if ref is not None:
        line = apply_type_markers(line, ref)
    return line


def _is_pce_file(path: Path) -> bool:
    with open(path, "rb") as f:
        head = decode_pce(f.read(4096)[:4000]) if path.stat().st_size else ""
    first = next((l for l in head.splitlines() if l.strip()), "")
    m = PCE_LINE.match(first)
    return bool(m and m.group(1) in BOOK_INDEX)


def process_file(inp, outp, pronouns=True):
    """Legacy mode: process a plain 'HEADER / C:V: text' file line by line."""
    header_abbr = {header: abbr for abbr, _, header in BOOKS}
    with open(inp, encoding="utf-8", errors="replace") as fin:
        rows, abbr = [], None
        for raw in fin:
            line = raw.rstrip("\r\n")
            m = re.match(r"^(\d+):(\d+): ", line)
            if line in header_abbr and not m:
                abbr = header_abbr[line]
            if m and abbr:
                rows.append(["verse", process_line(line), f"{abbr} {m.group(1)}:{m.group(2)}", abbr])
            else:
                rows.append(["other", process_line(line) if line.strip() else "", None, None])
    if pronouns:
        verse_rows = [r for r in rows if r[0] == "verse"]
        items = [(r[2], r[3], r[1].partition(": ")[2], None) for r in verse_rows]
        texts, _ = mark_divine_pronouns(items, overrides=[])
        for r, t in zip(verse_rows, texts):
            r[1] = r[1].partition(": ")[0] + ": " + t
    with open(outp, "w", encoding="utf-8", newline="\n") as fout:
        for r in rows:
            fout.write(r[1] + "\n")
    print(f"Processed {inp} -> {outp}")


def process_pce(source, outp, italics="strip", titles_json=None, timeout=30.0, pronouns=True,
                pronoun_review=None):
    verses, origin = load_pce(source, timeout=timeout)
    print(f"Loaded PCE from {origin}: {EXPECTED_BOOKS} books, {EXPECTED_CHAPTERS} chapters, {len(verses)} verses")
    outp = Path(outp)
    outp.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    items = []
    for v in verses:
        ref = f"{v['abbr']} {v['chapter']}:{v['verse']}"
        used.add(ref)
        line = process_line(f"{v['chapter']}:{v['verse']}: {render_text(v['text'], italics)}", ref)
        items.append((ref, v["abbr"], line.partition(": ")[2], render_text(v["text"], "strip")))
    missing = sorted(set(TYPES_BY_REF) - used)
    if missing:
        raise TypesError(f"jesus_types.tsv refers to verses not in the source: {', '.join(missing)}")
    if pronouns:
        texts, decisions = mark_divine_pronouns(items)
        changed = sum(1 for d in decisions if d["status"] == "include" and not d["already"])
        print(f"Divine pronouns: {changed} he/him marked")
        if pronoun_review:
            md, csv_path = dp.write_review(decisions, pronoun_review, [b[0] for b in BOOKS])
            print(f"Wrote divine-pronoun review -> {md}, {csv_path}")
    else:
        texts = [t for _, _, t, _ in items]
    with open(outp, "w", encoding="utf-8", newline="\n") as fout:
        current = None
        for v, text in zip(verses, texts):
            if v["abbr"] != current:
                current = v["abbr"]
                fout.write(v["header"] + "\n")
            fout.write(f"{v['chapter']}:{v['verse']}: {text}\n")
    if titles_json:
        Path(titles_json).write_text(json.dumps(titles_metadata(verses), ensure_ascii=False, indent=1) + "\n",
                                     encoding="utf-8")
        print(f"Wrote Psalm titles / colophons -> {titles_json}")
    print(f"Processed {origin} -> {outp}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Jesus-centric KJV processor (source: Pure Cambridge Edition)")
    p.add_argument("paths", nargs="*", type=Path, metavar="[input] [output]",
                   help="no args: PCE -> docs/jesus_centric_kjv_all66.txt; one arg: output path; "
                        "two args: input (PCE or legacy 'C:V: text' file) and output")
    p.add_argument("--source", "--pce-path", dest="source",
                   help="PCE file path or URL (default: docs/TEXT-PCE.txt, fallback: raw GitHub URL)")
    p.add_argument("--swaps", type=Path, default=DEFAULT_SWAPS_PATH,
                   help="TSV of word swaps, one old<TAB>new per line (default: swaps.tsv next to this script)")
    p.add_argument("--write-replacements-md", nargs="?", const=DEFAULT_REPLACEMENTS_MD,
                   type=Path, metavar="PATH",
                   help="regenerate REPLACEMENTS.md from the swaps file and exit "
                        "(default path: REPLACEMENTS.md next to this script)")
    p.add_argument("--types", type=Path, default=DEFAULT_TYPES_PATH,
                   help="TSV of per-verse [JESUS] markers (default: jesus_types.tsv next to this script)")
    p.add_argument("--write-types-md", nargs="?", const=DEFAULT_TYPES_MD, type=Path, metavar="PATH",
                   help="regenerate JESUS_TYPES.md from the types file and exit "
                        "(default path: JESUS_TYPES.md next to this script)")
    p.add_argument("--pronouns", type=Path, default=DEFAULT_PRONOUNS_PATH,
                   help="TSV of divine-pronoun overrides (default: divine_pronouns.tsv next to this script)")
    p.add_argument("--no-divine-pronouns", action="store_true",
                   help="skip the stage that writes He[JESUS] / Him[JESUS] for pronouns of GOD or JESUS")
    p.add_argument("--pronoun-review", type=Path, metavar="PREFIX",
                   help="also write PREFIX.md and PREFIX.csv listing every divine-pronoun decision")
    p.add_argument("--italics", choices=["strip", "keep", "html"], default="strip",
                   help="PCE [italic] supplied words: strip brackets (default), keep [ ], or wrap in <i></i>")
    p.add_argument("--titles-json", type=Path, help="also write Psalm titles / colophons (<<...>>) as JSON")
    p.add_argument("--timeout", type=float, default=30.0, help="download timeout in seconds (default 30)")
    args = p.parse_args(argv)
    if len(args.paths) > 2:
        p.error("expected at most two paths: [input] [output]")
    try:
        if Path(args.swaps) != DEFAULT_SWAPS_PATH or args.write_replacements_md:
            apply_swaps(load_swaps(args.swaps))
        if Path(args.types) != DEFAULT_TYPES_PATH or args.write_types_md:
            apply_types(load_types(args.types))
        if Path(args.pronouns) != DEFAULT_PRONOUNS_PATH:
            apply_pronoun_overrides(dp.load_overrides(args.pronouns, BOOK_INDEX))
        pron = not args.no_divine_pronouns
        if args.write_types_md is not None:
            out_md = write_types_md(TYPES, args.write_types_md)
            print(f"Wrote {len(TYPES)} jesus-type markers -> {out_md}")
            return
        if args.write_replacements_md is not None:
            out_md = write_replacements_md(REPLACEMENTS, args.write_replacements_md)
            print(f"Wrote {len(REPLACEMENTS)} swaps -> {out_md}")
            return
        if len(args.paths) == 2:
            inp, outp = args.paths
            if args.source:
                p.error("give either an input path or --source, not both")
            if _is_pce_file(inp):
                process_pce(inp, outp, args.italics, args.titles_json, args.timeout, pron, args.pronoun_review)
            else:
                process_file(inp, outp, pron)
        else:
            outp = args.paths[0] if args.paths else DEFAULT_OUTPUT
            process_pce(args.source, outp, args.italics, args.titles_json, args.timeout, pron, args.pronoun_review)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
