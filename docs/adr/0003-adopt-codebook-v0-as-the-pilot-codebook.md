# 0003. Adopt codebook v0 as the pilot codebook

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Lowell Mason
- **Blast radius:** every theme assignment coded against `djia-pilot` v0: the
  pilot's gold and curated hard negatives (Stage 6), the codebook contract (Stage 9),
  and the evaluations that score against it (Stages 11, 12, and 14).

## Context

What was known on 2026-10-03, when Stage 6 drafted its codebook
(`specs/pilot-codebook-split-and-gold-set-protocol.md`, §The codebook;
`specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md`, Task 17):

- **The question.** A codebook version names its discovery corpus and is approved in
  a decision record before it codes anything (R9.2, R9.7). GS9 makes v0 the pilot
  codebook, frozen before any dev or test bundle is read (R12.3, GS13).
- **The discovery corpus.** The training partition of pilot v1's split,
  `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json` (`issuer-time/1`, content
  hash `5c4a2f3c5ed9ffc2cf0065658ec4e75311220338cf9b3fe07802c0db9fcd0e53`): the 20 training
  events' parsed documents, which
  `evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md` lists. The pilot is
  pinned by content hash
  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926` (GS2). No dev or
  test document was read.
- **The drafting aid.** Four Claude Code sessions, each running Claude Opus 5.5
  (`claude-opus-5-5`), worked on the codebook (GS9, P9-5). For the revision and
  review sessions, their model and what they read are as the review session
  reported:
  - On 2026-10-02, a fresh session read the brief and the 20 training texts, and
    drafted 18 themes with their fields. The draft is kept, unchanged and
    uncommitted, under `data/runs/gold/drafts/`.
  - On 2026-10-03, at the user's direction, the session running plan 9 revised the
    working copy. It worked from the draft alone, whose example quotes it had read,
    and opened no training text under `data/runs/gold/texts/`.
  - On 2026-10-03, a fresh revision session, given the brief and a revision prompt
    the user reviewed, read the brief, the four contract modules the brief names,
    the working copy, and the 20 training texts. It added three themes, gave two
    themes a second positive example, and pointed one rule at a new theme. It
    departed from the brief by editing the working copy rather than writing a draft.
  - On 2026-10-03, a review session made two edits the user authorized: the
    drafting aid's date, and one inclusion rule of `tax`.

  `drafting_aid` records the model and the last pass's date, 2026-10-03.
- **The user's working copy.** The user chose each change, or the rule for making
  it, reviewed the result, and confirmed this account and the drafting history
  above:
  - `macro` covers conditions the release names: an economy, region, industry, or
    indicator. The draft's `macro.positive_examples[1]` and `[2]` became hard
    negatives, and the revision session added a positive example.
  - `costs` takes a margin change only when a cost caused it.
  - `products` keeps launches, refreshes, and roadmap milestones; growth credited
    to innovation in general goes to `demand`. The draft's
    `products.positive_examples[1]` became a hard negative.
  - `supply` no longer covers the company's own inventory balance. Dealer and
    channel stock and inventory write-downs stay in it. The draft's
    `supply.positive_examples[2]` became a hard negative.
  - `legal_regulatory` became two themes: `legal` (lawsuits, investigations, legal
    reserves), with the draft's positives [0] and [1] and a synthetic hard
    negative the session running plan 9 wrote, and `regulation` (laws, rules,
    government programs, reimbursement), with the draft's positive [2] and hard
    negative [0], and a positive example the revision session added.
  - `costs.restructuring`, `capital.returns`, `capital.investment`, and
    `products.pipeline` became `restructuring`, `shareholder_returns`,
    `capital_investment`, and `pipeline`, under the same parents.
  - `mix`, `tax`, and `impairments` were added. `pricing` sends mix to `mix`, and
    a change in tax law is coded both `tax` and `regulation`.
  - An `inflation` theme was considered and not added: the 8 training releases
    that name inflation do so only inside generic lists of risks or
    forward-looking statements, which the codebook excludes, so no positive example
    was possible (the revision session's count, rechecked by the review session).
  - Every other theme keeps its drafted definition, examples, and rules, except
    that a rule naming a renamed, split, or new theme now names it, in `capital`,
    `credit_quality`, `portfolio`, `pricing`, and `trade_policy`.
- **Blinding.** At the user's request, the session running plan 9 read the draft
  once, its example quotes from 18 training releases included, to rate its
  themes, and later edited the working copy. Both were exceptions the user
  authorized to GS13's rule that it never reads a draft or a working copy. It
  opened no training text under `data/runs/gold/texts/`, and no view or canonical
  document. No session read a dev or test document.
- **The checks.** `codebook freeze` anchored every example to an exact narrative span
  of a training document. It refused any string that shares 40 characters with any
  of the 40 pilot releases or Stage 1's 8 fixtures (GS3, P9-21): 642 strings, no
  refusal. No passage is both a positive example and a hard negative of one theme.

## Decision

Adopt `codebooks/djia-pilot/codebook-v0.toml` as codebook `djia-pilot`, version 0:
the pilot codebook.

- It holds 22 themes and 96 examples.
- Its content hash is `635975d1ec952cf5719ea3b473870f96e7e3a52bc3015cc1ac5725aa80ec1e79`. The
  hash covers every field but `status`, `approval`, and `content_hash`, so this
  record cites it before the approval exists, and approving changes no hashed byte
  (P9-13).
- Its discovery corpus is the training partition alone.

v0 is the pilot codebook, not the final taxonomy, which stays deliberately
unresolved (`AGENTS.md`, §Source basis and unresolved choices; GS9).

## Consequences

- **v0 never changes.** A claim no v0 theme fits is coded `unmatched`, never as a new
  theme (R9.3). A later codebook is a new version with its own decision record, and
  gold coded against v0 stays coded against v0.
- **Stage 6's records cite it.** Every gold file and the curated hard negatives name
  v0 by ID, version, and content hash, and the validator refuses any other.
- **Reading order.** Dev bundles may be read for gold from this approval on; test
  bundles only after Stage 14 freezes its configuration (GS13, GS18).
- **Later stages.** Stage 9 takes v0 as its codebook contract's first frozen version,
  and Stages 11, 12, and 14 score against it.

## Alternatives considered

- **Discover over every partition.** Rejected: dev and test documents would shape
  the themes they later score (R12.3).
- **Adopt the model's draft unchanged.** Rejected: the codebook is the user's
  decision, and the draft only an aid (GS9).
- **Draft from blank, with no model.** Not chosen: GS4 has the user verify drafts,
  and records the limitation that the gold follows one model family's reading.
- **The user edits the working copy by hand, as Task 17 planned.** Not chosen: the
  user chose each change, or the rule for making it, had Claude sessions apply
  them, and reviewed the result. The codebook stays the user's decision through that review and this
  approval.
- **Deeper theme levels now, such as `macro` above `demand` and `supply`.**
  Deferred to Stage 12. The draft's `demand` and `supply` describe the company and
  `macro` the economy, so nesting them would mix two scopes, and a split by scope
  would change what coded assignments mean.

## Trade-offs & reversibility

- **What it costs.** v0 starts from one model family's framing of 20 releases,
  across four sessions, as the user directed and reviewed it, and one annotator
  approved it. The verification record, `docs/verification/pilot-v1-gold-set.md`,
  states both limitations.
- **Reversibility.** v0 itself cannot change. A v1 needs its own decision record and
  a recoding of any gold scored against it, and the v0 gold stays traceable to v0.
