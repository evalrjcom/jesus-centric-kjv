# Jesus-Centric KJV

Independent modernization and Jesus-centric markup of the public-domain King James Version.

## Features
- Lexical modernization of archaic language
- LORD / GOD in all caps
- Name Jesus forced to JESUS
- [JESUS] markers on configured titles and (contextually) pronouns
- GitHub Pages searchable viewer organized by books, with **JESUS**, **LORD**, and **GOD** highlighted in red
- Suggest-a-change button that opens a pre-filled Issue
- GitHub Action that regenerates the processed text on changes to the processor

## Usage
```bash
# Default: read docs/TEXT-PCE.txt, write docs/jesus_centric_kjv_all66.txt
python3 jesus_centric_kjv_processor.py

# Choose the output, or the PCE source (local path or URL)
python3 jesus_centric_kjv_processor.py out.txt
python3 jesus_centric_kjv_processor.py --source path/or/url/TEXT-PCE.txt out.txt

# Still supported: explicit input and output (a PCE file, or a legacy "BOOK / C:V: text" file)
python3 jesus_centric_kjv_processor.py input_kjv.txt output.txt
```

Options:
- `--italics strip|keep|html`: PCE marks translator-supplied words with `[ ]` (printed in italics). The default, `strip`, keeps the words and drops the brackets. `keep` leaves the brackets, which can be confused with `[JESUS]` markers. `html` wraps them in `<i>…</i>`, which the viewer renders as italics.
- `--titles-json FILE`: Psalm titles and epistle colophons (`<<…>>` in PCE) are kept out of the verse text. Use this to save them as JSON metadata.
- `--timeout SECONDS`: download timeout when the source is fetched from a URL (default 30).
- `--swaps PATH`: TSV of word swaps, one `old<TAB>new` pair per line (default: `swaps.tsv` next to the script). `#` comments and blank lines are allowed.
- `--write-replacements-md [PATH]`: regenerate `REPLACEMENTS.md` from the swaps file and exit.

## Word swaps
Lexical modernization rules live in `swaps.tsv` (one `old<TAB>new` pair per line; `#` comments and blank lines are allowed). You can edit them locally or in the GitHub file editor.

**Local:** edit `swaps.tsv`, regenerate the documentation table, then commit and push both files:

```bash
python3 jesus_centric_kjv_processor.py --write-replacements-md
```

**On GitHub:** edit only `swaps.tsv` in the browser and commit to `main`. CI regenerates `REPLACEMENTS.md` and the processed text, runs the tests, and commits any updates.

Context rules that are not simple word pairs (currently the verb `art` → `are`) stay in the Python script. The full table and the `art` rule are in `REPLACEMENTS.md`. These swaps are kept in a separate file until a final Bible translation version is settled.

If `docs/TEXT-PCE.txt` is missing, the script downloads it from
`https://raw.githubusercontent.com/evalrjcom/jesus-centric-kjv/main/docs/TEXT-PCE.txt`.
Every load is validated: 66 books, 1,189 chapters and 31,102 verses, in canonical order with no duplicates. The script exits with an error if any check fails.

Tests: `python3 -m pytest -q tests`

## Viewer (GitHub Pages)
The processed text is served from the `/docs` folder.

**To enable GitHub Pages:**
1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` / folder: `/docs`
4. Save

The site will be available at `https://evalrjcom.github.io/jesus-centric-kjv/`.

The GitHub Action (`.github/workflows/process-kjv.yml`) automatically:
- Regenerates `REPLACEMENTS.md` from `swaps.tsv`
- Runs the tests
- Reads the Pure Cambridge Edition text from `docs/TEXT-PCE.txt`
- Runs the processor
- Commits the updated `docs/jesus_centric_kjv_all66.txt` and `REPLACEMENTS.md` when they change (or on manual workflow run)
- Comments on new/edited issues

Trigger the workflow manually from the Actions tab if you want to regenerate the text immediately.

## Source text and attribution
The source text is the **Pure Cambridge Edition (PCE)** of the King James Bible, from
[Bible Protector](https://www.bibleprotector.com). The repo copy is `docs/TEXT-PCE.txt` (the original Windows-1252 file, also in `docs/TEXT-PCE.zip`).
It is used as published: its spelling, punctuation and curly apostrophes are kept. Only the modernization and markup rules above are applied.
Thanks to bibleprotector.com for preparing and distributing the PCE text.

Earlier versions used the takelley1/plaintext-bible-kjv files. `docs/crosscheck-report.md` compares that text with PCE.
