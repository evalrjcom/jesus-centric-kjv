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
    (re.compile(r"\bovercometh\b", re.I), "overcomes"),
    (re.compile(r"\bwalketh\b", re.I), "walks"),
    (re.compile(r"\bstandeth\b", re.I), "stands"),
    (re.compile(r"\babideth\b", re.I), "abides"),
    (re.compile(r"\brejoiceth\b", re.I), "rejoices"),
    (re.compile(r"\bdrinketh\b", re.I), "drinks"),
    (re.compile(r"\brunneth\b", re.I), "runs"),
    (re.compile(r"\bthinketh\b", re.I), "thinks"),
    (re.compile(r"\bhopeth\b", re.I), "hopes"),
    # additional archaic forms
    (re.compile(r"\bspake\b", re.I), "spoke"),
    (re.compile(r"\bsware\b", re.I), "swore"),
    (re.compile(r"\bfrom hence\b", re.I), "from here"),
    # strong verbs / past forms
    (re.compile(r"\bsmote\b", re.I), "struck"),
    (re.compile(r"\bdwelt\b", re.I), "lived"),
    (re.compile(r"\bbegat\b", re.I), "fathered"),
    (re.compile(r"\bbare\b", re.I), "bore"),
    (re.compile(r"\bwrought\b", re.I), "worked"),
    (re.compile(r"\bbrake\b", re.I), "broke"),
    (re.compile(r"\bsmitten\b", re.I), "struck"),
    (re.compile(r"\brent\b", re.I), "tore"),
    (re.compile(r"\bbuilded\b", re.I), "built"),
    (re.compile(r"\bgat\b", re.I), "got"),
    (re.compile(r"\bclave\b", re.I), "clung"),
    (re.compile(r"\bdrave\b", re.I), "drove"),
    # location / direction
    (re.compile(r"\bfrom thence\b", re.I), "from there"),
    (re.compile(r"\bfrom whence\b", re.I), "from where"),
    (re.compile(r"\bthence\b", re.I), "from there"),
    (re.compile(r"\bwhither\b", re.I), "where"),
    (re.compile(r"\bthither\b", re.I), "there"),
    (re.compile(r"\bwhence\b", re.I), "from where"),
    (re.compile(r"\bhither\b", re.I), "here"),
    # compounds
    (re.compile(r"\bthereof\b", re.I), "of it"),
    (re.compile(r"\bwherein\b", re.I), "in which"),
    (re.compile(r"\bwherefore\b", re.I), "therefore"),
    (re.compile(r"\bwherewith\b", re.I), "with which"),
    (re.compile(r"\bwhereof\b", re.I), "of which"),
    (re.compile(r"\bthereon\b", re.I), "on it"),
    (re.compile(r"\bwhereby\b", re.I), "by which"),
    (re.compile(r"\bwhereunto\b", re.I), "to which"),
    # other common archaic
    (re.compile(r"\bunto\b", re.I), "to"),
    (re.compile(r"\bbehold\b", re.I), "look"),
    (re.compile(r"\byea\b", re.I), "yes"),
    (re.compile(r"\blo\b", re.I), "look"),
    (re.compile(r"\bhearken\b", re.I), "listen"),
    (re.compile(r"\bnigh\b", re.I), "near"),
    (re.compile(r"\bhowbeit\b", re.I), "however"),
    (re.compile(r"\braiment\b", re.I), "clothing"),
    (re.compile(r"\bfowls\b", re.I), "birds"),
    (re.compile(r"\bforasmuch\b", re.I), "since"),
    (re.compile(r"\bstraightway\b", re.I), "immediately"),
    (re.compile(r"\bperadventure\b", re.I), "perhaps"),
    (re.compile(r"\bbetwixt\b", re.I), "between"),
    (re.compile(r"\bwist\b", re.I), "knew"),
    (re.compile(r"\bholden\b", re.I), "held"),
    (re.compile(r"\bere\b", re.I), "before"),
    (re.compile(r"\bwhilst\b", re.I), "while"),
    (re.compile(r"\bwot\b", re.I), "know"),
    (re.compile(r"\bdurst\b", re.I), "dared"),
    (re.compile(r"\bbade\b", re.I), "told"),
    (re.compile(r"\bcloke\b", re.I), "cloak"),
    (re.compile(r"\bholpen\b", re.I), "helped"),
    # additional -eth / -est forms
    (re.compile(r"\bsmotest\b", re.I), "struck"),
    (re.compile(r"\bprophesieth\b", re.I), "prophesies"),
    (re.compile(r"\bslayeth\b", re.I), "slays"),
    (re.compile(r"\bproceedeth\b", re.I), "proceeds"),
    (re.compile(r"\bfeedeth\b", re.I), "feeds"),
    (re.compile(r"\bneedeth\b", re.I), "needs"),
    (re.compile(r"\brideth\b", re.I), "rides"),
    (re.compile(r"\bprovideth\b", re.I), "provides"),
    (re.compile(r"\bhideth\b", re.I), "hides"),
    (re.compile(r"\bdivideth\b", re.I), "divides"),
    (re.compile(r"\bslideth\b", re.I), "slides"),
    (re.compile(r"\bupbraideth\b", re.I), "reproaches"),
    # more -eth / -est forms
    (re.compile(r"\bcreepeth\b", re.I), "creeps"),
    (re.compile(r"\bescapeth\b", re.I), "escapes"),
    (re.compile(r"\blappeth\b", re.I), "laps"),
    (re.compile(r"\bboweth\b", re.I), "bows"),
    (re.compile(r"\bhelpeth\b", re.I), "helps"),
    (re.compile(r"\bworshippeth\b", re.I), "worships"),
    (re.compile(r"\bpreservest\b", re.I), "preserve"),
    (re.compile(r"\baddeth\b", re.I), "adds"),
    (re.compile(r"\bclappeth\b", re.I), "claps"),
    (re.compile(r"\bmultiplieth\b", re.I), "multiplies"),
    (re.compile(r"\bencampeth\b", re.I), "encamps"),
    (re.compile(r"\bdelivereth\b", re.I), "delivers"),
    (re.compile(r"\bslippeth\b", re.I), "slips"),
    (re.compile(r"\bsheweth\b", re.I), "shows"),
    (re.compile(r"\bfloweth\b", re.I), "flows"),
    (re.compile(r"\bfolloweth\b", re.I), "follows"),
    (re.compile(r"\boverthroweth\b", re.I), "overthrows"),
    (re.compile(r"\bdraweth\b", re.I), "draws"),
    (re.compile(r"\bbloweth\b", re.I), "blows"),
    (re.compile(r"\bsoweth\b", re.I), "sows"),
    (re.compile(r"\bvoweth\b", re.I), "vows"),
    (re.compile(r"\bsacrificeth\b", re.I), "sacrifices"),
    (re.compile(r"\balloweth\b", re.I), "allows"),
    (re.compile(r"\bgroweth\b", re.I), "grows"),
    # additional -eth forms
    (re.compile(r"\bmoveth\b", re.I), "moves"),
    (re.compile(r"\blieth\b", re.I), "lies"),
    (re.compile(r"\bopeneth\b", re.I), "opens"),
    (re.compile(r"\basketh\b", re.I), "asks"),
    (re.compile(r"\bfighteth\b", re.I), "fights"),
    (re.compile(r"\bhealeth\b", re.I), "heals"),
    (re.compile(r"\bremaineth\b", re.I), "remains"),
    (re.compile(r"\blighteth\b", re.I), "lights"),
    (re.compile(r"\bpasseth\b", re.I), "passes"),
    (re.compile(r"\bcovereth\b", re.I), "covers"),
    (re.compile(r"\btoucheth\b", re.I), "touches"),
    (re.compile(r"\bsprinkleth\b", re.I), "sprinkles"),
    (re.compile(r"\boffereth\b", re.I), "offers"),
    (re.compile(r"\bkilleth\b", re.I), "kills"),
    (re.compile(r"\bdieth\b", re.I), "dies"),
    (re.compile(r"\bcauseth\b", re.I), "causes"),
    (re.compile(r"\bseparateth\b", re.I), "separates"),
    (re.compile(r"\bsojourneth\b", re.I), "sojourns"),
    (re.compile(r"\bsinneth\b", re.I), "sins"),
    (re.compile(r"\bpurifieth\b", re.I), "purifies"),
    (re.compile(r"\bdefileth\b", re.I), "defiles"),
    (re.compile(r"\bchasteneth\b", re.I), "chastens"),
    (re.compile(r"\bdestroyeth\b", re.I), "destroys"),
    (re.compile(r"\bregardeth\b", re.I), "regards"),
    (re.compile(r"\bcareth\b", re.I), "cares"),
    (re.compile(r"\blusteth\b", re.I), "lusts"),
    (re.compile(r"\bdesireth\b", re.I), "desires"),
    (re.compile(r"\blendeth\b", re.I), "lends"),
    (re.compile(r"\bblesseth\b", re.I), "blesses"),
    (re.compile(r"\bhateth\b", re.I), "hates"),
    (re.compile(r"\bbreatheth\b", re.I), "breathes"),
    (re.compile(r"\bpertaineth\b", re.I), "pertains"),
    (re.compile(r"\bsetteth\b", re.I), "sets"),
    (re.compile(r"\bputteth\b", re.I), "puts"),
    (re.compile(r"\bflieth\b", re.I), "flies"),
    (re.compile(r"\bturneth\b", re.I), "turns"),
    (re.compile(r"\bbeareth\b", re.I), "bears"),
    (re.compile(r"\bmeaneth\b", re.I), "means"),
    (re.compile(r"\breigneth\b", re.I), "reigns"),
    (re.compile(r"\bseemeth\b", re.I), "seems"),
    (re.compile(r"\bsaveth\b", re.I), "saves"),
    (re.compile(r"\brepenteth\b", re.I), "repents"),
    (re.compile(r"\bpisseth\b", re.I), "urinates"),
    (re.compile(r"\blighteneth\b", re.I), "lightens"),
    (re.compile(r"\bpresseth\b", re.I), "presses"),
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
