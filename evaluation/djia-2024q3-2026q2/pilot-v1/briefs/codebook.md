# Brief: drafting codebook v0

Stage 6 of the evidence-linked theme-extraction roadmap, under its spec's GS9 and
GS13. This brief carries all of the spec a drafting session needs. The user starts
this session fresh, with this brief. You draft; the user edits, cuts, and approves.
Nothing you write is committed.

## Your task

Read the 20 training releases listed at the end, and propose the themes a reader
would use to code what these releases say about the business: the subjects that
recur across issuers and quarters. Write one file,
`data/runs/gold/drafts/codebook.draft.toml`, in the form below. It is the pilot
codebook, not the final taxonomy, which stays open.

## What you may read

- This brief.
- The contracts and checks: `packages/earnings-themes/src/earnings_themes/`
  `codebook.py`, `anchoring.py`, `records.py`, and `tomlfile.py`.
- The 20 texts listed at the end, under `data/runs/gold/texts/`, which the user
  prepared.

Nothing else. Open no other file under `data/`, apart from your own draft: no
other draft, and no view, saved exhibit, or canonical document. Read no dev or test release, no gold, and nothing
under `prompts/`, and no code, prompt, or output of an extraction stage. Open no
spec, plan, roadmap, or decision record.

## The draft's form

TOML. The values below are invented, to show the form; none comes from a release.

```toml
codebook_id = "djia-pilot"
codebook_version = 0

[drafting_aid]
model_id = "claude-opus-5-5"
drafted_on = 2026-10-01

[rules]
multi_label = "A claim may take several themes, one assignment row for each."
boilerplate = "Text under a boilerplate mask may be quoted; its masks are recorded."

[[themes]]
theme_id = "demand.volume"
label = "Unit demand"
definition = "Statements about how many units customers bought or ordered."
inclusion_rules = ["Order, shipment, or unit growth or decline."]
exclusion_rules = ["Price changes alone."]
sector_applicability = "all"

[[themes.positive_examples]]
event_id = "cik-0000000000:2024-12-31"
text = "The exact words of one sentence in that release."

[[themes.hard_negatives]]
synthetic = true
text = "Average selling prices rose while volumes held flat."
```

- `theme_id` matches `^[a-z][a-z0-9_.-]*$` and is never reused. `unmatched` is
  reserved. A sub-theme names its parent in `parent_id`; a top-level theme omits it.
- `label`, `definition`, and each rule are your own words.
- Each theme has at least one inclusion rule, exclusion rule, positive example, and
  hard negative.
- `sector_applicability` is `"all"` or a list of your own tags, such as
  `["retail", "energy"]`, each matching `^[a-z][a-z0-9-]*$`. A tag names a kind of
  business, never an issuer (GS16).
- An example is either a pointer or synthetic:
  - A **pointer** gives `event_id` and `text`: the exact words of a narrative
    passage in that training release: a sentence, list item, footnote, heading, or
    paragraph, or part of one, never a table, a table cell, or a page header or
    footer. The text must occur exactly once in the release. When it repeats, add
    `prefix` and `suffix`, the exact text just before and just after it, so that the
    three together occur once.
  - A **synthetic** example sets `synthetic = true` and gives `text` in your own
    words, with no `event_id`. Use one where no training release has a clear case,
    as hard negatives often need.
- The draft has no `approval`. The user approves v0 in ADR 0003.

## Rules

- **No copying.** Apart from a pointer's `text`, `prefix`, and `suffix`, no string
  may share 40 characters, dates masked, with any release in the pilot or any Stage
  1 fixture, including releases you are not given. The freeze refuses one that does,
  by its field and the text's ID (`source_wording`). Pointer text never reaches a
  committed file: the freeze turns it into offsets and hashes.
- **Scope.** A theme describes what a release says, not what an issuer is: no
  industry classification, no issuer's name, no ticker.
- **Sizing.** Propose the themes the 20 releases support, and no theme for a subject
  only one release mentions. Say in your summary which themes you were least sure
  of. The user cuts freely, so prefer a clear, small set to a long one.

## Checking your draft

Run, from the repository root:

```bash
uv run --locked --all-packages earnings-pipeline codebook freeze --working data/runs/gold/drafts/codebook.draft.toml
```

It anchors every example in the training releases, checks every field, and prints
counts, the content hash, and each refusal by item and reason. It writes nothing.
Fix the draft until it prints no refusal. Never print a release's text into this
session's output; the command never does.

## When you finish

Tell the user the draft's path, how many themes and examples it has, and the check's
last lines. Do not create the working copy, write any other file, or commit.

## The 20 training releases

Taken from the frozen split, `split-v1.json`; each is one release's canonical text,
named by its event ID with the colon as an underscore.

- `data/runs/gold/texts/cik-0000004962_2024-09-30.md`
- `data/runs/gold/texts/cik-0000018230_2024-12-31.md`
- `data/runs/gold/texts/cik-0000050863_2024-09-28.md`
- `data/runs/gold/texts/cik-0000051143_2024-12-31.md`
- `data/runs/gold/texts/cik-0000066740_2025-03-31.md`
- `data/runs/gold/texts/cik-0000080424_2025-06-30.md`
- `data/runs/gold/texts/cik-0000089800_2024-12-31.md`
- `data/runs/gold/texts/cik-0000089800_2025-03-31.md`
- `data/runs/gold/texts/cik-0000093410_2025-03-31.md`
- `data/runs/gold/texts/cik-0000104169_2025-04-30.md`
- `data/runs/gold/texts/cik-0000200406_2024-12-29.md`
- `data/runs/gold/texts/cik-0000310158_2025-06-30.md`
- `data/runs/gold/texts/cik-0000320187_2024-08-31.md`
- `data/runs/gold/texts/cik-0000731766_2024-09-30.md`
- `data/runs/gold/texts/cik-0000886982_2024-12-31.md`
- `data/runs/gold/texts/cik-0001018724_2025-03-31.md`
- `data/runs/gold/texts/cik-0001045810_2024-10-27.md`
- `data/runs/gold/texts/cik-0001045810_2025-04-27.md`
- `data/runs/gold/texts/cik-0001403161_2024-09-30.md`
- `data/runs/gold/texts/cik-0001751788_2024-09-30.md`
