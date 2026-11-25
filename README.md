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
python3 jesus_centric_kjv_processor.py input_kjv.txt output.txt
```

## Viewer (GitHub Pages)
The processed text is served from the `/docs` folder.

**To enable GitHub Pages:**
1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` / folder: `/docs`
4. Save

The site will be available at `https://evalrjcom.github.io/jesus-centric-kjv/`.

The GitHub Action (`.github/workflows/process-kjv.yml`) automatically:
- Downloads a clean public-domain KJV source
- Runs the processor
- Commits the updated `docs/jesus_centric_kjv_all66.txt` when the processor changes (or on manual workflow run)
- Comments on new/edited issues

Trigger the workflow manually from the Actions tab if you want to regenerate the text immediately.

Source text: public-domain KJV (via structured plaintext books).
