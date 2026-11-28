# Jesus-type markers

Verses where the processor adds `[JESUS]` right after a word that points to Christ, taken from the
"books of the Bible reveal Christ" chart. The source of truth is `jesus_types.tsv`. This file is generated from it:

```bash
python3 jesus_centric_kjv_processor.py --write-types-md
```

The target is matched in the processed (modernized) verse. If it already carries `[JESUS]` from the
Word / Lamb / Christ / Son of Man / Son of God rules, nothing more is added.

Total: **69** (strong 35, moderate 17, weak 17)

| Book | Verse | Target | # | Match | Theme |
|------|-------|--------|---|-------|-------|
| Genesis | 3:15 | `her seed` | 1 | strong | The seed of the woman who will bruise the serpent's head. |
| Exodus | 12:5 | `Lamb` | 1 | strong | The Passover Lamb (already marked by the Lamb rule). |
| Exodus | 16:15 | `bread` | 1 | strong | The Manna (bread from heaven). |
| Exodus | 17:6 | `rock` | 2 | strong | The Rock giving the water of life in the wilderness (the smitten rock). |
| Leviticus | 21:10 | `high priest` | 1 | moderate | Our High Priest and Intercessor. |
| Numbers | 14:14 | `pillar of fire` | 1 | moderate | The Pillar of Fire leading us through the wilderness. |
| Deuteronomy | 18:15 | `Prophet` | 1 | strong | The Prophet who would be raised up like unto Moses. |
| Joshua | 5:14 | `captain` | 1 | strong | The Captain of our Salvation who is leading us into the Promised Land. |
| Judges | 11:27 | `Judge` | 1 | weak | Our Judge and Lawgiver who delivers us from our enemies. |
| Ruth | 4:14 | `kinsman` | 1 | strong | Our kinsman Redeemer, descendent of Boaz and Ruth. |
| 1 Samuel | 2:10 | `anointed` | 1 | strong | The true Prophet/Priest/King, anointed giant killer, and only eternal King of Kings. |
| 2 Samuel | 7:12 | `seed` | 1 | strong | Will be the reigning King after God's own heart that unites all Israel. |
| 1 Kings | 5:5 | `Your son` | 1 | moderate | The greater Solomon who is building the temple of God in us. |
| 2 Kings | 1:3 | `angel of the LORD` | 1 | weak | The greater Elijah who defeats all false prophets. |
| 1 Chronicles | 17:14 | `him` | 1 | strong | The spiritual counterpart of David's righteous reign. |
| 2 Chronicles | 15:3 | `priest` | 1 | weak | The Priest recording the history of the descendants of Judah and Israel. |
| Ezra | 7:6 | `scribe` | 1 | weak | The faithful Scribe who helps us rebuild broken down walls. |
| Nehemiah | 5:14 | `governor` | 1 | weak | Our Governor working to rebuild everything that is broken to finish God's temple. |
| Esther | 4:14 | `deliverance` | 1 | weak | He is working to keep the Antichrist from destroying God's people. |
| Job | 19:25 | `redeemer` | 1 | strong | The Redeemer who delivers the upright from suffering after they are tested. |
| Psalms | 23:1 | `shepherd` | 1 | strong | The Shepherd that leading us to green pastures to feed and protect us. |
| Proverbs | 8:12 | `wisdom` | 1 | strong | Our Wisdom to help us succeed in life. |
| Ecclesiastes | 1:1 | `Preacher` | 1 | weak | The Preacher who exposes human endeavors without God as vanity. |
| Song of Solomon | 5:10 | `beloved` | 1 | moderate | The Bridegroom seeking a bride who finally finds Him working in the harvest field. |
| Isaiah | 7:14 | `son` | 1 | strong | The Son of a virgin who comforts his people and judges the nations. |
| Jeremiah | 23:5 | `Branch` | 1 | moderate | The suffering Servant who warns us when we error and asks us to repent. |
| Lamentations | 1:12 | `my sorrow` | 1 | weak | The weeping Prophet who offers forgiveness and grace when we fail. |
| Ezekiel | 37:22 | `one king` | 1 | moderate | The Son of Man who breathes new life in Judah and Israel making them one again. |
| Daniel | 3:25 | `Son of God` | 1 | strong | He symbolizes the fourth Man in furnace (already marked by the Son of God rule). |
| Daniel | 7:13 | `Son of Man` | 1 | strong | ...who is coming back again in the clouds (already marked by the Son of Man rule). |
| Hosea | 3:2 | `I` | 1 | moderate | The faithful Husband who buys back his wife who has been unfaithful. |
| Joel | 2:32 | `name of the LORD` | 1 | weak | The one the Father uses to pour His Holy Spirit out upon all who would believe. |
| Amos | 9:11 | `I` | 1 | moderate | The One rebuilding David's dynasty and making all the crooked places straight. |
| Obadiah | 1:21 | `saviours` | 1 | moderate | He is the Deliverer on Mt. Zion and the Judge of the nations. |
| Jonah | 1:17 | `three days and three nights` | 1 | moderate | God's true Missionary to the Gentiles who spent three days and nights in the earth. |
| Micah | 5:2 | `ruler` | 1 | strong | The Ruler born in Bethlehem that causes nations to beat swords into plowshares. |
| Nahum | 1:2 | `GOD` | 1 | weak | The jealous Avenger of God's elect from their violent enemies. |
| Habakkuk | 2:14 | `glory` | 1 | weak | The One who fills the righteous with the knowledge of the glory of God. |
| Zephaniah | 3:15 | `king of Israel` | 1 | moderate | God's righteous King who saves the remnant and removes the disobedient. |
| Haggai | 2:7 | `desire of all nations` | 1 | strong | The Desire of all nations and the Restorer of the temples glory. |
| Zechariah | 9:9 | `King` | 1 | strong | The Savior who rode a donkey into Jerusalem and was crucified by His people. |
| Malachi | 4:2 | `Sun of righteousness` | 1 | strong | The Sun of Righteousness who has risen with healing in His wings. |
| Matthew | 16:16 | `Christ` | 1 | strong | The Son of God, the Messiah, King of kings (already marked by the Christ rule). |
| Mark | 1:1 | `Son of God` | 1 | strong | The Son of God, the miracle worker (already marked by the Son of God rule). |
| Luke | 22:27 | `I` | 1 | moderate | The Son of God, the faithful servant. |
| John | 1:1 | `Word` | 1 | strong | The Son of God, with divine wisdom (already marked by the Word rule). |
| Acts | 5:31 | `Prince` | 1 | moderate | The Head of the church leading believers to mature the rest of His body. |
| Romans | 3:26 | `justifier` | 1 | strong | He is our Righteousness and our Justifier as we live in Him. |
| 1 Corinthians | 15:45 | `last Adam` | 1 | strong | The last Adam, the first fruit of the resurrection, pouring out God's gifts and power. |
| 2 Corinthians | 5:21 | `him` | 1 | strong | He is our Apostle, Sin Bearer, and Reconciler. |
| Galatians | 3:13 | `Christ` | 1 | strong | He is the Redeemer from the law empowering us to walk in the Spirit (already marked by the Christ rule). |
| Ephesians | 1:22 | `head` | 1 | strong | He is the Head of the Body and the unsearchable riches of God's kingdom. |
| Philippians | 4:13 | `Christ` | 1 | strong | He is the Life, and the Strength that supplies our every need (already marked by the Christ rule). |
| Colossians | 1:15 | `image` | 1 | strong | He is the Image of the invisible God holding the supreme position given by God. |
| 1 Thessalonians | 4:16 | `LORD` | 1 | strong | He is our Hope and returning King. |
| 2 Thessalonians | 1:10 | `he` | 1 | strong | He is our Glory and returning King. |
| 1 Timothy | 2:5 | `mediator` | 1 | strong | He is the Mediator between God and man. |
| 2 Timothy | 4:8 | `righteous judge` | 1 | weak | He is the true Leader, steadfast in doctrine and ministry. |
| Titus | 1:9 | `Word` | 1 | weak | He is the faithful Pastor and our Foundation of truth (already marked by the Word rule). |
| Philemon | 1:16 | `LORD` | 1 | weak | He is our Mediator and Friend that sticks closer than a brother. |
| Hebrews | 12:2 | `author` | 1 | strong | He is the High Priest of the New Covenant, the Author and Finisher of our faith. |
| James | 2:1 | `LORD of glory` | 1 | weak | He is the Power behind our faith. |
| 1 Peter | 5:4 | `chief Shepherd` | 1 | moderate | He is our Rich Reward during time of trials and suffering. |
| 2 Peter | 1:3 | `him` | 1 | moderate | He is the True Knowledge who guards us against false teaching. |
| 1 John | 2:8 | `true light` | 1 | moderate | He is the Light of the world and the Way to God's love. |
| 2 John | 1:3 | `Son of the Father` | 1 | moderate | He is the Truth for the elect lady (the church of Jesus Christ). |
| 3 John | 1:7 | `his` | 1 | weak | He is the motivation for our witness. |
| Jude | 1:25 | `Saviour` | 1 | weak | He is the contender of the faith delivered to the saints. |
| Revelation | 19:16 | `KING OF KINGS, AND LORD OF LORDS` | 1 | strong | He is the glorified King of Kings preparing a Body for God to dwell in. |
