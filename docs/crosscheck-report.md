# KJV crosscheck: takelley1/plaintext-bible-kjv vs TEXT-PCE.txt

- Source repo: https://github.com/takelley1/plaintext-bible-kjv @ `0e8cc040bfb69f564e15ba93b2569b00e28420a8`
- Concatenated file: `KJV-takelley1-66books.txt` (4,335,934 bytes, 31,234 lines incl. trailing newline)
- TEXT-PCE.txt: 4,496,932 bytes (UTF-8, CRLF line endings)

## Summary

| | takelley1 | TEXT-PCE |
|---|---:|---:|
| Books | 66 | 66 |
| Chapters | 1,189 | 1,189 |
| Verses | 31,102 | 31,102 |

- Verses missing from takelley1 (present in PCE): **0** 
- Extra verses in takelley1 (absent from PCE): **0** 
- Books whose chapter/verse counts differ: none

- **Strict raw comparison** (exact string): 15,571 identical / 15,531 different.
- **Normalised comparison** (PCE `[italic]` brackets and `<<…>>` superscriptions/colophons removed, curly apostrophes → `'`, whitespace collapsed): 30,225 identical / 877 different (2.82%).

### Difference categories (normalised)

| Category | Verses |
|---|---:|
| identical | 30,225 |
| hyphenation/compounding | 558 |
| word substitution / spelling | 161 |
| punctuation-only | 69 |
| words added/missing | 58 |
| case-only | 28 |
| punctuation+hyphenation | 3 |

### Why the raw comparison differs

- 14,251 PCE verses contain `[ ]` italics (supplied-word) markers; takelley1 has none.
- 1,779 PCE verses use curly `’`; takelley1 uses straight `'`.
- 132 `<<…>>` blocks in 132 PCE verses (Psalm titles and epistle subscriptions/colophons, e.g. `<<THE END.>>`). takelley1 contains the text of these in 0 of those verses (i.e. it omits them).

## Most frequent word-level variants (takelley1 → PCE)

| takelley1 | PCE | Count |
|---|---|---:|
| enquire | inquire | 46 |
| Beer-sheba | Beersheba | 34 |
| enquired | inquired | 34 |
| Ben-hadad | Benhadad | 27 |
| Beth-shemesh | Bethshemesh | 21 |
| Obed-edom | Obededom | 20 |
| Ramoth-gilead | Ramothgilead | 19 |
| Kirjath-jearim | Kirjathjearim | 18 |
| Nebuzar-adan | Nebuzaradan | 15 |
| Abed-nego | Abednego | 15 |
| Beth-horon | Bethhoron | 14 |
| Jabesh-gilead | Jabeshgilead | 12 |
| Ish-bosheth | Ishbosheth | 12 |
| Padan-aram | Padanaram | 10 |
| Kadesh-barnea | Kadeshbarnea | 10 |
| Bath-sheba | Bathsheba | 10 |
| Rab-shakeh | Rabshakeh | 8 |
| LORD | Lord | 8 |
| ∅ | the | 7 |
| razor | rasor | 7 |
| Beth-aven | Bethaven | 7 |
| Kirjath-arba | Kirjatharba | 6 |
| Baal-peor | Baalpeor | 6 |
| En-gedi | Engedi | 6 |
| Beth-shean | Bethshean | 6 |
| Pahath-moab | Pahathmoab | 6 |
| Ebed-melech | Ebedmelech | 6 |
| Baal-hanan | Baalhanan | 5 |
| Kibroth-hattaavah | Kibrothhattaavah | 5 |
| Pi-hahiroth | Pihahiroth | 4 |
| Hazar-enan | Hazarenan | 4 |
| Beth-peor | Bethpeor | 4 |
| En-rogel | Enrogel | 4 |
| Kirjath-sepher | Kirjathsepher | 4 |
| Hazar-shual | Hazarshual | 4 |
| Beth-zur | Bethzur | 4 |
| Gath-rimmon | Gathrimmon | 4 |
| Chushan-rishathaim | Chushanrishathaim | 4 |
| Enquire | Inquire | 4 |
| Malchi-shua | Malchishua | 4 |

## Examples by category

### hyphenation/compounding (558)

