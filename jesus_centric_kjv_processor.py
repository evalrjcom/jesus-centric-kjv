#!/usr/bin/env python3
"""Jesus-centric KJV processor. See README for rules.
Processes public-domain KJV text: modernizes archaic forms, capitalizes LORD/GOD, uppercases JESUS, and adds [JESUS] markers.
"""
import argparse, json, re, sys
from pathlib import Path


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
    "shalt": "shall", "hast": "have", "art": "are", "wilt": "will",
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
    "suffer": "let", "conversation": "conduct", "prevent": "precede",
    "charity": "love",
    # location
    "thence": "from there", "whither": "where", "thither": "there",
    "whence": "from where", "hither": "here",
    "thereof": "of it", "wherein": "in which", "wherefore": "therefore",
    "wherewith": "with which", "whereof": "of which", "thereon": "on it",
    "whereby": "by which", "whereunto": "to which",
    # strong verbs
    "smote": "struck", "dwelt": "lived", "begat": "fathered", "bare": "bore",
    "wrought": "worked", "brake": "broke", "smitten": "struck", "rent": "tore",
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
    # second-person -est forms
    "seest": "see", "lest": "lest", "standest": "stand", "liest": "lie",
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

def modernize_line(line):
    # Pass 1: explicit replacements (longest first)
    for old, new in SORTED_REPLACEMENTS:
        line = make_pattern(old).sub(new, line)
    # Pass 2: catch remaining -eth verbs (simple heuristic)
    def eth_to_s(m):
        w = m.group(0)
        base = w[:-3]  # strip eth
        # avoid turning short words into nonsense
        if len(base) < 3:
            return w
        # common consonant doubling already handled by explicit rules
        return base + "s"
    line = re.sub(r"\b[a-z]{4,}eth\b", eth_to_s, line, flags=re.I)
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

def process_file(inp, outp):
    with open(inp, encoding="utf-8", errors="replace") as fin, open(outp, "w", encoding="utf-8") as fout:
        for raw in fin:
            line = raw.rstrip("\n")
            if not line.strip():
                fout.write("\n")
                continue
            line = modernize_line(line)
            line = capitalize_divine(line)
            line = uppercase_jesus(line)
            line = add_jesus_marker(line)
            fout.write(line + "\n")
    print(f"Processed {inp} -> {outp}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    try:
        process_file(args.input, args.output)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
