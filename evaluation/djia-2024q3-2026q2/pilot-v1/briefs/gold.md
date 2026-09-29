# Brief: drafting gold

Stage 6 of the evidence-linked theme-extraction roadmap, under its spec's GS4, GS5,
GS13, and GS15. This brief carries all of the spec a drafting session needs. The
user starts this session fresh, with this brief, and names one task: one
bundle's gold, by its event ID, or the curated hard negatives. You draft; the user
verifies every item, adds what you missed, and signs. Nothing you write is
committed.

## Your task

- **One bundle's gold.** Read the one release the user names by its event ID, such
  as `cik-0000000000:2024-12-31`, whose text is
  `data/runs/gold/texts/cik-0000000000_2024-12-31.md`: file names write the colon as
  an underscore. Code what it says against codebook v0, and write
  `data/runs/gold/drafts/cik-0000000000_2024-12-31.draft.toml`.
- **The curated hard negatives.** Read Stage 1's fixture releases,
  `data/runs/gold/texts/fixtures/*.md`, and draft hard-negative claims over them, at
  least one each of `period`, `issuer`, and `section`. Write
  `data/runs/gold/drafts/hard-negatives.draft.toml`.

A test bundle is never drafted before Stage 14 freezes its configuration (GS18).
For one bundle's gold, before you open the release's text, find its row in the split,
`evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`. If its `partition` is not
`train` or `dev`, say so and stop.

## What you may read

- This brief.
- The contracts and checks: `packages/earnings-themes/src/earnings_themes/`
  `gold.py`, `annotation.py`, `anchoring.py`, `codebook.py`, `records.py`, and
  `tomlfile.py`.
- The split, `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`, for the named
  event's partition.
- Codebook v0: `codebooks/djia-pilot/codebook-v0.toml`.
- The text your task names: the one release, for one bundle's gold, or
  `data/runs/gold/texts/fixtures/*.md`, for the curated hard negatives; and your own
  draft under `data/runs/gold/drafts/`.

Nothing else. Open no other file under `data/`: no other release, and no other
draft, working copy, anchored file, view, saved exhibit, or canonical document. Read
no gold, committed or local: nothing under
`evaluation/djia-2024q3-2026q2/pilot-v1/gold/` or `tests/fixtures/gold/`. From
`evaluation/djia-2024q3-2026q2/pilot-v1/`, open only `split-v1.json` and this brief.
Read nothing under `prompts/`, and no code, prompt, or output of an extraction stage.
Open no spec, plan, roadmap, or decision record.

## Terms

- A **quote** is evidence: the exact words of a passage in the release.
- A **claim** is interpretation: what the quotes say, in your own words.
- A **theme** is a codebook definition. An **assignment** connects a claim to a
  theme, with whether the claim's quotes support it under that theme.

## The draft's form

TOML. The values below are invented, to show the form; none comes from a release.

```toml
event_id = "cik-0000000000:2024-12-31"
annotator = ""
no_theme = false

[drafting_aid]
model_id = "claude-opus-5-5"
drafted_on = 2026-10-03

[release_identification]
label = "release"
note = "The issuer's own results for the named quarter."

[[quotes]]
quote_id = "q1"
text = "The exact words of one sentence in the release."

[[quotes]]
quote_id = "q2"
text = "Words that occur twice"
prefix = "Exact text just before "
suffix = " and just after."

[[claims]]
claim_id = "c1"
quote_ids = ["q1"]
claim = "Unit orders grew over the year before."

[[assignments]]
claim_id = "c1"
theme_id = "demand.volume"
support = "supports"

[[hard_negatives]]
claim_id = "n1"
quote_ids = ["q2"]
claim = "Orders grew in the quarter being reported."
negative_kind = "period"
theme_id = "demand.volume"
```

For the curated hard negatives the file lists fixtures instead:

```toml
annotator = ""

[drafting_aid]
model_id = "claude-opus-5-5"
drafted_on = 2026-10-03

[[documents]]
fixture_id = "0000000000-00-000000_ex-99-1"

[[documents.quotes]]
quote_id = "q1"
text = "The exact words of one sentence in that fixture."

[[documents.hard_negatives]]
claim_id = "n1"
quote_ids = ["q1"]
claim = "A claim these words seem to support, but do not."
negative_kind = "section"
theme_id = "demand.volume"
```

A fixture's ID is its text file's name, without `.md`.

## Rules

- **`annotator` stays blank.** The user signs after verifying; an unsigned file is
  never committed (GS4).
- **Quotes.** A quote's `text` is the exact words of a narrative passage: a sentence,
  list item, footnote, heading, or paragraph, or part of one; never a table, a table
  cell, or a page header or footer (GS15). Text under a boilerplate notice may be
  quoted. It must occur exactly once in the release, or exactly once with the
  `prefix` and `suffix` you give, the exact text just before and after it.
- **Claims** are your own words and rest on at least one quote. No claim or note may
  share 40 characters, dates masked, with any release in the pilot or any Stage 1
  fixture, including those you are not given; the anchor refuses one that does, by
  its field and the text's ID (`source_wording`).
- **Assignments.** One row per claim and theme. `theme_id` is a codebook v0 theme,
  or `unmatched` when none fits: never propose a new theme (R9.3). `support` is
  `supports`, `does_not_support`, or `uncertain`. When a claim could take one of
  several themes and you cannot choose, give each a row with the same `tie_group`.
- **`no_theme`** is true exactly when no row pairs a claim with a codebook theme
  under `supports`. The anchor checks it.
- **Hard negatives** are claims the quotes seem to support but do not, each with its
  `negative_kind`: `period`, another quarter's result; `issuer`, another company's;
  or `section`, a passage such as boilerplate or a forward-looking statement that
  reports no result. `theme_id` names the theme it would wrongly support, if any.
- **Release identification.** `release` when the document is this event's earnings
  release, for its issuer and its period; `not_release` when it is not, optionally
  with `true_accession` and `true_exhibit`, as facts; `ambiguous` when you cannot
  tell. The note is your reason, in your words.
- **Coverage.** Code every claim a careful reader would, not only the clearest. The
  user adds what you miss, and the count of added items is reported.

## Checking your draft

Run, from the repository root, with the event ID the user named:

```bash
uv run --locked --all-packages earnings-pipeline gold anchor <event_id> --check
```

or, for the curated hard negatives:

```bash
uv run --locked --all-packages earnings-pipeline gold anchor --hard-negatives --check
```

It anchors every quote, checks every item, and prints counts and each refusal by
item and reason. It writes nothing. Fix the draft until it prints no refusal. Never
print the release's text into this session's output; the command never does.

## When you finish

Tell the user the draft's path, its counts, and the check's last lines. Do not create
the working copy, write any other file, or commit.
