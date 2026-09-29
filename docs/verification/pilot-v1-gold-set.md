# Pilot v1's codebook, split, and gold set: verification record

This record verifies roadmap Stage 6, which
`specs/pilot-codebook-split-and-gold-set-protocol.md` specifies and plan 9
(`specs/plans/9-pilot-codebook-split-and-gold-set-protocol.md`) built. Each gate
appends its section as it closes. The record holds IDs, counts, hashes, and dates,
never a release's wording or a paraphrase of it (GS3, GS13).

## The pin

- **The pilot.** Pilot v1, `config/corpus/djia-2024q3-2026q2/pilot-v1.json`,
  `djia-2024q3-2026q2-pilot`, content hash
  `3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926`: 40 events over
  33 issuers.
- **The events.** Events v1, `events-v1.json` beside it, content hash
  `2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7`.
- **The universe.** Universe v1,
  `config/universe/djia/manifests/djia-2024q3-2026q2-v1.json`, operative hash
  `c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573`.
- **What Stage 6 sent.** No SEC request, and no model call from code. The drafting
  sessions are listed at the end.

## Gate 1: the split and the coverage report

- **The split.** `evaluation/djia-2024q3-2026q2/pilot-v1/split-v1.json`, split v1 by
  `issuer-time/1`, content hash
  `5c4a2f3c5ed9ffc2cf0065658ec4e75311220338cf9b3fe07802c0db9fcd0e53`.
  - 20 train, 8 dev, 7 test, and 5 excluded.
  - Each excluded event is the later event of an issuer the pilot holds in an
    earlier partition (`issuer_in_earlier_partition`): `cik-0000004962:2026-06-30`,
    `cik-0000320187:2026-05-31`, `cik-0000731766:2026-06-30`,
    `cik-0000732712:2026-03-31`, and `cik-0001403161:2026-06-30`.
  - Two of the pilot's three `membership_boundary` events are in train, and the
    third is excluded. No event is a Stage 1 fixture's (P9-15).
- **The coverage report.** `coverage-v1.json`, coverage v1, content hash
  `7b1d8b8a10fa837e686addc6a60d43803782cc418f377efeb24e215d903f4060`.
  - It reads runs `acquire-20260928T153046989675Z` and
    `acquire-20260928T153714715420Z`.
  - All 40 documents are `parsed`.
  - `unavailable`, `restricted`, and `failed` are coverage gaps (D4), never
    repaired by reselecting.
  - One override applies: `release-doc-dis-2026-03-28`, on
    `cik-0001744489:2026-03-28:release`, with the verdict `not_confirmed`.
  - The no-theme count joins at Stage 11 for train and dev, and at Stage 14 for
    test.
- **The user's review.** The user read both on 2026-09-29, and approved them.
- **Checks.** The rebuilt split and report reproduce both files byte for byte. The
  local legs printed `11 passed, 3 skipped`, and the wording guard `5 passed`.