- **Genesis 4:22** — `also bare [-Tubal-cain,-]{+Tubalcain,+} | sister of [-Tubal-cain-]{+Tubalcain+}`
- **Genesis 10:26** — `Sheleph, and [-Hazar-maveth,-]{+Hazarmaveth,+}`
- **Genesis 14:6** — `Seir, unto [-El-paran,-]{+Elparan,+}`
- **Genesis 16:14** — `was called [-Beer-lahai-roi;-]{+Beerlahairoi;+}`
- **Genesis 21:14** — `wilderness of [-Beer-sheba.-]{+Beersheba.+}`
- **Genesis 21:31** — `that place [-Beer-sheba;-]{+Beersheba;+}`
- **Genesis 21:32** — `covenant at [-Beer-sheba:-]{+Beersheba:+}`
- **Genesis 21:33** — `grove in [-Beer-sheba,-]{+Beersheba,+}`

### word substitution / spelling (161)

- **Genesis 14:13** — `brother of [-Eschol,-]{+Eshcol,+}`
- **Genesis 24:57** — `damsel, and [-enquire-]{+inquire+}`
- **Genesis 25:22** — `went to [-enquire-]{+inquire+}`
- **Genesis 26:14** — `flocks, and [-possessions-]{+possession+}`
- **Exodus 18:15** — `me to [-enquire-]{+inquire+}`
- **Exodus 39:43** — `behold, they [-have-]{+had+}`
- **Leviticus 17:8** — `burnt offering [-of-]{+or+}`
- **Leviticus 25:19** — `fruit, and [-he-]{+ye+}`

### punctuation-only (69)

- **Genesis 2:21** — `fall upon [-Adam-]{+Adam,+}`
- **Genesis 22:5** — `again to [-you,-]{+you.+}`
- **Genesis 24:42** — `which I [-go;-]{+go:+}`
- **Genesis 26:25** — `of the [-LORD-]{+LORD,+}`
- **Genesis 30:3** — `upon my [-knees-]{+knees,+}`
- **Genesis 36:28** — `Dishan are [-these:-]{+these;+}`
- **Genesis 38:28** — `came out [-first,-]{+first.+}`
- **Genesis 44:10** — `unto your [-words;-]{+words:+}`

### words added/missing (58)

- **Genesis 21:17** — `God called {+to+}`
- **Genesis 50:23** — `the son {+of+}`
- **Leviticus 8:16** — `inwards, and {+the+}`
- **Leviticus 13:2** — `scab, or [-a-]`
- **Deuteronomy 14:12** — `eagle, and {+the+}`
- **Joshua 6:23** — `and brought {+out+}`
- **Judges 19:23** — `went out {+unto them, and said+}`
- **Ruth 1:4** — `the other {+Ruth:+}`

### case-only (28)

- **Genesis 19:34** — `of our [-Father.-]{+father.+}`
- **Genesis 26:18** — `for the [-philistines-]{+Philistines+}`
- **Genesis 41:56** — `the earth: [-and-]{+And+}`
- **Numbers 7:52** — `…[-one-]{+One+}`
- **Deuteronomy 14:2** — `…[-for-]{+For+}`
- **1 Samuel 16:2** — `it, he [-Will-]{+will+}`
- **2 Samuel 3:22** — `And, [-Behold,-]{+behold,+}`
- **1 Kings 9:18** — `…[-and-]{+And+}`

### punctuation+hyphenation (3)

- **Genesis 14:7** — `came to [-En-mishpat,-]{+Enmishpat,+} | also the [-Amorites-]{+Amorites,+} | dwelt in [-Hazezon-tamar.-]{+Hazezontamar.+}`
- **Joshua 19:12** — `border of [-Chisloth-tabor,-]{+Chislothtabor,+} | out to [-daberath,-]{+Daberath,+}`
- **2 Kings 18:27** — `But [-Rab-shakeh-]{+Rabshakeh+} | piss with [-you.-]{+you?+}`

## Differing verses per book

