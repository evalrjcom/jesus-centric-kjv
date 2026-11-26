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

# ---------------------------------------------------------------------------
# Pure Cambridge Edition (PCE) source
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_PCE_PATH = REPO_ROOT / "docs" / "TEXT-PCE.txt"
PCE_RAW_URL = "https://raw.githubusercontent.com/evalrjcom/jesus-centric-kjv/main/docs/TEXT-PCE.txt"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "jesus_centric_kjv_all66.txt"

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

# Word/phrase replacements (longer phrases first)
REPLACEMENTS = {
    # phrases first
    "from hence": "from here",
    "from thence": "from there",
    "from whence": "from where",
    "it came to pass": "it happened",
    "and it came to pass": "and it happened",
    # pronouns
    "thee": "you", "thou": "you", "thy": "your", "thine": "yours", "ye": "you",
    "thyself": "yourself",
    # modals / second person
    "shalt": "shall", "hast": "have", "wilt": "will",
    "didst": "did", "mayest": "may", "shouldest": "should", "wast": "were",
    "knowest": "know", "doest": "do", "canst": "can", "wouldest": "would",
    "livest": "live", "preservest": "preserve", "smotest": "struck",
    # common archaic
    "hath": "has", "doth": "does", "saith": "says", "unto": "to",
    "behold": "look", "yea": "yes", "lo": "look", "hearken": "listen",
    "nigh": "near", "howbeit": "however", "raiment": "clothing",
    "fowls": "birds", "forasmuch": "since", "straightway": "immediately",
    "peradventure": "perhaps", "betwixt": "between", "wist": "knew",
    "holden": "held", "ere": "before", "whilst": "while", "wot": "know",
    "durst": "dared", "bade": "told", "cloke": "cloak", "holpen": "helped",
    "verily": "truly", "whosoever": "whoever", "whoso": "whoever",
    "suffer": "let", "conversation": "conduct",
    "charity": "love",
    # location
    "thence": "from there", "whither": "where", "thither": "there",
    "whence": "from where", "hither": "here",
    "thereof": "of it", "wherein": "in which", "wherefore": "therefore",
    "wherewith": "with which", "whereof": "of which", "thereon": "on it",
    "whereby": "by which", "whereunto": "to which",
    # strong verbs
    "smote": "struck", "dwelt": "lived", "begat": "fathered", "bareth": "bares",
    "wrought": "worked", "brake": "broke", "smitten": "struck",
    "builded": "built", "gat": "got", "clave": "clung", "drave": "drove",
    "spake": "spoke", "sware": "swore",
    # -eth forms (sample; full list below)
    "believeth": "believes", "maketh": "makes", "leadeth": "leads",
    "restoreth": "restores", "goeth": "goes", "cometh": "comes",
    "spreadeth": "spreads", "treadeth": "treads", "fadeth": "fades",
    "readeth": "reads", "pleadeth": "pleads", "persuadeth": "persuades",
    "loadeth": "loads", "ladeth": "lades", "giveth": "gives",
    "knoweth": "knows", "liveth": "lives", "doeth": "does",
    "bringeth": "brings", "taketh": "takes", "speaketh": "speaks",
    "loveth": "loves", "dwelleth": "dwells", "eateth": "eats",
    "seeth": "sees", "heareth": "hears", "keepeth": "keeps",
    "sitteth": "sits", "walketh": "walks", "standeth": "stands",
    "abideth": "abides", "rejoiceth": "rejoices", "drinketh": "drinks",
    "runneth": "runs", "thinketh": "thinks", "hopeth": "hopes",
    "prophesieth": "prophesies", "slayeth": "slays", "proceedeth": "proceeds",
    "feedeth": "feeds", "needeth": "needs", "rideth": "rides",
    "provideth": "provides", "hideth": "hides", "divideth": "divides",
    "slideth": "slides", "upbraideth": "reproaches",
    "creepeth": "creeps", "escapeth": "escapes", "lappeth": "laps",
    "boweth": "bows", "helpeth": "helps", "worshippeth": "worships",
    "addeth": "adds", "clappeth": "claps", "multiplieth": "multiplies",
    "encampeth": "encamps", "delivereth": "delivers", "slippeth": "slips",
    "sheweth": "shows", "floweth": "flows", "followeth": "follows",
    "overthroweth": "overthrows", "draweth": "draws", "bloweth": "blows",
    "soweth": "sows", "voweth": "vows", "sacrificeth": "sacrifices",
    "alloweth": "allows", "groweth": "grows",
    "moveth": "moves", "lieth": "lies", "openeth": "opens", "asketh": "asks",
    "fighteth": "fights", "healeth": "heals", "remaineth": "remains",
    "lighteth": "lights", "passeth": "passes", "covereth": "covers",
    "toucheth": "touches", "sprinkleth": "sprinkles", "offereth": "offers",
    "killeth": "kills", "dieth": "dies", "causeth": "causes",
    "separateth": "separates", "sojourneth": "sojourns", "sinneth": "sins",
    "purifieth": "purifies", "defileth": "defiles", "chasteneth": "chastens",
    "destroyeth": "destroys", "regardeth": "regards", "careth": "cares",
    "lusteth": "lusts", "desireth": "desires", "lendeth": "lends",
    "blesseth": "blesses", "hateth": "hates", "breatheth": "breathes",
    "pertaineth": "pertains", "setteth": "sets", "putteth": "puts",
    "flieth": "flies", "turneth": "turns", "beareth": "bears",
    "meaneth": "means", "reigneth": "reigns", "seemeth": "seems",
    "saveth": "saves", "repenteth": "repents", "pisseth": "urinates",
    "lighteneth": "lightens", "presseth": "presses",
    # remaining -eth verbs: explicit 3rd-person forms, checked by hand (alphabetical).
    # Proper names (Nazareth, Japheth...), Psalm 119 letters (BETH, CHETH, DALETH, TETH), -ieth ordinals and teeth are left out on purpose.
    "abhorreth": "abhors", "aboundeth": "abounds", "accepteth": "accepts", "accuseth": "accuses",
    "acknowledgeth": "acknowledges", "adorneth": "adorns", "advantageth": "advantages",
    "affecteth": "affects", "agreeth": "agrees", "aileth": "ails", "altereth": "alters",
    "answereth": "answers", "appeaseth": "appeases", "appertaineth": "appertains", "appointeth": "appoints",
    "approacheth": "approaches", "approveth": "approves", "ariseth": "arises", "ascendeth": "ascends",
    "availeth": "avails", "avengeth": "avenges", "awaketh": "awakes", "backbiteth": "backbites",
    "baketh": "bakes", "baptizeth": "baptizes", "beateth": "beats", "becometh": "becomes",
    "befalleth": "befalls", "begetteth": "begets", "behaveth": "behaves", "beholdeth": "beholds",
    "belongeth": "belongs", "bendeth": "bends", "bereaveth": "bereaves", "betrayeth": "betrays",
    "bewaileth": "bewails", "bewrayeth": "bewrays", "biddeth": "bids", "bindeth": "binds", "biteth": "bites",
    "blasphemeth": "blasphemes", "blindeth": "blinds", "blotteth": "blots", "boasteth": "boasts",
    "borroweth": "borrows", "breaketh": "breaks", "bridleth": "bridles", "buildeth": "builds",
    "burneth": "burns", "buyeth": "buys", "calleth": "calls", "calveth": "calves", "carrieth": "carries",
    "casteth": "casts", "catcheth": "catches", "ceaseth": "ceases", "challengeth": "challenges",
    "chanceth": "chances", "changeth": "changes", "chaseth": "chases", "chastiseth": "chastises",
    "cheereth": "cheers", "cherisheth": "cherishes", "cheweth": "chews", "chooseth": "chooses",
    "cleanseth": "cleanses", "cleaveth": "cleaves", "climbeth": "climbs", "comforteth": "comforts",
    "commandeth": "commands", "commendeth": "commends", "committeth": "commits", "compasseth": "compasses",
    "compoundeth": "compounds", "concealeth": "conceals", "concerneth": "concerns", "condemneth": "condemns",
    "confesseth": "confesses", "confirmeth": "confirms", "considereth": "considers", "consisteth": "consists",
    "constraineth": "constrains", "consulteth": "consults", "consumeth": "consumes", "containeth": "contains",
    "contemneth": "contemns", "contendeth": "contends", "continueth": "continues", "converteth": "converts",
    "convinceth": "convinces", "correcteth": "corrects", "corrupteth": "corrupts", "coucheth": "couches",
    "counteth": "counts", "coupleth": "couples", "coveteth": "covets", "craveth": "craves",
    "createth": "creates", "crieth": "cries", "croucheth": "crouches", "crowneth": "crowns",
    "cumbereth": "cumbers", "curseth": "curses", "cutteth": "cuts", "darkeneth": "darkens",
    "dasheth": "dashes", "dealeth": "deals", "decayeth": "decays", "deceiveth": "deceives",
    "decketh": "decks", "declareth": "declares", "declineth": "declines", "deferreth": "defers",
    "delayeth": "delays", "delighteth": "delights", "denieth": "denies", "departeth": "departs",
    "descendeth": "descends", "describeth": "describes", "deserveth": "deserves", "despiseth": "despises",
    "deviseth": "devises", "devoureth": "devours", "differeth": "differs", "diggeth": "digs",
    "dippeth": "dips", "directeth": "directs", "disannulleth": "disannuls", "disappointeth": "disappoints",
    "discerneth": "discerns", "discovereth": "discovers", "disguiseth": "disguises",
    "dishonoureth": "dishonours", "dissembleth": "dissembles", "distributeth": "distributes",
    "divineth": "divines", "doubteth": "doubts", "dreameth": "dreams", "dresseth": "dresses",
    "drieth": "dries", "driveth": "drives", "droppeth": "drops", "dureth": "dures", "earneth": "earns",
    "edifieth": "edifies", "emboldeneth": "emboldens", "endeth": "ends", "endureth": "endures",
    "enlargeth": "enlarges", "entangleth": "entangles", "entereth": "enters", "enticeth": "entices",
    "entreateth": "entreats", "envieth": "envies", "erreth": "errs", "escheweth": "eschews",
    "establisheth": "establishes", "exacteth": "exacts", "exalteth": "exalts", "exceedeth": "exceeds",
    "excelleth": "excels", "executeth": "executes", "exerciseth": "exercises", "exhorteth": "exhorts",
    "extendeth": "extends", "faileth": "fails", "fainteth": "faints", "falleth": "falls",
    "fashioneth": "fashions", "favoureth": "favours", "feareth": "fears", "fetcheth": "fetches",
    "filleth": "fills", "findeth": "finds", "fitteth": "fits", "flattereth": "flatters", "fleeth": "flees",
    "flourisheth": "flourishes", "fluttereth": "flutters", "foameth": "foams", "foldeth": "folds",
    "forbeareth": "forbears", "forbiddeth": "forbids", "foreseeth": "foresees", "forgetteth": "forgets",
    "forgiveth": "forgives", "formeth": "forms", "forsaketh": "forsakes", "frameth": "frames",
    "fretteth": "frets", "frustrateth": "frustrates", "gathereth": "gathers", "gendereth": "genders",
    "getteth": "gets", "girdeth": "girds", "glorieth": "glories", "glorifieth": "glorifies",
    "gnasheth": "gnashes", "graveth": "graves", "greeteth": "greets", "grieveth": "grieves",
    "groaneth": "groans", "gropeth": "gropes", "halteth": "halts", "handleth": "handles", "hangeth": "hangs",
    "happeneth": "happens", "hardeneth": "hardens", "hasteneth": "hastens", "hasteth": "hastes",
    "hatcheth": "hatches", "heapeth": "heaps", "hearkeneth": "listens", "heweth": "hews",
    "hindereth": "hinders", "holdeth": "holds", "humbleth": "humbles", "hunteth": "hunts", "hurleth": "hurls",
    "imagineth": "imagines", "imputeth": "imputes", "inclineth": "inclines", "increaseth": "increases",
    "inhabiteth": "inhabits", "inheriteth": "inherits", "intermeddleth": "intermeddles", "judgeth": "judges",
    "justifieth": "justifies", "kindleth": "kindles", "knocketh": "knocks", "laboureth": "labours",
    "lacketh": "lacks", "languisheth": "languishes", "laugheth": "laughs", "layeth": "lays",
    "leaneth": "leans", "leaveneth": "leavens", "leaveth": "leaves", "letteth": "lets", "licketh": "licks",
    "lifteth": "lifts", "liketh": "likes", "limiteth": "limits", "lingereth": "lingers", "listeth": "lists",
    "loatheth": "loathes", "lodgeth": "lodges", "longeth": "longs", "looketh": "looks", "looseth": "looses",
    "loseth": "loses", "lotheth": "lothes", "loweth": "lows", "marketh": "marks", "marrieth": "marries",
    "meddleth": "meddles", "meeteth": "meets", "melteth": "melts", "ministereth": "ministers",
    "mocketh": "mocks", "mourneth": "mourns", "mustereth": "musters", "nameth": "names",
    "nourisheth": "nourishes", "obeyeth": "obeys", "observeth": "observes", "obtaineth": "obtains",
    "occupieth": "occupies", "opposeth": "opposes", "oppresseth": "oppresses", "ordaineth": "ordains",
    "ordereth": "orders", "overcometh": "overcomes", "overfloweth": "overflows", "overtaketh": "overtakes",
    "overturneth": "overturns", "oweth": "owes", "owneth": "owns", "pacifieth": "pacifies",
    "panteth": "pants", "pardoneth": "pardons", "parteth": "parts", "paweth": "paws", "payeth": "pays",
    "perceiveth": "perceives", "performeth": "performs", "perisheth": "perishes", "perverteth": "perverts",
    "pierceth": "pierces", "pineth": "pines", "pitieth": "pities", "planteth": "plants", "playeth": "plays",
    "pleaseth": "pleases", "plotteth": "plots", "ploweth": "plows", "plucketh": "plucks",
    "pondereth": "ponders", "possesseth": "possesses", "poureth": "pours", "praiseth": "praises",
    "prayeth": "prays", "preacheth": "preaches", "prepareth": "prepares", "preserveth": "preserves",
    "prevaileth": "prevails", "proclaimeth": "proclaims", "procureth": "procures", "profaneth": "profanes",
    "profiteth": "profits", "prolongeth": "prolongs", "prospereth": "prospers", "proveth": "proves",
    "provoketh": "provokes", "publisheth": "publishes", "puffeth": "puffs", "purgeth": "purges",
    "purposeth": "purposes", "pursueth": "pursues", "quickeneth": "quickens", "quieteth": "quiets",
    "rageth": "rages", "raiseth": "raises", "rattleth": "rattles", "reacheth": "reaches", "reapeth": "reaps",
    "rebuketh": "rebukes", "receiveth": "receives", "reckoneth": "reckons", "redeemeth": "redeems",
    "refraineth": "refrains", "refresheth": "refreshes", "refuseth": "refuses", "rejecteth": "rejects",
    "relieveth": "relieves", "remembereth": "remembers", "removeth": "removes", "rendereth": "renders",
    "repayeth": "repays", "repeateth": "repeats", "reproacheth": "reproaches", "reproveth": "reproves",
    "requireth": "requires", "rescueth": "rescues", "reserveth": "reserves", "resisteth": "resists",
    "respecteth": "respects", "resteth": "rests", "retaineth": "retains", "returneth": "returns",
    "revealeth": "reveals", "revengeth": "revenges", "rewardeth": "rewards", "riseth": "rises",
    "roareth": "roars", "roasteth": "roasts", "robbeth": "robs", "rolleth": "rolls", "rusheth": "rushes",
    "saluteth": "salutes", "sanctifieth": "sanctifies", "satisfieth": "satisfies", "scaleth": "scales",
    "scattereth": "scatters", "scorneth": "scorns", "scourgeth": "scourges", "sealeth": "seals",
    "searcheth": "searches", "seduceth": "seduces", "seeketh": "seeks", "selleth": "sells",
    "sendeth": "sends", "serveth": "serves", "seweth": "sews", "shaketh": "shakes", "shameth": "shames",
    "sharpeneth": "sharpens", "sheddeth": "sheds", "shineth": "shines", "shooteth": "shoots",
    "shouteth": "shouts", "shutteth": "shuts", "sigheth": "sighs", "signifieth": "signifies",
    "singeth": "sings", "slandereth": "slanders", "sleepeth": "sleeps", "slumbereth": "slumbers",
    "smelleth": "smells", "smiteth": "smites", "smootheth": "smooths", "snuffeth": "snuffs",
    "sorroweth": "sorrows", "soundeth": "sounds", "spareth": "spares", "spendeth": "spends",
    "spoileth": "spoils", "springeth": "springs", "stablisheth": "stablishes", "staggereth": "staggers",
    "stayeth": "stays", "stealeth": "steals", "steppeth": "steps", "sticketh": "sticks", "stilleth": "stills",
    "stingeth": "stings", "stinketh": "stinks", "stirreth": "stirs", "stoopeth": "stoops",
    "stoppeth": "stops", "straiteneth": "straitens", "strengtheneth": "strengthens",
    "stretcheth": "stretches", "striketh": "strikes", "striveth": "strives", "studieth": "studies",
    "stumbleth": "stumbles", "subdueth": "subdues", "suffereth": "suffers", "sufficeth": "suffices",
    "supplieth": "supplies", "swalloweth": "swallows", "sweareth": "swears", "swimmeth": "swims",
    "talketh": "talks", "tarrieth": "tarries", "tasteth": "tastes", "teacheth": "teaches", "teareth": "tears",
    "telleth": "tells", "tempteth": "tempts", "tendeth": "tends", "thirsteth": "thirsts",
    "thresheth": "threshes", "thrusteth": "thrusts", "thundereth": "thunders", "tilleth": "tills",
    "transgresseth": "transgresses", "travaileth": "travails", "travelleth": "travels",
    "trembleth": "trembles", "trickleth": "trickles", "trieth": "tries", "troubleth": "troubles",
    "trusteth": "trusts", "uncovereth": "uncovers", "understandeth": "understands", "upholdeth": "upholds",
    "useth": "uses", "uttereth": "utters", "vanisheth": "vanishes", "vaunteth": "vaunts",
    "visiteth": "visits", "vomiteth": "vomits", "waiteth": "waits", "wakeneth": "wakens", "waketh": "wakes",
    "wandereth": "wanders", "wanteth": "wants", "warmeth": "warms", "warreth": "wars", "wasteth": "wastes",
    "watcheth": "watches", "watereth": "waters", "wavereth": "wavers", "waxeth": "waxes",
    "weakeneth": "weakens", "weareth": "wears", "wearieth": "wearies", "weepeth": "weeps",
    "weigheth": "weighs", "whirleth": "whirls", "willeth": "wills", "winketh": "winks", "winneth": "wins",
    "winnoweth": "winnows", "wipeth": "wipes", "withdraweth": "withdraws", "withereth": "withers",
    "withholdeth": "withholds", "witnesseth": "witnesses", "worketh": "works", "wotteth": "knows",
    "woundeth": "wounds", "writeth": "writes", "wrongeth": "wrongs", "yieldeth": "yields",
    # second-person -est forms
    "seest": "see", "standest": "stand", "liest": "lie",
    "goest": "go", "broughtest": "brought", "sayest": "say", "reapest": "reap",
    "layest": "lay", "stoodest": "stood", "puttest": "put", "succeedest": "succeed",
    "dwellest": "dwell", "bearest": "bear", "askest": "ask", "spakest": "spoke",
    "lodgest": "lodge", "sawest": "saw", "leddest": "led", "seekest": "seek",
    "swarest": "swore", "keepest": "keep", "comest": "come", "heardest": "heard",
    "madest": "made", "forgavest": "forgave", "tookest": "took", "takest": "take",
    "makest": "make", "trustest": "trust", "forgettest": "forget", "speakest": "speak",
    "holdest": "hold", "devourest": "devour", "callest": "call", "hearest": "hear",
    "destroyest": "destroy", "buildest": "build", "savourest": "savor",
    "lackest": "lack", "answerest": "answer", "teachest": "teach", "acceptest": "accept",
    # additional forms
    "testifieth": "testifies", "esteemeth": "esteems", "appeareth": "appears",
    "honoureth": "honors", "ruleth": "rules", "basest": "base",
    "thyself": "yourself", "bestead": "beset",
}

