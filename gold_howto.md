## Gold marking in detail

**The task in one sentence.** For each fixture you record, from what the browser shows, where each block of text starts and ends, what kind of block it is, and the order a reader meets the blocks. You don't transcribe the text. The scorer searches each parser's output for your short anchors, and every metric used to choose the Stage 1 parser comes from where it finds them.

### 1. How the scorer uses each field

| You mark | The scorer uses it for |
|---|---|
| `start` and `end` of a text block | **Coverage.** A block counts as found only if both anchors appear in the parser's output. It also feeds two diagnostics: a **split** (the anchors land in different elements) and a **merge** (one element holds anchors from two blocks). |
| `type` | **Footnote merging:** a footnote that shares an element with a heading, paragraph or list item. **Section header loss:** a heading the parser didn't type as a heading, or merged with another block. |
| The order of the `[[blocks]]` entries | **Reading order:** the share of neighbouring blocks that the parser puts in reverse order. |
| A table's three `cells` | Whether the table was found (all three cells present), and reading order inside the table. A parser that emits a table column by column puts `below` before `right`. A table moved elsewhere, say to the end of the document, shows up too. |
| A table's `headers` | **Table header loss:** header texts missing from the parser's table. |
| `row_header`, `col_header` | A diagnostic: does the parser attach each sample cell to the right row and column? |
| `level`, page artifacts | Neither is scored. Levels are tallied in a summary of your gold; page artifacts are kept for Stage 3. |

The practical consequence is that **your block boundaries are the ruler**. Boundaries around headings and footnotes feed ranked metrics directly. The rest feed the split and merge diagnostics.

### 2. One fixture, start to finish

1. **Open the fixture** in the browser's normal view: not Reader mode, not translated, and with no extension that rewrites page text. Put `gold.toml` in your editor next to it.
2. **Fill in `annotator` and `browser`.** For `browser`, give the name and version, from the browser's About box.
3. **Add `completed` now, not at the end.** I just confirmed on a scratch copy that while `completed` is missing, the validator reports only that one error and never checks your anchors. Checking as you go would show you nothing useful until you'd finished. For now, put `completed = 2026-09-23` below `browser` and change it to the real date when you finish. The better fix is in the validator itself: have it check anchors even before `completed` is set. That's a few lines, written test-first, and a missing `completed` would still fail the file. **Say "fix it" and I'll make that change.**
4. **Read the whole document once before marking anything.** Note the title, dateline, sections, lists, tables, footnotes, and any running header, footer or page number.
5. **Mark top to bottom,** one `[[blocks]]` entry per block, in the order a reader goes.
6. **Run the validator every few blocks.** Errors block scoring and warnings don't.
7. **Finish:**
   - set `completed` to the real finish date;
   - get the validator to 0 errors;
   - fill in the fixture's section of `gold-notes.md`;
   - tell me, and I'll commit it.

### 3. Deciding what counts as a block

The spec settles these cases:
- **Every piece of rendered text belongs to exactly one block.** That includes datelines, contact lines, "About the company" and safe-harbor paragraphs, and short oddities such as an end mark (`###`).
- **A block is what a reader sees as one unit.** A two-line title is one heading. A paragraph broken by a page break is one block.
- **Prose laid out inside an HTML table** is marked as paragraphs, not as a table.
- **A table title drawn outside the grid** is its own `heading` block. A title or units line inside the grid goes in `headers`.
- **Page artifacts** are running headers and footers and page numbers. Mark one entry for each occurrence.

Where the spec doesn't decide a case, the call is yours. Examples: a subtitle under the headline, a one-time "EXHIBIT 99.1" label, or bulleted rows laid out in a table. Decide by what a reader sees, apply the choice the same way in every fixture, and note it under "Structure the gold schema cannot express" in `gold-notes.md`.

I won't advise on those cases. I wrote the walker, which is one of the parsers being scored, so any guidance I gave could pull your gold toward how it behaves.

### 4. Writing anchors