| Book | Differing | Verses |
|---|---:|---:|
| Genesis | 57 | 1533 |
| Exodus | 7 | 1213 |
| Leviticus | 8 | 859 |
| Numbers | 36 | 1288 |
| Deuteronomy | 24 | 959 |
| Joshua | 89 | 658 |
| Judges | 42 | 618 |
| Ruth | 2 | 85 |
| 1 Samuel | 52 | 810 |
| 2 Samuel | 50 | 695 |
| 1 Kings | 56 | 816 |
| 2 Kings | 61 | 719 |
| 1 Chronicles | 80 | 942 |
| 2 Chronicles | 39 | 822 |
| Ezra | 13 | 280 |
| Nehemiah | 15 | 406 |
| Esther | 7 | 167 |
| Job | 10 | 1070 |
| Psalms | 46 | 2461 |
| Proverbs | 5 | 915 |
| Ecclesiastes | 1 | 222 |
| Song of Solomon | 3 | 117 |
| Isaiah | 19 | 1292 |
| Jeremiah | 44 | 1364 |
| Lamentations | 0 | 154 |
| Ezekiel | 32 | 1273 |
| Daniel | 20 | 357 |
| Hosea | 10 | 197 |
| Joel | 1 | 73 |
| Amos | 6 | 146 |
| Obadiah | 0 | 21 |
| Jonah | 0 | 48 |
| Micah | 2 | 105 |
| Nahum | 2 | 47 |
| Habakkuk | 0 | 56 |
| Zephaniah | 1 | 53 |
| Haggai | 0 | 38 |
| Zechariah | 7 | 211 |
| Malachi | 2 | 55 |
| Matthew | 4 | 1071 |
| Mark | 2 | 678 |
| Luke | 2 | 1151 |
| John | 3 | 879 |
| Acts | 11 | 1007 |
| Romans | 2 | 433 |
| 1 Corinthians | 1 | 437 |
| 2 Corinthians | 1 | 257 |
| Galatians | 0 | 149 |
| Ephesians | 0 | 155 |
| Philippians | 0 | 104 |
| Colossians | 0 | 95 |
| 1 Thessalonians | 0 | 89 |
| 2 Thessalonians | 0 | 47 |
| 1 Timothy | 0 | 113 |
| 2 Timothy | 0 | 83 |
| Titus | 0 | 46 |
| Philemon | 0 | 25 |
| Hebrews | 0 | 303 |
| James | 0 | 108 |
| 1 Peter | 1 | 105 |
| 2 Peter | 0 | 61 |
| 1 John | 1 | 105 |
| 2 John | 0 | 13 |
| 3 John | 0 | 14 |
| Jude | 0 | 25 |
| Revelation | 0 | 404 |

## Method

1. Cloned the default branch; used the 66 files `01-genesis.txt` … `66-revelation.txt` (numeric prefix = canonical order; README.md excluded). Each file already starts with an uppercase book header line (e.g. `GENESIS`, `FIRST SAMUEL`, `1 KINGS`), so no headers were added; files were joined verbatim with one blank line between books, LF line endings, UTF-8 (source is pure ASCII). Note: file 38 is spelled `38-zecharaiah.txt` in the repo; its header reads `ZECHARIAH`.
2. takelley1 lines `C:V: text` and PCE lines `Abbr C:V text` were parsed into (book, chapter, verse) → text; duplicates/unparseable lines abort the script.
3. Strict comparison = exact string equality. Normalised comparison removes PCE markup as listed above. Categories: case-only; punctuation-only (same words, different punctuation); hyphenation/compounding (only hyphen/space joins differ, e.g. `burnt-offering` vs `burnt offering`); punctuation+hyphenation; word substitution/spelling (same word count, ≥1 word differs); words added/missing (word count differs).
4. Word-level diffs use difflib on whitespace tokens: `[-takelley1-]{+PCE+}` with two words of leading context.

The report describes only what the two files show; it does not attribute either text to a specific printed edition.

## Notable verses (manually reviewed from the diffs CSV)

These look like text errors in takelley1, judged only by comparing the two files:
- **Ruth 1:4**: takelley1 drops the name: "the name of the other and they dwelled…". PCE has "the other Ruth: and they dwelled…".
- **Judges 19:23**: takelley1 drops "and said unto them,".
- **1 Chronicles 11:2**: takelley1 repeats "and thou shalt be ruler over my people Israel," twice.
- **Ezekiel 17:24**: takelley1 repeats the whole clause "I the LORD have brought down the high tree … to flourish:" twice.
- **Genesis 21:17** ("God called {+to+} Hagar"), **Genesis 50:23** ("the son {+of+}"), **Joshua 6:23** ("brought {+out+}"): takelley1 leaves out a word.
- Casing: takelley1 has "Father" (Gen 19:34), "philistines" (Gen 26:18) and "Will" (1 Sam 16:2) where PCE has father/Philistines/will. Its LORD/Lord/GOD casing also differs from PCE in about 15 verses (e.g. Isa 3:15, Dan 5:23, Ps 7:1, Ps 68:20). In 3 verses, takelley1 has "Spirit" where PCE has "spirit" (Acts 11:12, 11:28; 1 John 5:8).
- Systematic differences: takelley1 hyphenates compound proper names (Beer-sheba, Ben-hadad, Obed-edom…), which PCE writes as one word (558 verses). It uses "enquire/enquired" where PCE has "inquire/inquired" (about 80 places).