# Sort by length descending so phrases win over single words
SORTED_REPLACEMENTS = sorted(REPLACEMENTS.items(), key=lambda x: -len(x[0]))

# Boundary that treats punctuation as non-word
def make_pattern(word):
    return re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.I)

# Compiled once: with 700+ entries, compiling per line overflowed Python's regex cache (512) and made a
# full run take many minutes.
COMPILED_REPLACEMENTS = [(make_pattern(old), new) for old, new in SORTED_REPLACEMENTS]

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

def modernize_line(line):
    # Pass 1: explicit replacements (longest first), keeping the original word's capitalization
    for pattern, new in COMPILED_REPLACEMENTS:
        line = pattern.sub(lambda m, new=new: match_case(m.group(0), new), line)
    # The general "-eth -> -s" pass was removed: it mangled words such as compasseth -> "compasss".
    # Only -eth words listed explicitly in REPLACEMENTS are modernized; all others keep the KJV form.
    return line

def capitalize_divine(line):
    def repl(m):
        w = m.group(0)
        return w.upper() if w.lower() in ("lord", "god") else w
    return LORD_GOD_PATTERN.sub(repl, line)

def uppercase_jesus(line):
    return re.sub(r"\b[Jj]esus\b", "JESUS", line)

def add_jesus_marker(line):
    # Protect "JESUS CHRIST" so it is not marked as CHRIST[JESUS]
    placeholder = "__JESUS_CHRIST_PROTECTED__"
    line = re.sub(r"\bJESUS\s+CHRIST\b", placeholder, line, flags=re.I)

    terms = [r"\bWord\b", r"\bLamb\b", r"\bChrist\b", r"\bMessiah\b", r"\bSon of Man\b", r"\bSon of God\b"]
    def repl(m):
        t = m.group(0).upper()
        return t if t == "JESUS" else f"{t}[JESUS]"

    for term in terms:
        line = re.compile(term, re.I).sub(repl, line)

    # Restore protected phrase
    line = line.replace(placeholder, "JESUS CHRIST")
    return line

