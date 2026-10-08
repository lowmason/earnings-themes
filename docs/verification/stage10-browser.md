# Stage 10 V5 presentation and fallback protocol

Native/manual observations are **complete (2026-10-08)** from human-supplied outcomes. The original frozen protocol and pre-observation expected rows remain below. Agent fixture checks alone do not establish native behavior; actual screenshot capture remains unverified.

## Declared target and policy

The complete target set is Chrome for Testing **154.0.8037.57**, matching chromedriver, **mac-arm64**. Capture uses unchanged `ISOLATED_1` (`isolated/1`), disabled source JavaScript, blocked network and images, bounded startup/navigation/capture/shutdown, viewport 1280 × 1024, UTC and the policy’s pinned preferences. Human observer/OS/target/date are recorded below; actual Selenium/driver execution details remain unreported. No cross-browser or remote HTTPS result is claimed.

## Concrete offline artifacts

Open `/private/tmp/earnings-stage10-v5/v1/index.html`. Its static link opens the content-bound six-case index. The bundle is `70f13f640e1ee84fa9372d19256c2873cb8c4ff188b7450dd4522c61c1c83129`; `expected.json` beside that index pins every expected CP/UTF-16 coordinate, canonical hash, mark anchor, exact saved-source/fallback filename, source-artifact SHA-256, and pending observation. These are invented sources. Files survive pytest temporary-fixture cleanup and command exit; the operating system may eventually clean `/private/tmp`, so the human command recreates the same immutable artifact set if absent. Conflicting bytes refuse instead of overwriting. The index pointer, prepared capture JSON and session observations are fully staged in a temporary file and published with a no-replace hard link; interrupted writes leave no partial final-name file and clean up temporary files. The bundle retains its existing staging/rename boundary.

The saved-source passage link points to the **content-hashed invented saved HTML** using the same text directive as the evidence source link. The canonical fallback link points to a separate content-hashed canonical HTML artifact’s exact stable mark anchor. The external source URL is metadata only; do not browse it. `tested_transport="local_file"`; external HTTPS remains `unverified`. Local-file success is not an HTTPS highlighting claim. The no-text-fragment case supplies both the primary directive link and an explicit control link with no directive. The drift case deliberately saves changed invented source wording while preserving the immutable canonical span. The repeated case targets the second occurrence. The long-page case uses an invented vertical CR-line prefix and marks visible target text after it; its CP offsets still refer to saved canonical text.

### Original expected metadata — historical pending rows

| Case ID | CP [start,end) | UTF-16 [start,end) | Native | Manual fallback | Capture | Observer/date |
| --- | --- | --- | --- | --- | --- | --- |
| unique | [0,24) | [0,24) | pending | pending | pending | pending |
| repeated | [27,53) | [28,55) | pending | pending | pending | pending |
| astral | [21,47) | [23,50) | pending | pending | pending | pending |
| long-page | [1701,1727) | [1701,1728) | pending | pending | pending | pending |
| drift | [0,30) | [0,30) | pending | pending | pending | pending |
| no-text-fragment | [0,26) | [0,26) | pending | pending | pending | pending |

## Human-only observation procedure

Run from this checkout, without browser setup, dependency syncing or downloads:

```bash
UV_CACHE_DIR=/private/tmp/earnings-stage10-uv POLARS_MAX_THREADS=2 uv run --locked --offline --no-sync --all-packages python tools/stage10_checks.py browser-user --user-only
```

This route collects exactly `tests/integration/test_stage10_browser.py` with `-m browser`. It builds the six invented pages, calls the public application `capture_evidence_view` through the shipped renderer, and writes an immutable `session-<UTC timestamp>/observations.json` under the content-bound bundle. Actual capture JSON and any screenshot bytes remain in that local session; their local references are content-hash bound. Screenshot rights are always `local_only`. No screenshots are opened by blind agents or placed in Git/public export. Missing optional SDK, binary or supported platform records `unavailable/browser_unavailable` and a skipped check; failed capture records its fixed reason and fails the check. An available successful capture never changes pending native/manual fields. A skip is not native success.

With network disabled, manually open the index in the declared target and try each invented saved-source passage link, then the independent canonical fallback anchor. Record only these native statuses: `highlighted`, `page_top`, `not_highlighted`, `wrong_occurrence`, `failed`, `unavailable`. Record fallback independently as `span_visible`, `failed`, or `withheld`. A usable fallback must show the correct canonical occurrence highlighted for every permitted span even if native navigation drifts or fails; rights withholding is explicit and cannot count as fallback success. For no-text-fragment, also inspect the plain control link. The static fallback itself contains no source JS or remote resources and needs no capture/network.

