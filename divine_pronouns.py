"""Divine pronouns: capitalize he/him that refer to God or Jesus and mark them He[JESUS] / Him[JESUS].

Runs on the PROCESSED verse text (after swaps, LORD/GOD, JESUS and the [JESUS] title markers), one book
at a time, so a pronoun can look back to an antecedent in the same verse or the previous verses.

How a pronoun is resolved (heuristic, tuned for precision):
  * Mentions are scanned left to right: divine names/titles (GOD, LORD, JESUS, CHRIST[JESUS], Holy Ghost,
    Spirit, Father, Almighty, Most High, ...), singular human nouns (man, king, servant, prophet, ...),
    proper names (a capitalized word that never appears in lowercase in the Bible), and the pronouns
    he / him / his / himself (each resolved in turn, so a chain of pronouns follows its antecedent).
    Plural nouns are ignored: "he" cannot refer to them.
  * A pronoun takes the nearest earlier singular mention, looking back at most two verses (same book).
  * "him" cannot be the subject of its own sentence ("JESUS said to him", "created he him"), so when the
    sentence subject or a "he" in the same clause is divine, a divine antecedent is not accepted for "him".
  * "he" is ambiguous (left unchanged) when the sentence subject and the nearest mention disagree
    ("Moses went up to GOD, and he ...").
  * "the man of GOD", "the servant of the LORD", "the angel of the LORD" count as the human/angel, not GOD.
  * "he that ..." / "him that ..." are generic people and stay lowercase, except "he/him that sent me".
  * Confidence: high = divine name in the same verse; medium = previous verse, or a pronoun chain one verse
    back; low = two verses back. Only high and medium are applied; low and ambiguous go to the review list.
  * divine_pronouns.tsv (ref, word, occurrence, action[, note]) overrides any decision: include / exclude.
"""
import re
from pathlib import Path

JESUS_MARK = "[JESUS]"
ACTIONS = ("include", "exclude")
GOSPELS = {"Mt", "Mr", "Lu", "Joh"}


class OverridesError(ValueError):
    """Raised when divine_pronouns.tsv is malformed or an override does not match its verse."""