- **Copy and paste from the browser; don't retype.** The files are pure ASCII, so any curly quote or dash you see comes from an HTML entity, and a typed straight quote won't match it.
- **Keep each anchor on one line.** A line break pasted inside quotes makes the TOML invalid. Replace it with a space; spacing never matters.
- **Length:** at least 4 words or 20 characters, unless the whole block is shorter, in which case the whole block is the anchor.
- **One contiguous run of text.** An anchor never includes a bullet, list number or footnote marker, and never skips over one. For "EBITDA(1) increased 5%", the anchor must sit entirely before or after the "(1)".
- **Unique:** matching deletes all spaces and then does a plain substring search, so `1,234` also matches inside `11,234`. If the validator says an anchor occurs more than once, add words.
- **Short and still not unique:** replace `end` with `after = "the next words on the page"`.
- **Still not unique after that:** set `unanchorable = true` and put the full text in `start`. The validator only accepts this flag if the text really does occur at least twice.
- **IDs:** only the position of an entry defines the reading order, not its ID. Numbering b001, b002… in order is easiest to review. If you find a block you missed, insert its entry in the right place with any unused ID, such as `b004a`.

### 5. Tables

- **`headers`:** every header text inside the grid.
  - column headers at every level;
  - the stub header (the top-left cell, such as "(Millions of Dollars)");
  - any title or units line inside the grid.

  Row labels aren't headers. Each header text only has to appear somewhere in the document.
- **The L of three cells:**
  - `corner`: a body value;
  - `right`: the same row, next data column;
  - `below`: the next row, same column as `corner`.
- **Rows to use:** pick rows with no `$` sign and no parentheses. Those are often in cells of their own, and the rendering doesn't show you where cell boundaries are. Also avoid numbers that appear elsewhere in the document.
- **`col_header` with several header levels:** the check is whether your text is contained in the parser's header stack for that column. The full stack ("Three Months Ended December 31, 2013") is the stricter test. The bottom level alone ("2013") is more lenient, and would also accept a parser that attached the cell to a different column group ending in 2013. The spec doesn't say which to use, so pick one, use it in every table, and note it.

### 6. A worked example (made up, not from any fixture)

What the browser shows:

```text
EXAMPLE PIPELINE PARTNERS LP REPORTS
FOURTH-QUARTER 2013 RESULTS

HOUSTON, Feb. 4, 2014 – Example Pipeline Partners LP today reported
fourth-quarter net income of $31.2 million, or $0.44 per unit.

Highlights
 • Throughput rose 12 percent from the prior-year quarter
 • Declared a quarterly distribution of $0.25 per unit(1)

                         Three Months Ended December 31,
(Millions of Dollars)            2013          2012
Revenues                   $     95.4     $    81.7
Net income                       31.2          24.9
Adjusted EBITDA                  40.6          33.8
Distributable cash flow          35.1          29.7

(1) Payable Feb. 14, 2014, to unitholders of record on Feb. 10, 2014.

- 2 -
```

The gold:

```toml
[[blocks]]
id = "b001"
type = "heading"
level = 1
start = "EXAMPLE PIPELINE PARTNERS LP REPORTS"   # both title lines form one heading
end = "FOURTH-QUARTER 2013 RESULTS"

[[blocks]]
id = "b002"
type = "paragraph"
start = "HOUSTON, Feb. 4, 2014"
end = "or $0.44 per unit."

[[blocks]]
id = "b003"
type = "heading"
level = 2
start = "Highlights"          # whole block is under 4 words, so it is its own anchor; no end

[[blocks]]
id = "b004"
type = "list_item"
start = "Throughput rose 12 percent"          # the bullet is left out
end = "from the prior-year quarter"

[[blocks]]
id = "b005"
type = "list_item"
start = "Declared a quarterly distribution"
end = "distribution of $0.25 per unit"        # stops before the (1) marker

[[blocks]]
id = "t001"
type = "table"
headers = ["Three Months Ended December 31,", "(Millions of Dollars)", "2013", "2012"]
cells = [
  { role = "corner", text = "40.6", row_header = "Adjusted EBITDA", col_header = "2013" },
  { role = "right",  text = "33.8", row_header = "Adjusted EBITDA", col_header = "2012" },
  { role = "below",  text = "35.1", row_header = "Distributable cash flow", col_header = "2013" },
]

[[blocks]]
id = "b006"
type = "footnote"
start = "Payable Feb. 14, 2014, to"            # the (1) marker is left out
end = "of record on Feb. 10, 2014."

[[blocks]]
id = "p001"
type = "page_artifact"
start = "- 2 -"
```

Why the L sits where it does:
- The Net income row fails because `31.2` also appears in the dateline, and the validator would report that it "occurs 2 times".
- The Revenues row has `$` signs, likely in cells of their own.

Suppose a short heading such as "Outlook" also appeared in a sentence. You would anchor it with `after`:

