#!/usr/bin/env python3
"""Jesus-centric KJV processor. See README for rules.
Processes public-domain KJV text: modernizes archaic forms, capitalizes LORD/GOD, uppercases JESUS, and adds [JESUS] markers.
"""
import argparse, json, re, sys
from pathlib import Path

MODERNIZATION_RULES = [
    (re.compile(r"\bthee\b", re.I), "you"),
    (re.compile(r"\bthou\b", re.I), "you"),
    (re.compile(r"\bthy\b", re.I), "your"),
    (re.compile(r"\bthine\b", re.I), "yours"),
    (re.compile(r"\bye\b", re.I), "you"),
    (re.compile(r"\bhath\b", re.I), "has"),
    (re.compile(r"\bdoth\b", re.I), "does"),
    (re.compile(r"\bsaith\b", re.I), "says"),
    (re.compile(r"\bbelieveth\b", re.I), "believes"),
    (re.compile(r"\bmaketh\b", re.I), "makes"),
    (re.compile(r"\bleadeth\b", re.I), "leads"),
    (re.compile(r"\brestoreth\b", re.I), "restores"),
    (re.compile(r"\bgoeth\b", re.I), "goes"),
    (re.compile(r"\bcometh\b", re.I), "comes"),
    (re.compile(r"\bsuffer\b", re.I), "let"),
    (re.compile(r"\bconversation\b", re.I), "conduct"),
    (re.compile(r"\bprevent\b", re.I), "precede"),
    (re.compile(r"\bcharity\b", re.I), "love"),
    (re.compile(r"\bverily\b", re.I), "truly"),
    (re.compile(r"\bwhosoever\b", re.I), "whoever"),
    (re.compile(r"\bwhoso\b", re.I), "whoever"),
    # -adeth forms
    (re.compile(r"\bspreadeth\b", re.I), "spreads"),
    (re.compile(r"\btreadeth\b", re.I), "treads"),
    (re.compile(r"\bfadeth\b", re.I), "fades"),
    (re.compile(r"\breadeth\b", re.I), "reads"),
    (re.compile(r"\bpleadeth\b", re.I), "pleads"),
    (re.compile(r"\bpersuadeth\b", re.I), "persuades"),
    (re.compile(r"\bloadeth\b", re.I), "loads"),
    (re.compile(r"\bladeth\b", re.I), "lades"),
    # second-person and modal archaic forms
    (re.compile(r"\bshalt\b", re.I), "shall"),
    (re.compile(r"\bhast\b", re.I), "have"),
    (re.compile(r"\bart\b", re.I), "are"),
    (re.compile(r"\bwilt\b", re.I), "will"),
    (re.compile(r"\bdidst\b", re.I), "did"),
    (re.compile(r"\bmayest\b", re.I), "may"),
    (re.compile(r"\bshouldest\b", re.I), "should"),
    (re.compile(r"\bwast\b", re.I), "were"),
    (re.compile(r"\bknowest\b", re.I), "know"),
    (re.compile(r"\bdoest\b", re.I), "do"),
    (re.compile(r"\bcanst\b", re.I), "can"),
    (re.compile(r"\bwouldest\b", re.I), "would"),
    (re.compile(r"\blivest\b", re.I), "live"),
    # -eth verb forms
    (re.compile(r"\bgiveth\b", re.I), "gives"),
    (re.compile(r"\bknoweth\b", re.I), "knows"),
    (re.compile(r"\bliveth\b", re.I), "lives"),
    (re.compile(r"\bdoeth\b", re.I), "does"),
    (re.compile(r"\bbringeth\b", re.I), "brings"),
    (re.compile(r"\btaketh\b", re.I), "takes"),
    (re.compile(r"\bspeaketh\b", re.I), "speaks"),
    (re.compile(r"\bloveth\b", re.I), "loves"),
    (re.compile(r"\bdwelleth\b", re.I), "dwells"),
    (re.compile(r"\beateth\b", re.I), "eats"),
    (re.compile(r"\bseeth\b", re.I), "sees"),
    (re.compile(r"\bheareth\b", re.I), "hears"),
    (re.compile(r"\bkeepeth\b", re.I), "keeps"),
    (re.compile(r"\bsitteth\b", re.I), "sits"),
    (re.compile(r"\bwalketh\b", re.I), "walks"),
    (re.compile(r"\bstandeth\b", re.I), "stands"),
    (re.compile(r"\babideth\b", re.I), "abides"),
    (re.compile(r"\brejoiceth\b", re.I), "rejoices"),
    (re.compile(r"\bdrinketh\b", re.I), "drinks"),
    (re.compile(r"\brunneth\b", re.I), "runs"),
    (re.compile(r"\bthinketh\b", re.I), "thinks"),
    (re.compile(r"\bhopeth\b", re.I), "hopes"),
]

LORD_GOD_PATTERN = re.compile(r"\b(Lord|LORD|God|GOD)\b")

def modernize_line(line):
    for p, r in MODERNIZATION_RULES:
        line = p.sub(r, line)
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