# --------------------------------------------------------------------------- overrides file
def load_overrides(path, book_index=None) -> list:
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise OverridesError(f"{path}: file not found") from None
    out, seen = [], set()
    for n, line in enumerate(raw.splitlines(), 1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        f = [p.strip() for p in line.split("\t")]
        if len(f) not in (4, 5):
            raise OverridesError(f"{path}:{n}: expected 4 or 5 tab-separated fields "
                                 f"(ref, word, occurrence, action[, note]), got {len(f)}: {line[:80]!r}")
        ref, word, occ, action = f[:4]
        note = f[4] if len(f) == 5 else ""
        m = re.match(r"^(\S+) (\d+):(\d+)$", ref)
        if not m or (book_index is not None and m.group(1) not in book_index):
            raise OverridesError(f"{path}:{n}: bad ref {ref!r} (expected e.g. 'Ps 23:2')")
        if word.lower() not in ("he", "him"):
            raise OverridesError(f"{path}:{n}: word must be 'he' or 'him', got {word!r}")
        try:
            occ_n = int(occ)
        except ValueError:
            raise OverridesError(f"{path}:{n}: occurrence must be a number, got {occ!r}") from None
        if occ_n < 1:
            raise OverridesError(f"{path}:{n}: occurrence must be >= 1")
        if action not in ACTIONS:
            raise OverridesError(f"{path}:{n}: action must be one of {ACTIONS}, got {action!r}")
        key = (ref, word.lower(), occ_n)
        if key in seen:
            raise OverridesError(f"{path}:{n}: duplicate override {ref} {word} #{occ_n}")
        seen.add(key)
        out.append({"ref": ref, "word": word.lower(), "occurrence": occ_n, "action": action,
                    "note": note, "line": n})
    return out


def index_overrides(entries: list) -> dict:
    return {(e["ref"], e["word"], e["occurrence"]): e for e in entries}


# --------------------------------------------------------------------------- vocabulary
# Divine names / titles, longest first. (regex, category). Category "LORD" is resolved per testament.
DIVINE_PATTERNS = [
    (r"SON OF MAN\[JESUS\]", "Jesus"), (r"SON OF GOD\[JESUS\]", "Jesus"),
    (r"(?:CHRIST|WORD|LAMB|MESSIAH)\[JESUS\]", "Jesus"),
    (r"JESUS CHRIST|CHRIST JESUS|JESUS", "Jesus"),
    (r"Holy (?:Ghost|Spirit)|Spirit of (?:GOD|the LORD|CHRIST(?:\[JESUS\])?)|Comforter", "Holy Spirit"),
    (r"LORD GOD|LORD of hosts|GOD|Almighty|Most High|Highest|Holy One|Creator|Maker|Rock|Redeemer", "God"),
    (r"LORD", "LORD"),
    (r"Saviour", "Saviour"),
]
# Capitalized only when not at the start of a sentence (KJV caps them for God mid-sentence).
MIDSENTENCE_DIVINE = {"Spirit": "Holy Spirit", "Father": "God", "Son": "Jesus"}

HUMAN_NOUNS = set("""
man king servant prophet priest son father brother child lad youth stranger neighbour neighbor enemy adversary
fool wicked righteous sluggard scorner angel messenger captain prince judge master lord husband owner thief
murderer seer shepherd hireling steward centurion publican scribe ruler governor soldier leper disciple apostle
bridegroom heir person beast ox ass horse lion bullock ram goat serpent dragon devil deceiver transgressor
sinner hypocrite bastard Nazarite offerer prisoner captive orphan fatherless inhabitant nobleman labourer husbandman householder debtor creditor friend kinsman uncle nephew eunuch
porter watchman workman warrior one whoever whosoever whoso everyone nobody somebody fellow boy infant babe
grandson firstborn bondman bondservant slave elder chief officer herdman keeper physician merchant poor needy
upright simple slothful drunkard stranger sojourner traveller wayfaring builder smith potter carpenter
""".split())
GENERIC_FOLLOW = re.compile(r"^\s+(?:that|which|who|whom|whose)\b")
SENT_ME = re.compile(r"^\s+(?:that|which|who)\s+(?:sent|has sent|hath sent)\s+me\b")
# Words before a mention that leave it in subject position ("And JESUS said", "when the LORD saw").
SUBJECT_PREV = set("""and but then when for that because if so now behold look lo yet until as since lest how
also therefore wherefore thus moreover nevertheless neither nor or where while though although
surely truly even again verily which whom who
immediately straightway forthwith afterward afterwards likewise suddenly presently therefore""".split())
DETERMINERS = {"the", "our", "my", "your", "his", "their", "thy", "this", "a", "an", "every", "any", "no",
               "o", "o,"}
GENITIVE_HEADS = HUMAN_NOUNS | {"men", "children", "sons", "servants", "prophets", "people"}

TOKEN = re.compile(
    r"(?P<pron>\b(?:he|He|HE|him|Him|HIM|his|His|HIS|himself|Himself|HIMSELF)\b)(?P<pmark>\[JESUS\])?"
    r"|(?P<div>" + "|".join(f"(?:{p})" for p, _ in DIVINE_PATTERNS) + r")(?![\w\[])"
    r"|(?P<word>[A-Za-z][A-Za-z’']*)(?P<wmark>\[JESUS\])?"
    r"|(?P<stop>[.;:?!])|(?P<comma>,)"
)
DIVINE_RES = [(re.compile(rf"^(?:{p})$"), c) for p, c in DIVINE_PATTERNS]
SPEECH_VERBS = {"said", "says", "saith", "saying", "answered", "written", "cried", "sware",
                "swore", "testified", "prayed"}
PREDICATE_VERBS = {"is", "was", "be", "art", "are", "am", "were", "became", "become", "been"}
APPOSITIVE = re.compile(r"^,\s+(?:even\s+)?(?:the\s+|our\s+|my\s+)?(?P<d>"
                        + "|".join(f"(?:{p})" for p, _ in DIVINE_PATTERNS) + r"|Spirit|Father|Son)(?![\w\[])")
FIRST_PERSON = re.compile(r"\b(?:I|me|my|mine|we|us|our|ours)\b")
NOMINATIVE = {"i", "we", "they", "you", "ye", "thou", "she", "it"}
CONJ_CARRY = {"and", "but", "or", "nor", "then", "yet", "so"}
# Title markers that the general rules add to lowercase words too ("his word", "a lamb", Ezekiel's
# "son of man"): they count as JESUS only where the KJV itself capitalizes the title mid-sentence.
RAW_TITLES = {"WORD[JESUS]": r"word", "LAMB[JESUS]": r"lamb", "SON OF MAN[JESUS]": r"son of man",
              "SON OF GOD[JESUS]": r"son of god"}


def _divine_category(text, nt):
    for rx, cat in DIVINE_RES:
        if rx.match(text):
            if cat == "LORD":
                return "LORD (NT)" if nt else "God"
            if cat == "Saviour":
                return "Jesus" if nt else "God"
            return cat
    return None


def raw_title_flags(raw, phrase_rx):
    """For each occurrence of a title in the KJV (PCE) text: True when it is capitalized mid-sentence."""
    flags = []
    for m in re.finditer(rf"(?<![\w]){phrase_rx}(?!\w)", raw or "", re.I):
        before = raw[:m.start()].rstrip()
        sentence_start = not before or before[-1] in ".;:?!,"
        flags.append(m.group(0)[0].isupper() and not sentence_start)
    return flags


class Mention:
    __slots__ = ("kind", "cat", "verse", "sent", "clause", "subject", "csubj", "pron", "conf", "start", "end",
                 "word", "generic", "ssubj", "quote", "wordno", "voc", "fp")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


CONF_ORDER = {"high": 3, "medium": 2, "low": 1}


def _min_conf(a, b):
    return a if CONF_ORDER[a] <= CONF_ORDER[b] else b


class Resolver:
    """Resolve he/him across the verses of one book. Call reset() at each book, then verse() in order."""

    def __init__(self, common_words, overrides_by_key=None, lookback=2):
        self.common = common_words
        self.overrides = overrides_by_key or {}
        self.used_overrides = set()
        self.lookback = lookback
        self.reset()

    def reset(self):
        self.history = []   # mentions from earlier verses of the current book
        self._quote_verses = set()
        self.focus = None   # Gospels: (kind, category, verse) of the last narrative subject
        self.vno = 0

    # ---- scanning --------------------------------------------------------
    def _scan(self, text, abbr, nt, raw):
        mentions = []
        sent = clause = 0
        prev_words = []          # lowercase words of the current sentence
        cur_subject = None       # subject mention of the current clause
        after_comma = False
        title_flags = {k: raw_title_flags(raw, rx) if raw is not None else None for k, rx in RAW_TITLES.items()}
        title_seen = {k: 0 for k in RAW_TITLES}
        sent_subject = None      # first subject mention of the current sentence
        quote_start = None       # text offset where quoted speech starts in this verse
        speech_pending = None    # words since a speech verb ("said", "saying", ...) awaiting , or :
        wordno = 0
        quote_opened = False
        self._ends_in_quote = False

        def add(kind, cat, m, word, pron=None, conf="high", subj=False, generic=False):
            nonlocal cur_subject, sent_subject
            mm = Mention(kind=kind, cat=cat, verse=self.vno, sent=sent, clause=clause, subject=subj,
                         csubj=cur_subject, pron=pron, conf=conf, start=m.start(), end=m.end(), word=word,
                         generic=generic, ssubj=sent_subject, quote=quote_start, wordno=wordno)
            mentions.append(mm)
            if subj and (pron in (None, "he")):
                cur_subject = mm
                if sent_subject is None:
                    sent_subject = mm
            return mm

        for m in TOKEN.finditer(text):
            if m.group("stop") or m.group("comma"):
                if speech_pending is not None and m.group(0) in ",:;" and quote_start is None:
                    quote_start = m.end()
                    quote_opened = True
                speech_pending = None
            if m.group("stop"):
                sent += 1; clause += 1; prev_words = []; cur_subject = None; after_comma = False
                sent_subject = None
                continue
            if m.group("comma"):
                clause += 1; prev_words.append(","); after_comma = True
                continue
            wordno += 1
            if speech_pending is not None:
                speech_pending += 1
                if speech_pending > 5:
                    speech_pending = None
            if m.group(0).lower() in SPEECH_VERBS:
                speech_pending = 0
            tok = m.group(0)
            first = tok.split("[")[0].split()[0].lower()
            if after_comma:
                after_comma = False
                if first not in CONJ_CARRY:
                    cur_subject = None
            pw = [w for w in prev_words if w not in DETERMINERS]
            subj = (not pw) or pw[-1] in SUBJECT_PREV or quote_opened   # first word of a quote too
            quote_opened = False
            sentence_start = not prev_words
            if m.group("pron"):
                w = m.group("pron"); lw = w.lower()
                generic = lw in ("he", "him") and bool(GENERIC_FOLLOW.match(text[m.end():]))
                mm = add(None, None, m, w, pron=lw, conf=None, subj=subj and lw == "he", generic=generic)
                mm.end = m.end("pron")
                if m.group("pmark"):
                    mm.kind, mm.cat, mm.conf = "divine", "marked", "high"
                prev_words.append(lw)
                continue
            if m.group("div"):
                d = m.group("div")
                cat = _divine_category(d, nt)
                if d in RAW_TITLES:
                    flags = title_flags[d]; i = title_seen[d]; title_seen[d] += 1
                    is_title = bool(flags) and i < len(flags) and flags[i]
                    if not is_title:
                        if d == "SON OF MAN[JESUS]" or d == "SON OF GOD[JESUS]":
                            add("human", "human", m, d, subj=subj)
                        prev_words.append(d.lower())
                        continue
                tail = [w for w in prev_words if w != "the"]
                if len(tail) >= 2 and tail[-1] == "of" and tail[-2] in GENITIVE_HEADS:
                    prev_words.append(d.lower())     # "man of GOD": the head noun is the referent
                    continue
                possessive = text[m.end():m.end() + 2] in ("’s", "'s")
                mm = add("divine", cat, m, d, subj=subj and not possessive)
                mm.voc = bool(prev_words) and prev_words[-1] == "o"
                # "the word of the LORD came to him", "the anger of the LORD ... against him",
                # "GOD's anger ... him": for 'him' these bind like a subject (him is someone else)
                head = [w for w in prev_words if w not in DETERMINERS]
                if (len(head) >= 2 and head[-1] == "of" and
                        (len(head) == 2 or head[-3] in SUBJECT_PREV)) or (possessive and subj):
                    if sent_subject is None:
                        sent_subject = mm
                    cur_subject = mm
                prev_words.append(d.lower())
                continue
            w = m.group("word"); lw = w.lower()
            if lw in NOMINATIVE and subj:
                # "he is my GOD, and I will prepare him": a new (non-third-person) subject ends the binding
                cur_subject = sent_subject = None
            if lw in ("and", "but", "that", "which", "who", "when", "because", "for") and w.islower():
                clause += 1
            if (w in MIDSENTENCE_DIVINE and not sentence_start and not (pw and pw[-1] == ",")
                    and not (w == "Father" and text[m.end():].startswith(" Abraham"))):
                add("divine", MIDSENTENCE_DIVINE[w], m, w, subj=subj)
                prev_words.append(lw)
                continue
            if w == "Master" and abbr in GOSPELS and not sentence_start:
                add("divine", "Jesus", m, w, subj=subj)
                prev_words.append(lw)
                continue
            base = re.sub(r"[’']s?$", "", lw)
            possessive = base != lw
            predicate = bool(pw) and pw[-1] in PREDICATE_VERBS   # "The LORD is my shepherd"
            if not predicate and (base in HUMAN_NOUNS or (w[0].isupper() and base not in self.common
                                                          and len(base) > 1 and w not in ("I", "O"))):
                add("human", "human", m, w, subj=subj and not possessive)
            prev_words.append(lw)
        self._ends_in_quote = quote_start is not None
        first_person = [bool(FIRST_PERSON.search(part)) for part in re.split(r"[.;:?!]", text)]
        for mm in mentions:
            mm.fp = first_person[mm.sent] if mm.sent < len(first_person) else False
        return mentions

    # ---- resolution ------------------------------------------------------
    def _resolve(self, m, earlier, text):
        """Return (kind, category, confidence, reason) for pronoun mention m."""
        after = text[m.end:]
        if m.generic:
            if SENT_ME.match(after):
                return "divine", "God", "high", "he/him that sent me"
            return "human", "generic", "high", "generic 'he that' / 'him that'"
        ap = APPOSITIVE.match(after)
        if ap and m.pron in ("he", "him"):
            cat = _divine_category(ap.group("d"), self._nt) or MIDSENTENCE_DIVINE.get(ap.group("d"))
            return "divine", cat, "high", f"apposition '{ap.group('d')}'"
        block_divine, skip = False, set()
        if m.pron == "him":
            for cs in (m.csubj, m.ssubj):
                if cs is not None and cs.verse == m.verse and (m.quote is None or cs.start > m.quote):
                    skip.add(id(cs))
                    if cs.kind == "divine":
                        block_divine = True
            for x in earlier:     # "created he him": him is not the 'he' of its own clause
                if x.pron == "he" and x.verse == m.verse and x.clause == m.clause:
                    skip.add(id(x))
                    if x.kind == "divine":
                        block_divine = True
        skipped_human = False
        for x in reversed(earlier):
            dist = m.verse - x.verse
            if dist > self.lookback:
                break
            if id(x) in skip:
                skipped_human = skipped_human or x.kind != "divine"
                continue
            if x.kind == "other":       # a 'him' that is someone other than a divine subject: uninformative
                continue
            if x.voc:
                return "ambiguous", x.cat, "low", f"nearest mention 'O {x.word}' is a vocative"
            if x.kind is None or x.kind == "ambiguous":
                return "ambiguous", None, "low", f"antecedent {x.word!r} is itself unresolved"
            if x.kind == "human":
                return "human", x.cat, "high", f"nearest antecedent is {x.word!r}"
            # divine candidate
            if m.quote is not None and (x.verse < m.verse or x.start < m.quote):
                return "ambiguous", x.cat, "low", (f"inside quoted speech; {x.word!r} is outside the quote "
                                                   "(the speaker would say 'I')")
            if x.quote is not None and x.start > x.quote and (x.verse != m.verse or m.quote is None):
                return "ambiguous", x.cat, "low", f"{x.word!r} is inside quoted speech, the pronoun is not"
            if skipped_human and not (x.verse == m.verse and x.sent == m.sent):
                return "ambiguous", x.cat, "low", "skipped a human clause subject to reach a divine name"
            if x.verse < m.verse and x.verse in self._quote_verses and m.wordno > 6:
                return "ambiguous", x.cat, "low", f"{x.word!r} is followed by quoted speech in its verse"
            if block_divine:
                return "other", x.cat, "low", "the clause subject is divine, so 'him' is someone else"
            cs = m.csubj
            if m.pron in ("he", "his", "himself") and cs is not None and cs is not x and cs.kind != "divine":
                return "ambiguous", x.cat, "low", f"clause subject {cs.word!r} is not divine"
            if (x.verse != m.verse or x.sent != m.sent) and x.fp and not m.fp and not x.pron:
                return "ambiguous", x.cat, "low", (f"{x.word!r} is in a first-person sentence (speech?) and the "
                                                   "pronoun is not")
            if dist >= 1 and x.pron in ("his", "himself"):
                return "ambiguous", x.cat, "low", f"only a '{x.pron}' in an earlier verse points to GOD"
            if dist >= 1:
                rivals = [y for y in earlier if x.verse <= y.verse < m.verse and y is not x
                          and y.kind in ("human", "ambiguous")]
                if rivals:
                    return "ambiguous", x.cat, "low", (f"antecedent {x.word!r} is in an earlier verse that also "
                                                       f"names {rivals[-1].word!r}")
            topic = any(y.kind == "divine" and y.cat == x.cat and y.subject and not y.pron
                        and y.verse == m.verse and y.start < m.start for y in earlier)
            if not x.subject and not x.pron and not topic:
                rivals = [y for y in earlier if y.verse in (m.verse, x.verse) and y is not x
                          and (y.verse < m.verse or y.start < m.start)
                          and y.kind in ("human", "ambiguous")]
                if rivals:
                    return "ambiguous", x.cat, "low", (f"{x.word!r} is not a subject and {rivals[-1].word!r} "
                                                       "is also in the verse")
            conf = {0: "high", 1: "medium"}.get(dist, "low")
            if x.pron:
                conf = _min_conf(conf, x.conf or "low")
                if dist >= 1 and conf == "high":
                    conf = "medium"
            reason = f"antecedent {x.word!r}" + ("" if dist == 0 else f" {dist} verse(s) back")
            return "divine", x.cat, conf, reason
        return "none", None, "low", "no antecedent found"

    def verse(self, ref, abbr, text, nt=False, raw=None):
        """Resolve one verse (processed text). Returns (new_text, decisions)."""
        self._nt = nt
        mentions = self._scan(text, abbr, nt, raw)
        earlier = list(self.history)
        decisions, counts = [], {}
        for mm in mentions:
            if mm.pron:
                if mm.kind is None:
                    kind, cat, conf, reason = self._resolve(mm, earlier, text)
                    mm.kind, mm.cat, mm.conf = kind, cat, conf
                    if kind == "none" or (kind == "divine" and conf == "low"):
                        mm.kind = "ambiguous"
                    if (mm.kind == "ambiguous" and abbr in GOSPELS and mm.pron == "he" and mm.subject
                            and not mm.generic and mm.quote is None
                            and (reason.startswith("no antecedent") or reason.endswith("itself unresolved"))
                            and self.focus and self.focus[0] == "divine" and self.focus[1] in ("Jesus", "LORD (NT)")
                            and self.vno - self.focus[2] <= 6):
                        mm.kind, mm.cat, mm.conf = "divine", "Jesus", "medium"
                        reason = "Gospel narrative: JESUS is the current subject"
                else:
                    reason = "already marked [JESUS]"
                if mm.pron in ("he", "him"):
                    counts[mm.pron] = counts.get(mm.pron, 0) + 1
                    occ = counts[mm.pron]
                    status = "include" if (mm.kind == "divine" and CONF_ORDER.get(mm.conf, 0) >= 2) else "skip"
                    ov = self.overrides.get((ref, mm.pron, occ))
                    if ov:
                        self.used_overrides.add((ref, mm.pron, occ))
                        status = ov["action"]
                        reason = "override" + (f": {ov['note']}" if ov["note"] else "")
                        if status == "include":
                            if mm.kind != "divine":
                                mm.cat = "override"
                            mm.kind, mm.conf = "divine", "high"
                        else:
                            mm.kind, mm.cat, mm.conf = "human", "override", "high"
                    decisions.append({"ref": ref, "word": mm.word, "occurrence": occ, "start": mm.start,
                                      "end": mm.end, "kind": mm.kind, "referent": mm.cat, "confidence": mm.conf,
                                      "reason": reason, "status": status,
                                      "already": text.startswith(JESUS_MARK, mm.end)})
            earlier.append(mm)
            if mm.subject and mm.quote is None and not mm.generic and mm.kind in ("human", "divine"):
                self.focus = (mm.kind, mm.cat, self.vno)
        new = text
        for d in sorted(decisions, key=lambda d: -d["start"]):
            if d["status"] == "include":
                w = d["word"]
                cap = w if w.isupper() else w[0].upper() + w[1:]
                new = new[:d["start"]] + cap + ("" if d["already"] else JESUS_MARK) + new[d["end"]:]
        if self._ends_in_quote:
            self._quote_verses.add(self.vno)
        self.history = [x for x in earlier if self.vno - x.verse < self.lookback]
        self.vno += 1
        return new, decisions


def common_words(texts) -> set:
    """Words that occur in lowercase somewhere: a capitalized form of these is not a proper name."""
    out = set()
    for t in texts:
        out.update(re.findall(r"\b[a-z][a-z’']*", t))
    return out | {re.sub(r"[’']s?$", "", w) for w in out}


# --------------------------------------------------------------------------- review output
REVIEW_SAMPLES = [
    # OT
    "Ge 1:27", "Ge 2:3", "Ge 4:8", "Ge 22:9", "Ex 15:2", "De 31:3", "1Sa 15:35", "Job 22:13", "Ps 23:2", "Ps 23:3",
    "Ps 46:9", "Ps 91:2", "Ps 103:9", "Ps 107:13", "Isa 40:10", "Isa 53:5", "Isa 53:7", "Eze 17:19", "Jer 20:13",
    "Mic 7:19",
    # Gospels
    "Mt 3:16", "Mt 8:3", "Mt 8:7", "Mt 14:31", "Mt 24:31", "Mr 1:41", "Mr 5:32", "Lu 4:41", "Lu 8:50", "Lu 22:67",
    "Joh 1:3", "Joh 1:18", "Joh 3:16", "Joh 3:17", "Joh 9:4", "Joh 13:25", "Joh 14:16", "Joh 14:17", "Joh 16:13",
    # rest of the NT
    "Ro 6:9", "Heb 4:8", "1Jo 2:22", "Re 17:14",
]


def _csv_cell(s):
    s = str(s if s is not None else "")
    return '"' + s.replace('"', '""') + '"' if any(c in s for c in ',"\n') else s


def write_review(decisions, prefix, book_order, samples=None):
    """Write PREFIX.md (summary + samples) and PREFIX.csv (every change and every ambiguous case)."""
    prefix = Path(prefix)
    if prefix.suffix in (".md", ".csv"):
        prefix = prefix.with_suffix("")
    md_path, csv_path = prefix.with_suffix(".md"), prefix.with_suffix(".csv")
    changed = [d for d in decisions if d["status"] == "include" and not d["already"]]
    already = [d for d in decisions if d["status"] == "include" and d["already"]]
    ambiguous = [d for d in decisions if d["status"] != "include" and d["kind"] in ("ambiguous", "other")]
    overrides = [d for d in decisions if d["reason"].startswith("override")]
    by_ref = {}
    for d in decisions:
        by_ref.setdefault(d["ref"], []).append(d)

    rows = ["ref,word,occurrence,status,referent,confidence,reason,before,after"]
    for d in decisions:
        if d in changed or d in already or d in ambiguous or d in overrides:
            status = ("changed" if d in changed else "already marked" if d in already
                      else "excluded by override" if d["status"] == "exclude" else "ambiguous (unchanged)")
            rows.append(",".join(_csv_cell(x) for x in (d["ref"], d["word"], d["occurrence"], status, d["referent"],
                                                       d["confidence"], d["reason"], d["before"], d["after"])))
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def count(ds, key):
        out = {}
        for d in ds:
            out[key(d)] = out.get(key(d), 0) + 1
        return out

    by_ref_cat = count(changed, lambda d: d["referent"] or "?")
    by_conf = count(changed, lambda d: d["confidence"])
    by_word = count(changed, lambda d: d["word"].lower())
    by_book = count(changed, lambda d: d["ref"].split()[0])
    amb_book = count(ambiguous, lambda d: d["ref"].split()[0])
    total = sum(1 for d in decisions)
    lines = [
        "# Divine pronouns review",
        "",
        "`he` / `him` that refer to GOD (the LORD, GOD, the Father), JESUS or the Holy Spirit are written",
        "`He[JESUS]` / `Him[JESUS]`. `his` and `himself` are left as they are. Detection is a heuristic tuned for",
        "precision: unclear cases are left unchanged and listed as ambiguous. Fix any verse with a row in",
        "`divine_pronouns.tsv` (`ref`, `word`, `occurrence`, `include`/`exclude`).",
        "",
        f"- he/him in the text: **{total}**",
        f"- changed to He[JESUS] / Him[JESUS]: **{len(changed)}** "
        f"(he {by_word.get('he', 0)}, him {by_word.get('him', 0)}; confidence high {by_conf.get('high', 0)}, "
        f"medium {by_conf.get('medium', 0)})",
        f"- already carried [JESUS] from jesus_types.tsv (now capitalized): **{len(already)}**",
        f"- ambiguous, left unchanged: **{len(ambiguous)}**",
        f"- decided by divine_pronouns.tsv overrides: **{len(overrides)}**",
        "",
        "## By referent",
        "",
        "| Referent | Changed |",
        "|----------|---------|",
    ]
    for k, v in sorted(by_ref_cat.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    lines += ["", "`LORD (NT)` = \"the Lord\" in the New Testament (JESUS or the Father); `override` = forced by",
              "divine_pronouns.tsv.", "", "## By book", "", "| Book | Changed | Ambiguous |", "|------|---------|-----------|"]
    for b in book_order:
        if by_book.get(b) or amb_book.get(b):
            lines.append(f"| {b} | {by_book.get(b, 0)} | {amb_book.get(b, 0)} |")
    lines += ["", "## Sample verses (before / after)", ""]
    for ref in (samples or REVIEW_SAMPLES):
        ds = by_ref.get(ref)
        if not ds:
            continue
        notes = "; ".join(f"{d['word']}#{d['occurrence']}: "
                          f"{'CHANGED' if d in changed else 'kept'} ({d['referent'] or '-'}, {d['reason']})"
                          for d in ds)
        lines += [f"**{ref}**", "", f"- before: {ds[0]['before']}", f"- after: {ds[0]['after']}",
                  f"- why: {notes}", ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, csv_path