```toml
[[blocks]]
id = "b010"
type = "heading"
start = "Outlook"
after = "The partnership expects"   # the first words of the next block; no end
```

### 7. Reading the validator's messages

| Message | What to do |
|---|---|
| Only `missing top-level key 'completed'` | Your anchors haven't been checked yet; see step 3. |
| `gold.toml is not valid TOML` | Usually a pasted line break, or an unescaped `"` or `\`. Keep the anchor on one line, and use `'…'` quotes or escapes. |
| `start: not found` | Copy it again from the browser. Check that it doesn't include or skip over a marker. |
| `…case-insensitive hits…text-transform…` | The page's styling changed the letter case on screen. Use the case in the file, which the browser's developer tools show. |
| `occurs N times; extend it until it is unique` | Add words, or use `after` for a short block. |
| `…shorter than four words and 20 characters…` | Lengthen the anchor. If the whole block is that short, drop `end`. |
| `header '…' not found` | Copy the header text again. |
| `unanchorable text must occur at least twice` | The text is unique, so remove the flag and anchor it normally. |
| Warning: `…not unique in the fallback space` | Optional to fix. The scorer's fallback for altered text can't rescue this anchor. It also appears next to a "not found" error and clears once that is fixed. |
| Warning: `…may begin with a bullet or marker` | Remove the marker from the anchor. |
| Warning: `end precedes start` | You've probably swapped them or copied the wrong occurrence. |

### 8. What to expect from your eight fixtures

The class-test script recorded these for each fixture. Visible text (counted without spaces) predicts effort better than the file sizes I gave you earlier.

| Fixture | Class | Visible text | Recorded quirks |
|---|---|---|---|
| Ruby Tuesday 2005 | table-heavy | 0.9k | 85% of its text is in data tables |
| Phillips 66 Partners 2014 | narrative-only | 1.8k | none |
| Establishment Labs 2023 | narrative-only | 5.4k | page-break styling |
| UQM Technologies 2018 | clean | 6.7k | page-break styling |
| AVX 2017 | clean | 8.9k | page-break styling |
| AEP 2024 | malformed | 21.3k | positioned text; bare page-number blocks |
| IKON 2005 | malformed | 31.2k | mostly `<pre>` text; long prose inside layout tables |
| Humana 2006 | table-heavy | 32.7k | 58% of its text is in data tables |

What the quirks mean for marking:
- **Page-break styling:** the file was laid out for print. Watch for paragraphs split across page breaks and for running headers or footers.
- **Positioned text (AEP):** CSS places some text, so the on-screen order can differ from the order in the file. Mark the order you read on screen; that's exactly what the reading-order metric tests.
- **Page-number blocks (AEP):** mark them as page artifacts.
- **`<pre>` text (IKON):** monospaced text, with blocks separated by blank lines and any tables drawn with spaces. The same what-a-reader-sees rule applies. Note in `gold-notes.md` how you handled it.

**Suggested order:**
1. Phillips 66 Partners, which is open already, to learn text blocks.
2. Ruby Tuesday, to learn tables on a small file.
3. The three files with page-break styling.
4. AEP, IKON and Humana last.

### 9. `gold-notes.md`

- **Validator encoding line:** copy the validator's first line. For all eight it says every byte is ASCII, so skip the `characterSet` line.
- **Time spent:** V2 reports it as part of the gold protocol.
- **Tables inside lists or inside other tables:** Stage 2 needs this to design how elements nest.
- **Structure the gold schema cannot express:** anything that didn't fit, plus your judgment calls.

### 10. Where I can and can't help

**I can:**
- explain any validator message;
- fix TOML problems;
- work out at the character level why an anchor won't match;
- commit each fixture once it validates.

**I won't:**
- suggest block boundaries, types or anchor text;
- check your marking against the HTML.

The spec makes you the sole annotator, and my involvement would put the walker's author inside the thing it's measured against.

`★ Insight ─────────────────────────────────────`
- **Why anchors instead of transcription:** each anchor is an exact substring search, so the gold stays small, scoring never needs fuzzy matching, and the browser's spacing never matters. Uniqueness is what makes each anchor refer to exactly one place in a parser's output.
- **Why the browser is the reference:** none of the three parsers' code is involved in rendering the page. Gold marked from the rendering therefore measures the parsers rather than agreeing with one of them. The walker is my code, which is why I stay out of the marking.
`─────────────────────────────────────────────────`