def process_line(line):
    line = modernize_line(line)
    line = capitalize_divine(line)
    line = uppercase_jesus(line)
    line = add_jesus_marker(line)
    return line


def _is_pce_file(path: Path) -> bool:
    with open(path, "rb") as f:
        head = decode_pce(f.read(4096)[:4000]) if path.stat().st_size else ""
    first = next((l for l in head.splitlines() if l.strip()), "")
    m = PCE_LINE.match(first)
    return bool(m and m.group(1) in BOOK_INDEX)


def process_file(inp, outp):
    """Legacy mode: process a plain 'HEADER / C:V: text' file line by line."""
    with open(inp, encoding="utf-8", errors="replace") as fin, open(outp, "w", encoding="utf-8", newline="\n") as fout:
        for raw in fin:
            line = raw.rstrip("\r\n")
            if not line.strip():
                fout.write("\n")
                continue
            fout.write(process_line(line) + "\n")
    print(f"Processed {inp} -> {outp}")


def process_pce(source, outp, italics="strip", titles_json=None, timeout=30.0):
    verses, origin = load_pce(source, timeout=timeout)
    print(f"Loaded PCE from {origin}: {EXPECTED_BOOKS} books, {EXPECTED_CHAPTERS} chapters, {len(verses)} verses")
    outp = Path(outp)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8", newline="\n") as fout:
        for line in pce_to_lines(verses, italics):
            # book headers pass through unchanged; verse lines get the full pipeline
            fout.write((line if not re.match(r"^\d+:\d+: ", line) else process_line(line)) + "\n")
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
    p.add_argument("--italics", choices=["strip", "keep", "html"], default="strip",
                   help="PCE [italic] supplied words: strip brackets (default), keep [ ], or wrap in <i></i>")
    p.add_argument("--titles-json", type=Path, help="also write Psalm titles / colophons (<<...>>) as JSON")
    p.add_argument("--timeout", type=float, default=30.0, help="download timeout in seconds (default 30)")
    args = p.parse_args(argv)
    if len(args.paths) > 2:
        p.error("expected at most two paths: [input] [output]")
    try:
        if len(args.paths) == 2:
            inp, outp = args.paths
            if args.source:
                p.error("give either an input path or --source, not both")
            if _is_pce_file(inp):
                process_pce(inp, outp, args.italics, args.titles_json, args.timeout)
            else:
                process_file(inp, outp)
        else:
            outp = args.paths[0] if args.paths else DEFAULT_OUTPUT
            process_pce(args.source, outp, args.italics, args.titles_json, args.timeout)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