Copy the pending observation rows into a new local observation file; add observer ID and UTC date, actual environment, the chosen native/fallback statuses, closed failure reason (`native_failed`, `browser_unavailable`, `fallback_failed`, or `rights_restricted` when applicable), and optional local screenshot artifact IDs. Retain the original expected and capture files unchanged. Report only validated case IDs/counts/closed statuses, environment metadata and hashes to the controller. Do not paste source wording, screenshots, error details or traces. The controller records human-supplied outcomes here before Stage 10 completion.

If no target is available or `local_file` cannot exercise native highlighting, record that limitation and the independent manual fallback outcomes, then obtain an explicit V5 completion disposition. Native/browser support is not fabricated from static marks, capture success or fixture tests.

## Agent evidence and freeze exception

Invented fake lifecycle checks reproduce navigation exception, inherited-proxy use and leaked startup sockets. The user explicitly approved exactly the three disclosed lifecycle/isolation repairs on 2026-10-07. Only the unbounded current URL read is an uncaught capture crash; the other two are startup/isolation/cleanup repairs. The existing `crash` amendment category is used as an explicitly approved exception to the literal fixture-capture-crash restriction, not evidence that any actual fixture/native capture crashed. No comparison type/mapping/unit/metric/input, Stage 3 capture/report bytes, pin or capture-policy semantics changed. Standalone amendment and preregistration verification follow the committed adapter implementation. At this historical amendment checkpoint native availability/manual behavior were pending. Subsequent observations below close those gates; external HTTPS remains unverified.


The dedicated no-proxy debugger discovery opener now refuses every HTTP redirect,
including a redirect to another loopback URL, before a second request. This
completes the already approved validated-loopback isolation repair; it is not a
fourth lifecycle exception. Invented in-memory HTTP responses exercise the real
urllib redirect machinery without network or browser execution. The public
startup-failure reason and cleanup boundary remain unchanged. A second standalone
amendment retains the first record and discloses the same user-approved broader
crash classification; no actual native/fixture observation or remeasurement is
claimed.

## Human observations — 2026-10-08

Lowell Mason explicitly confirmed the UTC date and target availability/use: Chrome for Testing 154.0.8037.57, mac-arm64 on macOS. Codex in-app browser was also reported, with version unreported. Native outcomes followed the instruction to use the pinned target. Reported start 1:30 PM and finish 1:59 PM have no independently supplied clock timezone; they are not converted to timestamps. Implementation reference is `611f84a564ed9bfd4a52cf6682bf2c6a88676a23`; later human bindings use continuous same-checkout metadata. Safe closed metadata is retained in [stage10-browser-observations.json](stage10-browser-observations.json).

| Case ID | CP [start,end) | UTF-16 [start,end) | Native | Manual fallback | Actual capture |
| --- | --- | --- | --- | --- | --- |
| unique | [0,24) | [0,24) | highlighted | span_visible | unverified |
| repeated | [27,53) | [28,55) | highlighted | span_visible | unverified |
| astral | [21,47) | [23,50) | highlighted | span_visible | unverified |
| long-page | [1701,1727) | [1701,1728) | highlighted | span_visible | unverified |
| drift | [0,30) | [0,30) | not_highlighted | span_visible | unverified |
| no-text-fragment | [0,26) | [0,26) | highlighted | span_visible | unverified |

Repeated native/fallback outcomes identify the second occurrence. Drift has changed saved-source wording and correctly does not highlight natively; its independent canonical span is visible. The no-text-fragment plain control was opened: two items, neither highlighted. All observations use local_file; external HTTPS and automatic long-page scrolling remain unverified.

The human browser command returned 0 passed / 1 skipped / 0 failed, zero other counters, IDs [] and reason null. The audited source skips only when all captures are unavailable; the actual SDK/binary/platform cause was not supplied. The pinned manual target was explicitly available, so this skip does not establish an absent browser. Actual capture/screenshot success is unverified; workflow capture remains nondurable. Human-supplied inline invented-page images informed the fallback reports, but no agent opened actual capture files or copied images, wording or image references into Git/export. Screenshots retain local_only rights.

V5’s native/manual gate is now observed complete; no unavailable-target waiver is used. The 23 frozen inputs, original scenario order/status vocabulary, two approved amendments and final adapter SHA-256 `0ce37500b561c3642d971dc587e02e2e144a966581496c548017024d45f627b8` remain unchanged. The approved broader crash-category exception covers exactly three lifecycle/isolation defects, not a V5 waiver.
