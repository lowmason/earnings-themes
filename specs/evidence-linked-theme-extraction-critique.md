# First-pass methodological review: evidence-linked theme extraction from earnings releases

Most of the time goes on four choices in the method, not on the hardware: a classifier prompt ordered so that nothing can be cached, a four-trial unanimity rule that makes the support stage carry no information, verification keys that embed whole input bundles, and support labels bound to run identity. Fixing these four should take a train pass from about 73 h to roughly 12–16 h (my estimate) without discarding any manual label. All points below are first-pass findings for discussion. None has been adjudicated.

## TL;DR

- **Where the cost comes from.** Component C5 puts the claim text before the codebook, which blocks prefix-cache reuse of about 7,000 prompt tokens on every call (about 33 h of the 60 h of model time). Λ_V re-verifies 13 MB keys at every read (about 13 h per pass, plus 14 h per replay). The four-trial panel in C6 (about 26 h) produces a degenerate outcome: 1 clear target out of 1,170. My estimate is that about 80% of a train pass can be removed with fixes that do not change what any model is asked.
- **What is methodologically off.** The route from targets to π_{k,τ} runs through a per-target accept-or-review gate, while the measurement literature reaches prevalence through prediction-powered or design-based estimators that combine all model outputs with a probability sample of gold (Angelopoulos et al. 2023; Egami et al. 2023). The unanimity rule has no published counterpart: panels in the literature aggregate by vote or average (Verga et al. 2024), and "accept only when sure" is done by selective prediction with a calibrated guarantee (Jung et al. 2025). The support labels and the gold are model-drafted, and the anchoring this causes has been documented (Schroeder et al. 2025).
- **What to do first, and the labels it keeps.** (1) Re-key support labels by content (source hash, quote spans, claim text, theme), so that y^σ survives any change to C5 or C6. (2) Move the codebook to the front of the C5 prompt and confirm cache hits on your runtime. (3) Replace bundle-embedding keys with digest-addressed storage that is verified at write. (4) Drop the temperature-0 stability runs (about 90 h). (5) Replace unanimity with a fitted score plus a precision-guaranteed threshold, calibrated on new unaided owner labels. Freeze C3: it is cheap, and freezing it keeps every label set intact.

## Reading notes and shorthand

Label sets: **G** = signed gold (28 events), **IP** = the owner's independent dev passes (8 events), **HN** = hard negatives, **STr** = train support labels (70 targets, 63 usable), **SDv** = dev support labels (24, 21 usable), **TG** = test gold (not yet made). "Estimate" marks my arithmetic. Unless I say otherwise, time figures are per train pass of 20 documents and are built from the description's own observed figures.

The platform is not stated. I treat "36 GB unified memory, GPU and CPU" as consistent with Apple Silicon, but as an inference only. Each runtime-dependent recommendation names the capability it needs and what you should check.

---

## Part 1 — Where the method sits relative to the state of the art (ask 1)

**CP1 — Pointer extraction with code-verified spans (C3, C4, A1–A3) is sound, and stricter than the norm in this literature.**
- Targets: C3, C4, A1, A2, A3. Type: none needed (sound).
- Evidence: firm-level text measures in finance, such as the bigram share of earnings-call text devoted to political risk (Hassan et al. 2019, https://www.nber.org/system/files/working_papers/w24029/w24029.pdf) and GPT-3.5 summaries of chunked transcripts (Kim, Muhn & Nikolaev 2023, https://arxiv.org/abs/2310.17721), validate mainly through economic outcomes such as volatility and investment.\[1\]\[2\] They do not bind each measurement to an exact span. Making the model cite unit labels and letting code produce the quote removes quote fabrication by construction. Verifying "does the cited text support the claim" is then a well-posed grounding task with dedicated checkers (Tang, Laban & Durrett 2024, https://aclanthology.org/2024.emnlp-main.499/). \[3\]
- Effect: no change proposed. Labels: all kept.
- Check: none needed, beyond the retention reporting the method already does.

**CP2 — Component C1 (point-in-time cohort, acceptance-time eligibility, frozen hashed cohort) is sound.**
- Targets: C1. Type: none needed.
- Evidence: freezing membership and the sample rule before any text is seen is the standard defence against look-ahead and selection on outcome. Acceptance time is a defensible availability stamp for a prevalence estimand indexed by quarter. A wire release may come before the filing, but that does not move it to another quarter.
- Effect: none. Labels: all kept. Check: none.

**CP3 — Component C8's coverage-aware denominator is right, but the untested assumption that missingness is unrelated to themes can be bounded cheaply.**
- Targets: C8 assumption 1. Type: extend scope.
- Evidence: this is my reasoning, not a sourced result. Worst-case (Manski-type) bounds come from setting the missing firms to all-absent or all-present: π ∈ [n_k/(N_obs+N_miss), (n_k+N_miss)/(N_obs+N_miss)]. These cost nothing and show when missingness could matter.
- Effect: no time cost; makes a stated limitation quantitative. Confidence: high. Labels: all kept.
- Check: report the bounds per (k, τ) on the pilot's processing-state table.

**CP4 — In component C2, treating layout-table prose as unquotable is an unmeasured recall risk.**
- Targets: C2 assumption 2. Type: extend scope (measurement).
- Evidence: none found in this run on how much earnings-release prose sits inside layout tables. Outlook and quote boxes are plausible cases, but that is my conjecture.
- Effect: none on time. Possible small gain in recall. Labels: all kept, as long as canonicalization does not change. If you change the parser, A2 creates a new canonical version and G, IP and HN must be re-projected.
- Check: count the G quotes whose spans overlap layout-table elements in x_d.

**CP5 — The route from targets to π_{k,τ} (accept-or-review per target) is not how the measurement literature estimates prevalence from an imperfect classifier.**
- Targets: Purpose and estimand; C7; C8. Type: adopt a better method.
- Evidence: prediction-powered inference combines model predictions on the full population with a labelled sample to give valid intervals for means and other estimands (Angelopoulos et al. 2023, https://www.science.org/doi/10.1126/science.adi6000). \[4\]\[5\] Design-based supervised learning does the same for LLM annotations, requiring only known sampling probabilities for the gold (Egami et al. 2023, https://arxiv.org/pdf/2306.04746). \[6\]\[7\] For a binary event-level presence f̂_{ik} with gold Y_{ik} on a random subset L of events:
  $$\hat\pi^{PP}_{k,\tau}=\frac1N\sum_{i}\hat f_{ik}+\frac1{|L|}\sum_{i\in L}\big(Y_{ik}-\hat f_{ik}\big).$$
  Under the current design, the numerator counts only accepted assignments. At a 0.1% yield, π̂ is biased towards 0. Even a well-tuned precision gate biases π̂ downward, because it trades recall for precision. Reviewing every flagged target does not scale: 240 events at 59–90 claims each is about 14,000–22,000 targets.
- Ambiguity: "drawn by a fixed rule from frozen metadata" could mean a seeded random draw or a purposive rule. (a) If it is random with known inclusion probabilities, G is directly usable as L. (b) If it is purposive, the rectifier term needs a model of selection, or a fresh random gold draw.
- Effect: removes the need for C7 to accept anything in order to estimate π. Quotes are still reported, ranked by support score. Quality: unbiased under design (a). Confidence: high on the principle, low on precision for rare themes with 28 events.
- Labels: keeps G (event × theme presence is exactly Y_{ik}), IP and HN. STr and SDv are not needed for π.
- Check: compute π̂^{PP} against the naive plug-in for each theme on the 20 train events, using leave-one-event-out labels.

**CP6 — The finance literature measures intensity (share of text), whereas π is a binary "any mention" rate that is sensitive to single false positives.**
- Targets: Purpose and estimand. Type: extend scope.
- Evidence: Hassan et al. 2019 define exposure as the share of the call devoted to the topic.\[2\]\[8\] Kim et al. 2023 build call-level scores.\[9\] The ∃-indicator turns one spurious accepted quote into a firm-level positive.
- Effect: no time cost. Reporting an intensity companion (accepted units for theme k ÷ eligible units) would make results comparable with that literature. Labels: all kept.
- Check: on G, compare event-level presence with unit-share intensity, and see how many presences rest on a single unit.

**CP7 — A route the method ignores: codebook-following by open-weight models improves substantially with supervised tuning, and a large model's labels can be distilled into a small classifier.**
- Targets: C5; Q1 ("small trained classifier"). Type: extend scope.
- Evidence: Halterman & Keith (2026, Political Analysis, https://ideas.repec.org/a/cup/polals/v34y2026i2p188-204_3.html) find that "current open-weight LLMs have limitations in following codebooks zero-shot, but that supervised instruction-tuning can substantially improve performance".\[10\]\[11\] A 2026 preprint probes LLM coders' sensitivity to codebook order and label–definition remappings (https://arxiv.org/pdf/2606.06781), which is relevant to C5 assumption 2.\[12\]
- Effect: in the long run, near-zero marginal classification time. Quality unknown until tested. Confidence: low on this codebook.
- Labels: keeps G, IP and HN as evaluation data. Fine-tuning data would be the 1,171 train claims labelled by Gemma, which are model labels and not a human set, so no human set is consumed. STr/SDv y^φ are orphaned only if they are not content-keyed (see CP19).
- Check: train a small encoder on the C5 outputs for the train claims, then score event × theme F1 against dev G.

**CP8 — The panel borrows the "jury" idea but uses an aggregation (unanimity) that the panel literature does not use.**
- Targets: C6 step 3; A5; A6. Type: adopt a better method.
- Evidence: Verga et al. (2024, preprint, https://arxiv.org/pdf/2404.18796) find that a panel of smaller models from disjoint families "outperforms a single large judge" and is cheaper.\[13\] Their panels pool by voting or averaging, not by requiring every member to agree.\[14\]\[15\]
- Effect: see CP11. Labels: all kept.
- Check: on STr/SDv, compare majority vote and mean score against unanimity on the same trials.

**CP9 — "Accept only when sure" has a published form, selective prediction with a guarantee. C7's grid search with a recall floor offers no guarantee.**
- Targets: C7; Q2. Type: adopt a better method.
- Evidence: Jung, Brahman & Choi (ICLR 2025, https://arxiv.org/pdf/2407.18370) calibrate a confidence threshold so that P(agree with human | judge evaluates) ≥ 1−α holds with probability 1−δ.\[16\]\[17\] They cascade from weak to strong judges.\[18\] In their experiments Mistral-7B reaches over 80% human agreement at nearly 80% coverage.\[19\] Conformal risk control (Angelopoulos et al. 2024, https://arxiv.org/abs/2208.02814) and Learn-then-Test (Angelopoulos et al. 2025, https://arxiv.org/abs/2110.01052) provide the general threshold-selection tools.
- Effect: turns C7 into a rule with a stated precision guarantee at a given coverage. Labels: see Q2 and Q4.
- Check: see Q2.

---

## Part 2 — What is wrong, stale or unsupported (ask 2)

**CP10 — C5 places the claim-specific text before the shared codebook. This defeats prefix-cache reuse and is the largest single cost.**
- Targets: C5; cost model ("The classifier dominates inference"). Type: fix an error.
- Evidence: llama.cpp's server reuses the KV cache for the longest matching prefix ("the prompt is compared to the previous completion and only the 'unseen' suffix is evaluated"), and its responses report `cache_n`, the number of prompt tokens reused (ggml-org 2026, https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). \[20\] mlx-lm provides prompt caches that are treated as a prefix (Apple 2025, https://developer.apple.com/videos/play/wwdc2025/298/). \[21\]\[22\]\[23\]\[24\] A community oMLX run of Gemma 4 31B-it QAT 4-bit on an M4 Max (40-core GPU) measured about 200 prompt tok/s and about 15.4 generated tok/s (oMLX 2026-07-19, https://omlx.ai/benchmarks/e37o04o1). \[25\] This is a single community benchmark.
- Arithmetic (estimate): 7,000 prompt tokens at roughly 90–200 tok/s is 35–78 s of prefill, against about 2–3 s to decode 29 tokens. So prefill is about 95% of each call, which confirms your inference. Your own baseline of about 80 s per call implies about 91 prompt tok/s. If the codebook is about 5,000–6,000 tokens and moves to the front, the uncached suffix is about 1,000–2,000 tokens, or about 14–25 s per call. Over 1,181 calls that is 4.6–8.2 h instead of 33.3 h, a **saving of about 25–29 h per train pass**.
- Runtime caveat: Gemma 4 uses sliding-window attention (a 1,024-token window on the 31B) and shares KV across layers (SiliconBench 2026, https://arxiv.org/pdf/2609.19169). \[26\]\[27\] llama.cpp exposes a `--swa-full` flag ("use full-size SWA cache").\[28\] Whether prefix reuse holds for SWA layers without it is something to check on your runtime. Confirm reuse empirically through `cache_n` or the equivalent.
- Quality: the content is identical, only the order changes. Codebook-order sensitivity exists (arXiv 2606.06781), so measure it rather than assume it away. Confidence: high on direction, medium on size.
- Labels: under current keying, any C5 prompt change orphans STr and SDv. Under content keying (CP19), y^σ survives fully and y^φ survives wherever the theme assignment is unchanged. G, IP and HN are kept.
- Check: rerun C5 on one train document with the codebook first. Record `cache_n`, per-call time, and the agreement of Θ_c with the old run.

**CP11 — Under unanimity, O(t) is degenerate: it flags 99.9% of targets while the labels imply a much lower rate of failures. It carries almost no information, so C7 cannot calibrate on it.**
- Targets: C6 step 3; C6 assumption 2; C7 assumption 1. Type: fix an error.
- Evidence (internal): train has 1 clear target of 1,170, dev has 5 of 601. Write q for the probability that a single trial is entirely clean on a supported target. If trials were independent, P(clear) = q⁴ ≈ 1/1,170, so q ≈ 0.17. On this rough reading, each trial objects to about 83% of targets. Yet 62 of 64 y^σ labels are "supported".
- My inference: C7's recall bound of 1/41 implies that 41 usable train targets have y = 1 (supported and fits). That puts the joint label prevalence at about 41/63 ≈ 65%. The flag rate (≈ 100%) far exceeds the failure rate in the labels (≈ 35% joint, ≈ 3% σ). The unanimity rule was not tested before deployment (the description says so), and the figures refute it as a precision device.
- Effect: removing unanimity changes the yield from ≈ 0 to something measurable. Confidence: high.
- Labels: all kept. The raw trials are stored, so STr and SDv can be rescored under any aggregator without new model calls.
- Check: recompute the outcome under majority vote and under the mean score on stored trials, then cross-tabulate against y.

**CP12 — C6 re-asks theme fit (φ), which C5 has already decided, and asks claim support (σ) with general judges when specialised grounding checkers exist.**
- Targets: C6 problem statement; C5/C6 split. Type: adopt a better method.
- Evidence: MiniCheck-FT5 (770M) "reaches GPT-4 accuracy" on LLM-AggreFact (Tang et al. 2024, https://aclanthology.org/2024.emnlp-main.499/). \[3\] The authors' repository describes Bespoke-MiniCheck-7B as "the current SOTA regardless of size" (https://github.com/Liyan06/MiniCheck). \[29\] That is an author claim, and its date should be checked against current LLM-AggreFact standings. Asking for φ four more times duplicates the C5 decision with weaker models.
- Effect: σ comes from s_P (already computed, or an upgraded checker); φ comes from C5's own confidence, e.g. token log-probabilities, if your runtime exposes them. Judges are needed only where both are uncertain. Time: see Q1. Quality: probably neutral to positive. Confidence: medium.
- Labels: y^σ and y^φ are kept and used separately, which is a better use of them than the joint y.
- Check: AUC of s_P against y^σ is uninformative with 2 negatives, so first collect σ-negatives (see Q8). Separately, measure the AUC of a C5 φ-confidence against y^φ on STr ∪ SDv.

**CP13 — Mistral-Nemo shows no measurable agreement (κ = 0.005, 90% CI −0.092 to 0.101), so under unanimity it can only veto.**
- Targets: C6; A6; Q1 ("dropping a judge family"). Type: fix an error.
- Evidence: the description's own figures. The comparison is with model-drafted labels, so this is weak evidence about the judge's agreement with experts, but it is the only evidence there is.
- Effect: removing its two trials halves judge calls, saving **about 9.7 h of the 19.5 h judge phase** (estimate). Quality loss: none measurable against current labels. Confidence: medium.
- Labels: all kept.
- Check: on stored trials, does removing Mistral change any decision of a majority or score aggregator on STr ∪ SDv?

**CP14 — Both judge models are 2024 releases, two generations behind current open-weight families of the same size.**
- Targets: A6; A10; Q3. Type: adopt a better method.
- Evidence: Gemma 4 (31B dense, 26B A4B MoE, 12B; Apache 2.0) was released on 31 March / 2 April 2026 (Google 2026, https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/). \[30\]\[31\]\[32\] SiliconBench (2026 preprint, https://arxiv.org/pdf/2609.19169) benchmarks the Qwen3.5/3.6 families on Apple-Silicon stacks.\[27\] Qwen2.5-14B was released on 19 September 2024 (Qwen Team 2024, https://qwenlm.github.io/blog/qwen2.5/) and Mistral NeMo 12B on 18 July 2024 (Mistral AI release notes, https://docs.mistral.ai/resources/release-notes). I did not verify a current Mistral-family model of the same size.
- Effect: probably better agreement per call. Quality gain unmeasured. Confidence: low–medium.
- Labels: a judge change changes the trials, not the targets. With content keying, STr and SDv survive.
- Check: rerun only the judge stage, on the 84 labelled targets, with a current non-Gemma model.

**CP15 — Presentation-order swapping is used as a veto (any disagreement flags) when it should be a modelled rater effect.**
- Targets: C6 step 2, assumption 3. Type: adopt a better method.
- Evidence: position bias in LLM judges is systematic rather than random, and it varies by judge and task (Shi et al. 2025, https://aclanthology.org/2025.ijcnlp-long.18/). \[33\]\[34\] A 2026 preprint of 21 judges reports high test–retest reliability alongside severe position bias, for example Qwen 3 8B with test–retest 0.992 and position bias 0.192 (https://arxiv.org/html/2606.19544v1). \[35\] Both papers study pairwise or list-wise candidate order. Applying them to evidence-first versus claim-first order is my extrapolation. Order disagreement therefore measures a bias of the judge, not the truth for the target, and averaging over a randomised order removes it in expectation.
- Effect: one trial per judge with a random order, and an order term in the aggregator, halves the remaining judge calls. Confidence: medium.
- Labels: all kept.
- Check: on stored trials, estimate the order effect per judge as P(σ = supported | evidence first) − P(σ = supported | claim first).

**CP16 — Judge outputs are verbose (about 127 tokens, including a rationale and per-quote labels), and most unavailable trials come from invalid quote references. Constrained decoding addresses both.**
- Targets: C6 step 2; ε_J; O_inc. Type: adopt a better method.
- Arithmetic (estimate): at about 200 prompt tok/s for a 14B model, 1,700 tokens take about 8.5 s; at about 22 tok/s, 127 output tokens take about 5.8 s. Together that is ≈ 14.3 s, close to the observed 14.4 s. So decode is about 40% of each judge call. Cutting output to about 40 tokens by enumerating quote IDs and moving the rationale to an audit subset saves about 25–30% per call.
- Runtime: grammar or JSON-schema constrained decoding has to be checked on your runtime. I did not verify it for MLX servers in this run.
- Effect: lower ε_J. Most of the 64 train incompletes should become complete. Labels: all kept.
- Check: count the O_inc causes that are invalid quote references.

**CP17 — The alternative scorer s_A runs on the production path (6 h 15 min on train) although no decision uses it.**
- Targets: C6 step 1; cost table. Type: fix an error.
- Evidence: the description says s_A is "a comparison", C7's rule uses only s_P, and its phase time is inflated by replaying 4,867 judge entries.
- Effect: running s_A only on labelled targets saves **about 6 h** per train pass. Confidence: high. Labels: all kept.

**CP18 — Λ_V is disproportionate: cache keys embed whole bundles (≈ 13 MB per key, ≈ 107 GB for 7,792 entries), and every invariant is re-checked at every consuming step.**
- Targets: A8; C4 cost; Λ_V; Q6. Type: fix an error.
- Evidence: Bazel's remote cache consists of "a map of action hashes to action result metadata" and "a content-addressable store (CAS) of output files" (Bazel docs, https://github.com/bazelbuild/bazel/blob/master/site/en/remote/caching.md); the Remote Execution API addresses each result "by a digest of the encoded Action", unlike the CAS, "which addresses blobs by their own content" (REAPI v2, https://buf.build/bazel/remote-apis). Every blob is keyed by its digest and each action by a digest of its input digests, i.e. a Merkle tree. Integrity is checked once, when a blob is written. A later read checks a 32-byte digest, not the full content.
- Arithmetic: 7,792 × 13 MB ≈ 101 GB, which is consistent with the 107 GB stated. Your exactness invariant q = x_d[a, b) needs x_d once per document, about 22 KB (5.5 windows × 4,000 characters), not once per cache entry.
- Effect (estimate): the 13 h write and read-back falls to under 1 h; the replay falls from 14.2 h to under 1 h; each label step falls from 32 min to about a minute. The exactness guarantee is kept, because each quote record stores (h(x_d), a, b, h(q)) and C4's check runs once at write. Confidence: medium on size, high on direction.
- Labels: all kept. Content keying (CP19) uses the same digests.
- Check: profile one replay. Split the time between hashing and reading bundles and the invariant checks themselves.

**CP19 — Binding support labels to run identity is a design error. y^σ does not depend on C5 at all.**
- Targets: label table; A8; Q4. Type: fix an error.
- Evidence (my reasoning): σ is a property of (x_d, quote spans, claim text). φ is a property of (claim text, k, codebook version). Neither depends on which model proposed the pair. A content key such as
  $$\text{key}_\sigma=h\big(h(x_d)\,\|\,\text{sorted}\{[a_i,b_i)\}\,\|\,\text{norm}(\ell_c)\big),\qquad \text{key}_\varphi=h\big(\text{norm}(\ell_c)\,\|\,k\,\|\,\text{ver}(\mathcal K)\big)$$
  lets labels survive any change to C5–C7, and any change to C3 that reproduces the same claim and spans.
- Effect: no time cost. It is the prerequisite for every other change. Confidence: high.
- Labels: keeps STr and SDv. Re-keying orphans nothing.
- Check: re-key all 94 labels and confirm that the mapping is one-to-one on the current runs.

**CP20 — The requirement that both judges and the primary scorer stay in memory together (A10) causes swapping, and it is what imposes the 14B cap.**
- Targets: A10; cost model ("Memory pressure"). Type: fix an error.
- Evidence (description): up to 22 GB swapped; one pressure episode raised classifier time from 80 to 155 s. Gemma 4 31B at 4 bits is about 15.5–19 GB of weights (LM Studio, https://lmstudio.ai/models/gemma-4). \[26\]\[36\] oMLX recorded a peak of 29 GB at 4k context on a 128 GB machine.\[25\]
- Arithmetic (estimate): the mean classifier time of 101.7 s against an unpressured 80 s gives (101.7 − 80) × 1,181 ≈ 7.1 h attributable to pressure, if pressure is the whole difference.
- Ambiguity: if the judges co-reside because they run interleaved per target, then running all of judge 1's trials and then all of judge 2's removes the need. If co-residence serves some other purpose, say which.
- Effect: about 5–7 h saved. It also lifts the cap, so a 24–31B judge or a 30B-class MoE judge fits. Labels: all kept.

**CP21 — The three temperature-0 stability runs (about 30 h each) measure runtime determinism, which a replay already demonstrates.**
- Targets: C9 stability; limitation 8. Type: fix an error.
- Evidence: the description itself says "a near-perfect result shows only runtime determinism". One caveat: once continuous batching is adopted (CP31), greedy outputs can depend on batch composition on some kernels. That makes one non-replay determinism check worthwhile, but not three full runs.
- Effect: saves **about 60–90 h** once. If sampling robustness is the goal, use sampled decoding on 2 dev events. Labels: all kept.

**CP22 — C5's per-document ceiling of 128 requests causes informative truncation (one dev document lost 94 of 220 claims).**
- Targets: C5 procedure. Type: fix an error.
- Evidence: truncation falls on long releases, so recall becomes a function of document length. That biases π towards themes typical of short releases.
- Effect: once CP10 applies, a call costs about 15–25 s, so the ceiling can go. Labels: all kept.
- Check: compare dev recall against G for the truncated document with that of the others.

**CP23 — G and SDv are model-drafted then human-verified, and anchoring towards model suggestions is documented. IP is the instrument that can measure it.**
- Targets: label table; C9 assumption 3; limitation 6. Type: adopt a better method.
- Evidence: in a pre-registered study with 410 annotators, "annotators strongly took the LLM suggestions, significantly changing the label distribution", and evaluating LLMs on such labels made "reported model performance significantly increase[s]" (Schroeder, Roy & Kabbara 2025, preprint, https://arxiv.org/abs/2507.15821). \[37\] That study used crowdworkers on subjective tasks. An earlier study found that annotators correcting tool output "exhibit an anchoring bias effect towards the output of automatic annotation tools", leading to "overestimation of parsing performance" (Berzak et al. 2016, https://arxiv.org/abs/1605.04481). \[38\]\[39\] The setting of an expert owner on earnings releases is different, so treat this as a risk to measure, not as a demonstrated effect.
- Effect: no time cost. Quality: sizes the bias in all G-based metrics. Labels: keeps all. IP is used as intended.
- Check: on the 8 dev events, compute event × theme agreement and quote-unit overlap between IP and the signed dev G. Count the themes in G that IP missed and the reverse. Asymmetric additions in G that match the drafter's suggestions are the anchoring signature.

**CP24 — STr has no human review, so C7's calibration fits a hosted model's view, and any precision it reports is agreement with that model.**
- Targets: label table; C7 assumption 2. Type: fix an error.
- Evidence: the description. Schroeder et al. 2025 show that evaluation on LLM-influenced labels overstates LLM performance.\[37\]
- Effect: use STr for development (choosing features and the aggregator form) and not for the guarantee. The guarantee needs fresh unaided owner labels (Q2). Labels: STr kept, with its role restated.

**CP25 — The gate rule ("a later configuration's dev point estimate ≥ the baseline's 90% lower bound") is unpaired, lenient, and reuses dev adaptively.**
- Targets: C9 procedure; Q8. Type: adopt a better method.
- Evidence (my reasoning): a configuration whose true value equals the baseline passes with probability ≈ 0.95. Configurations somewhat worse than the baseline also pass often. Repeated configuration searches against the same 8 events overfit dev. A paired per-event difference d_e = M_new(e) − M_base(e) cancels between-event variance. With 8 events, an exact sign-flip test over the 2⁸ = 256 sign patterns, with a pre-declared non-inferiority margin, is exact. Where the baseline accepts nothing, support precision is undefined, so the gate fails every configuration and is vacuous.
- Effect: no time. Better decisions. Labels: all kept. TG stays untouched.

**CP26 — Cluster-bootstrap intervals with 8 dev clusters are unreliable, and B = 10,000 exceeds the number of distinct resamples.**
- Targets: C9; B; Q8. Type: fix an error.
- Arithmetic: resampling 8 clusters with replacement gives C(15, 8) = 6,435 distinct multisets, fewer than B. The 5th percentile then rests on a handful of resamples dominated by the 1–2 weakest events. Cameron, Gelbach & Miller (2008, https://ideas.repec.org/a/tpr/restat/v90y2008i3p414-427.html) note that standard tests "can over-reject … with few (five to thirty) clusters" and that "with few clusters the bootstrap resampling methods produce a distinctly finite number of possible pseudo-samples".
- Effect: none on time. Labels: all kept. Use exact sign-flip or permutation methods for the 8 dev events, and report intervals as descriptive.

**CP27 — The κ imbalance concern applies to y^σ (62 of 64 positive), not to the joint y against which κ_j is computed (an implied ≈ 41/63 positive).**
- Targets: C6 evaluation; Q8; limitation 5. Type: adopt a better method.
- Evidence: under high prevalence κ can be low despite high observed agreement, and Gwet's AC1 is more stable (Wongpakaran et al. 2013, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3643869/). \[40\] AC1, however, "increases with increasing distance of the prevalence from 0.5" and "can be high in the case of no association", so it "cannot be seen as a substitute" for κ (Vach & Gerke 2023, https://pmc.ncbi.nlm.nih.gov/articles/PMC10205778/). \[41\]
- Effect: report sensitivity and specificity, or positive-specific and negative-specific agreement, with exact intervals, alongside κ. With 2 σ-negatives, specificity cannot be estimated under any statistic. Labels: all kept.

**CP28 — Several figures in the description do not reconcile.**
- Targets: cost model; label table. Type: fix an error (in the description).
- Items: (i) dev: 719 claims − 94 truncated = 625, but the text says 623 completed claims. (ii) The scorer formula gives 2N_T = 2,340 calls, but s_A shows 1,463 calls. "Per-quote signals" is undefined. (iii) Usable train labels: 63 targets, but "62 of 64 usable train claim labels". These are probably σ-usable and joint-usable counts. Please confirm. (iv) The recall bound "1/41" implies 41 joint positives. Please confirm (CP11 rests on it). Consistent items: 1,171 × 1.009 ≈ 1,181; 4 × 1,170 × 1.04 ≈ 4,867; phase times sum to 60 h 28 min; 63 + 21 = 84 and 70 + 24 = 94.

**CP29 — Windowed extraction (C3) is not a cost driver and should stay as it is. Duplicate claims across windows do inflate C5 and C6, and should be removed before C5.**
- Targets: C3 assumptions 1 and 3; Q7. Type: adopt a better method (dedupe).
- Evidence: C3 costs 1 h 22 min (2% of model time). A release is about 22,000 characters, or about 5–6k tokens. In NoLiMa, recall of facts without literal overlap "degrades significantly as context length increases", with "considerable drops even at 2K–8K tokens" (Modarressi et al. 2025, https://proceedings.mlr.press/v267/modarressi25a.html). \[42\]\[43\] That task is associative retrieval, not exhaustive extraction, so applying it here is my extrapolation. It nonetheless favours windows of about 1k tokens over whole-document reading for recall.
- Effect: dedupe by quote-span overlap together with a near-identical claim test. The saving is proportional to the duplicate rate, which has not been measured. Labels: all kept. Deduplication must keep the original claim IDs so that STr/SDv content keys still resolve.
- Check: cluster train claims by Jaccard similarity of cited unit sets and count the duplicates.

---

## Part 3 — Improvements ranked by expected value (ask 3)

Savings are per train pass (baseline ≈ 60 h of model time plus ≈ 13 h of verification), are my estimates, and are not additive: each row after the first applies to what is left.

| Rank | Change | CP | Type | Expected time saved | Expected quality effect | Labels kept / orphaned |
|---|---|---|---|---|---|---|
| 1 | Content-key support labels | CP19 | fix an error | 0 h (enables all others) | none | keeps all; orphans none |
| 2 | Codebook-first C5 prompt; verify `cache_n` | CP10 | fix an error | 25–29 h | ≈ none (test for order effects) | all kept with CP19 |
| 3 | Digest-addressed store, verify at write | CP18 | fix an error | ≈ 12 h per pass; replay 14 h → < 1 h | none; exactness kept | all kept |
| 4 | Drop the temperature-0 stability runs | CP21 | fix an error | 60–90 h once | none | all kept |
| 5 | Replace unanimity with a fitted score and a guaranteed threshold | CP11, CP8, CP9 | fix an error / adopt | indirect: makes C7 produce output | large gain in coverage; precision guaranteed only with human labels | all kept; needs new unaided labels |
| 6 | Drop Mistral-Nemo; one randomised order per judge | CP13, CP15 | fix / adopt | ≈ 9.7 h + ≈ 4.9 h | none measurable vs current labels | all kept |
| 7 | Remove s_A from the production path | CP17 | fix an error | ≈ 6 h | none on decisions | all kept |
| 8 | Phase scheduling instead of co-residence | CP20 | fix an error | ≈ 5–7 h | none; allows larger judges | all kept |
| 9 | Prevalence via PPI/DSL instead of gating | CP5 | adopt | avoids reviewing ≈ 14–22k targets | removes downward bias of π̂ | uses G as rectifier set |
| 10 | Measure anchoring with IP | CP23 | adopt | 0 | sizes the bias in gold | IP used as designed |
| 11 | Paired, exact dev gates | CP25, CP26, CP27 | adopt / fix | 0 | fewer false passes | TG untouched |
| 12 | Short constrained judge output | CP16 | adopt | ≈ 25–30% of residual judge time | fewer O_inc | all kept |
| 13 | Remove the C5 ceiling; dedupe claims | CP22, CP29 | fix / adopt | − (ceiling) / + (dedupe) | recall on long releases restored | all kept |
| 14 | MoE or QAT model for C5; parallel judge slots | CP30, CP31 | adopt | further 1.5–4× on residual (low confidence) | unknown; test | y^φ only where Θ_c changes |
| 15 | Distilled small classifier; rented or hosted runs | CP7, CP32 | extend scope | most of the residual | unknown | all kept as evaluation data |

**Projected pass after ranks 1–8 (estimate).** Extractor 1.4 h; classifier 4.6–8.2 h; one or two judge trials per target at ≈ 10 s each, 1,170 × 1–2 × 1.04 × 10 s ≈ 3.4–6.8 h; s_P on CPU ≈ 0.8 h; verification under 1 h. Total **≈ 11–18 h, against ≈ 73 h**. The full corpus is 12× train, or up to 18× at dev's claim density of about 90 claims per document: ≈ 130–320 h, or **about 6–13 days of continuous running instead of 40–45**.

**CP30 — For C5, test a mixture-of-experts model from the same family and the QAT checkpoints.**
- Type: adopt a better method (conditional).
- Evidence: Gemma 4 includes a 26B-A4B MoE (Google 2026). Google's QAT checkpoints aim at "preserving similar quality to bfloat16" (Google DeepMind 2026, https://huggingface.co/google/gemma-4-31B-it-qat-w4a16-ct). \[31\]\[32\] That is vendor documentation, and no independent quality evaluation was found in this run.
- Extrapolation: about 4B active parameters means roughly 1/8 of the per-token compute of the 31B dense model, so several-fold faster prefill on the same machine.
- Labels: same family, so A6 is unaffected. y^φ is orphaned only where Θ_c changes. Check: time and Θ_c agreement on 50 train claims.

**CP31 — Run the judges with parallel slots or continuous batching.**
- Type: adopt a better method (runtime-dependent).
- Evidence: llama.cpp server enables continuous batching by default, with `--parallel` slots (ggml-org 2026).\[20\]\[44\] vllm-mlx reports 3.7× throughput for Qwen3-0.6B at 16 concurrent requests on an M4 Max (Barrios 2026, preprint, https://arxiv.org/pdf/2601.19139). \[45\] oMLX measured 1.90× decode throughput at batch 2 for Gemma 4 31B.\[25\]
- Effect: helps the decode-heavy judges more than the prefill-bound classifier. Check KV memory per slot on 36 GB. Labels: all kept.

**CP32 — Rented GPUs or hosted open-weight models would remove the hardware constraint at small cost (see Q5).**
- Type: extend scope. Labels: all kept, provided keys are content-based.

---

## Part 4 — Answers to the open questions (ask 4)

### Q1. Where is the cost, and what should be attacked first?

The cost is λ_C first (33.3 h, caused by prompt order and swapping), then Λ_V (≈ 13 h per pass and 14 h per replay, caused by key design), then the panel (≈ 26 h including s_A, caused by four trials and an unused scorer). Ranking by expected time saved against expected quality lost:

| Option | Time saved (train pass, estimate) | Quality lost | Ratio judgement |
|---|---|---|---|
| C5 codebook-first prefix caching (CP10) | 25–29 h | ≈ 0 | best |
| Λ_V digest store (CP18) | ≈ 12 h plus replays | 0 | best |
| Drop the s_A production phase (CP17) | ≈ 6 h | 0 | best |
| Drop Mistral-Nemo (CP13) | ≈ 9.7 h | ≈ 0 vs current labels | very good |
| One randomised order per judge (CP15) | ≈ 4.9 h | small, modelled | very good |
| Phase scheduling, no swap (CP20) | ≈ 5–7 h | 0 | very good |
| Cascade: judges only where s_P is uncertain (CP9) | ≈ 50% of residual judge time (assumed band) | bounded by calibration | good, needs labels |
| Short constrained judge output (CP16) | ≈ 1.5 h | audit rationale lost unless sampled | good |
| Batch claims per window (Cheng et al. 2023, https://arxiv.org/pdf/2301.08721; Pipal et al. 2026, https://arxiv.org/pdf/2604.03684) \[46\]\[47\] | ≈ 3–4 h beyond CP10 | Pipal et al.: six of eight hosted models stayed within 2 pp up to 100 items;\[48\]\[49\] unknown for a 4-bit 31B multi-label hierarchy | moderate; do after CP10 |
| MoE classifier (CP30) | 50–75% of residual (low confidence) | unknown | test |
| Small trained classifier (CP7) | most of residual | unknown | longer-term |
| Single stronger judge | about 0 (more time per call) | possibly positive | only after CP20 lifts the cap |

**Recommendation:** fix C5's prompt order and Λ_V first, because they carry no quality risk. Then cut the panel to at most one current judge with a random order, behind an s_P-gated cascade.

### Q2. Is the unanimity rule sound?

No. On the pilot's own figures it flags almost everything, while the labels say most targets are supported (CP11). It does not follow the panel literature, which pools by vote or average (CP8).\[15\] There are three published alternatives.

- **(a) A learned aggregator.** For example, a Bayesian logistic model of y on s_P, the vote share of the chosen judge or judges, and an order term, with weakly informative priors given 84 labels.
- **(b) A latent-class model.** Use Dawid–Skene (Dawid & Skene 1979, JRSS C 28(1):20–28, doi:10.2307/2346806), which estimates rater error rates "even when the … 'true' response is not available", or a Bayesian extension, with Z_t ∈ {0, 1}, judge-specific confusion parameters, a target × judge random effect to absorb correlation between orders, and s_P as a class-conditional emission, anchored by the labelled targets. With only two judge families whose errors are correlated, the model is weakly identified without labels.
- **(c) Selective prediction with a guarantee.** Threshold any of these scores using Trust-or-Escalate, LTT or CRC (CP9).

What these need from the labels is human labels drawn at random from the targets the rule will be applied to. STr and SDv are model-drafted, so a guarantee built on them certifies agreement with the hosted model (CP24). Sample size, by my arithmetic: with n accepted labelled targets and zero errors, the one-sided 1−δ bound on precision is δ^{1/n}. For precision ≥ 0.90 at δ = 0.1 you need n ≥ 22 accepted and all correct. For ≥ 0.95 you need n ≥ 45. With one error the requirement roughly doubles. Labels come in at most 5 per event, so treat events as the exchangeable units.

**Recommendation:** fit (a) on STr ∪ SDv for development. Collect about 100–150 new unaided owner labels on a random sample of dev and new events, and set the threshold with LTT at a pre-declared precision. Keep (b) as a sensitivity analysis.

### Q3. Is the model choice right for this hardware?

Gemma 4 31B-it is current (released in April 2026 under Apache 2.0, with a 256K context).\[26\]\[30\]\[31\] At 4 bits it fits, but C5's workload is prefill-bound, which is where dense 31B models are slowest. The oMLX community figure is about 200 prompt tok/s on an M4 Max with a 40-core GPU.\[25\] The judges (Qwen2.5-14B, Mistral-Nemo 12B) are stale (CP14). Speculative decoding speeds up decode, not prefill, so it does little for C5; it could help the judges, if your runtime supports a matched draft model. Continuous batching helps the judges (CP31). I found no published benchmark of quantized open-weight models on deductive multi-label classification of financial disclosures. The nearest evidence is Halterman & Keith's codebook study and the batching study of Pipal et al. Neither involves 4-bit local models.

**Recommendation:** keep Gemma 4 31B for C3. For C5, A/B test the QAT 31B against the 26B-A4B MoE on the train gold. For judges, once CP20 lifts the 14B cap, try one current non-Gemma model of about 24–32B, or a Bespoke-MiniCheck-7B-style checker for σ.

### Q4. How can the manual labels be kept through a method change?

Re-key them by content (CP19). This is better than freezing old runs, which keeps the labels but strands them on obsolete targets, and better than re-labelling, which wastes owner time. y^σ keys on (h(x_d), quote spans, normalized claim). y^φ keys on (claim, k, codebook version). Freeze C3, which costs only 1.4 h. Then every claim and its spans reproduce exactly, and all 94 support labels map one-to-one under any change to C5, C6 or C7. If C3 must change, map old to new by identical quote-span sets and have the owner confirm any claim rewording; the number of cases is small. G, IP and HN bind to canonical text and survive everything except a canonicalization change.

**Recommendation:** implement content keys before any other change, and confirm the one-to-one mapping on the current train and dev runs.

### Q5. What would relaxing the local-only rule buy?

**(a) Staying local.** Everything in Part 3, ranks 1–8 and 12–14: about 4–6× per pass by my estimate.

**(b) Renting or hosting.** Prices checked on 27 November 2026: RunPod H100 PCIe 80 GB at $2.89/h and A100 80 GB at $2.09–2.19/h (page updated 25 November 2026, https://www.runpod.io/pricing); Lambda HGX H100 at $4.59 per GPU-hour (https://lambda.ai/service/gpu-cloud/pricing); Gemma 4 31B-it on OpenRouter from $0.10 per 1M input tokens and $0.34 per 1M output tokens (https://openrouter.ai/google/gemma-4-31b-it). \[50\]\[51\]\[52\]

Arithmetic: a train pass's token volume (8.27M classifier input tokens plus 8.27M judge input and 0.62M judge output) comes to about $1.9 at Gemma rates. The full corpus is about $25–35, assuming judge families cost about the same; I did not check Qwen-class prices. A rented H100 would cost tens to low hundreds of dollars for the corpus, but I found no sourced throughput figure for this workload.

Quality gain: the literature supports larger and newer judges agreeing better, and Jung et al. show that cascades reach higher human agreement than single judges.\[17\] I found no quantified gain for this task.

Trade-offs: the release texts are public SEC filings, so rights risk is low, but check providers' data-retention terms. On reproducibility, the OpenRouter page lists DeepInfra serving the same model at both fp4 and fp8, so the same model name does not guarantee the same numerics.\[50\] Pin provider and precision, or rent a GPU and pin the weights. Shared-family risk: when a judge or classifier comes from the drafter's family, its agreement with G is inflated, as LLM-assisted labels raise measured LLM performance (Schroeder et al. 2025).\[37\]

**Recommendation:** never use the drafter's family in evaluation runs. If you do use it, evaluate it only against IP. Rent a GPU for the one-off corpus run only after ranks 1–3, so that you are not paying for the waste.

### Q6. Is the re-verification design proportionate?

No (CP18). Keys should be digests, not bundles. Each document's x_d and each output blob should be stored once, under its own hash. Each quote record carries (h(x_d), a, b, h(q)). C4's full check runs once, at write, and later reads verify the digests. A replay then compares output digests and does not re-derive every invariant. A Merkle-style digest of a run (a run manifest of its output digests) makes "same run" a 32-byte comparison. This is the design of Bazel's action cache and CAS, documented in the Bazel remote-caching docs and the REAPI v2 spec (CP18).

**Recommendation:** verify at write and check digests at read. Keep a scheduled full re-verification, for example weekly or before export, as the safeguard.

### Q7. Is exhaustive windowed traversal the right discovery design?

Yes for coverage, and it is cheap (CP29). Long-context evidence such as NoLiMa argues against reading whole releases in one pass if recall is the priority.\[42\] A hierarchical or document-level pass would save at most 1.4 h. The real cost of windows is the duplicate claims passed downstream.

**Recommendation:** keep 4,000-character windows. Add a small overlap, or a boundary check, for claims that span windows (C3 assumption 1), and deduplicate claims before C5. Measure the duplicate rate first.

### Q8. Is the evaluation design adequate for a 28-event pilot?

It is adequate as a feasibility screen, not as a set of gates (CP25, CP26). Bootstrap lower bounds from 8 clusters are unstable, unpaired comparisons waste power, and reusing dev invites overfitting. κ is a defensible statistic for the joint y, whose implied prevalence is about 65% (CP27). For y^σ, with 2 negatives, no agreement statistic is informative: specificity is unidentified.

**Recommendation:** use paired per-event differences with exact sign-flip tests and pre-declared margins. Report sensitivity and specificity, or specific agreements, with exact intervals. Collect at least 20–30 σ-negative unaided labels, for example by sampling targets that s_P scores low. Keep TG sealed for one final comparison.

## Caveats

- The search budget ran out before primary sources on quantization quality loss could be retrieved; claims on that topic are labelled as extrapolation.
- Throughput figures come from community benchmarks (oMLX) and preprints (SiliconBench, vllm-mlx), not from your machine. Every time estimate scales with your actual prompt rate, which should be measured once (CP10's check).
- Several inferences rest on the description's figures, notably the 41 joint positives and the codebook's token share. If those readings are wrong, CP11 and CP10's sizes change, though not their direction.

## Sources

1. [\[2310.17721\] From Transcripts to Insights: Uncovering Corporate Risks Using Generative AI](https://arxiv.org/abs/2310.17721)
2. [EconPapers: Firm-Level Political Risk: Measurement and Effects](https://econpapers.repec.org/RePEc:oup:qjecon:v:134:y:2019:i:4:p:2135-2202.)
3. [MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents](https://www.alphaxiv.org/abs/2404.10774v1)
4. [Prediction-powered inference](https://www.science.org/doi/10.1126/science.adi6000)
5. [\[PDF\] Prediction-powered inference](https://www.semanticscholar.org/paper/Prediction-powered-inference-Angelopoulos-Bates/96f75d06ce8bc26128f0af0071b374d065bf7d64)
6. [\[2306.04746v1\] Using Large Language Model Annotations for Valid Downstream Statistical Inference in Social Science: Design-Based Semi-Supervised Learning](https://arxiv.org/abs/2306.04746v1)
7. [Large Language Model Hacking: Quantifying the Hidden Risks of Using LLMs for Text Annotation](https://arxiv.org/pdf/2509.08825)
8. [Firm-Level Political Risk](https://www.policyuncertainty.com/firm_pr.html)
9. [From Transcripts to Insights: Uncovering Corporate Risks Using Generative AI](https://arxiv.org/html/2310.17721)
10. [\[PDF\] Codebook LLMs: Evaluating LLMs as Measurement Tools for Political Science Concepts](https://www.semanticscholar.org/paper/Codebook-LLMs:-Evaluating-LLMs-as-Measurement-Tools-Halterman-Keith/957438737fe594119c99124d2e853ecde9016c75)
11. [Codebook LLMs: Evaluating LLMs as Measurement Tools for Political Science Concepts](https://ideas.repec.org/a/cup/polals/v34y2026i2p188-204_3.html)
12. [When Better Codebooks Are Not Enough: Predictive Performance and Behavioral Reliability in LLM Political Event Coding](https://arxiv.org/pdf/2606.06781)
13. [Replacing Judges with Juries: Evaluating LLM Generations with a Panel of](https://arxiv.org/pdf/2404.18796)
14. [Who judges the judges? Governance from metrics: a runtime framework for continuous LLM compliance monitoring](https://arxiv.org/pdf/2605.24737)
15. [🧑‍⚖️ "Replacing Judges with Juries" using distilabel](https://huggingface.co/blog/alvarobartt/replacing-judges-with-juries-distilabel)
16. [Trust or Escalate: LLM Judges with Provable Guarantees for Human Agreement](https://www.alphaxiv.org/abs/2407.18370)
17. [TRUST OR ESCALATE: LLM JUDGES WITH PROVABLE GUARANTEES FOR HUMAN AGREEMENT](https://arxiv.org/pdf/2407.18370)
18. [ICLR Oral Trust or Escalate: LLM Judges with Provable Guarantees for Human Agreement](https://iclr.cc/virtual/2025/oral/31838)
19. [Trust or Escalate: LLM Judges with Provable Guarantees for Human Agreement - 专知论文](https://www.zhuanzhi.ai/paper/acca348b378da2b8c75c5dad9115efa8)
20. [llama.cpp/tools/server/README.md at master · ggml-org/llama.cpp · GitHub](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
21. [--- name: mlx-apple-silicon](https://raw.githubusercontent.com/plurigrid/asi/main/skills/mlx-apple-silicon/SKILL.md)
22. [mlx-lm vs oMLX: What an Honest Benchmark Reveals](https://medium.com/macoclock/mlx-lm-vs-omlx-i-was-wrong-about-the-winner-8f36be328069)
23. [GitHub - pierre427/mlx-lm-unified: MLX-LM serving stack for Apple Silicon: self-speculative decoding, automatic prefix caching, fused Metal kernels, and megakernel decode lanes. · GitHub](https://github.com/pierre427/mlx-lm-unified)
24. [Explore large language models on Apple silicon with MLX - WWDC25 - Videos - Apple Developer](https://developer.apple.com/videos/play/wwdc2025/298/)
25. [gemma-4-31B-it-qat on M4 Max (40c) — oMLX Benchmark](https://omlx.ai/benchmarks/e37o04o1)
26. [Gemma 4](https://lmstudio.ai/models/gemma-4)
27. [SiliconBench: Speed, Memory, and Fidelity for LLM Serving on Unified-Memory Desktops](https://arxiv.org/pdf/2609.19169)
28. [llama.cpp/tools/server/README.md at main · llmsforall/llama.cpp · GitHub](https://github.com/llmsforall/llama.cpp/blob/main/tools/server/README.md)
29. [GitHub - Liyan06/MiniCheck: MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents \[EMNLP 2024\] · GitHub](https://github.com/Liyan06/MiniCheck)
30. [Gemma (language model)](<https://en.wikipedia.org/wiki/Gemma_(language_model)>)
31. [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/)
32. [google/gemma-4-31B-it-qat-w4a16-ct · Hugging Face](https://huggingface.co/google/gemma-4-31B-it-qat-w4a16-ct)
33. [Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge - ACL Anthology](https://aclanthology.org/2025.ijcnlp-long.18/)
34. [Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge](https://arxiv.org/html/2406.07791v9)
35. [Reliability without Validity: A Systematic, Large-Scale Evaluationof LLM-as-a-Judge Models Across Agreement, Consistency, and Bias](https://arxiv.org/html/2606.19544v1)
36. [Gemma 4 31B on a 24GB GPU: Which Size Fits Which Card](https://tech-insider.org/google-gemma-4-open-model-benchmarks-2026/)
37. <https://arxiv.org/pdf/2507.15821>
38. [arXiv:1605.04481v3 \[cs.CL\] 21 Sep 2016 Anchoring and Agreement in Syntactic](https://arxiv.org/pdf/1605.04481)
39. [Anchoring and Agreement in Syntactic Annotations](https://arxiv.org/html/1605.04481)
40. [A comparison of Cohen’s Kappa and Gwet’s AC1 when calculating inter-rater reliability coefficients: a study conducted with personality disorder samples](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3643869/)
41. [Gwet's AC1 is not a substitute for Cohen's kappa](https://pmc.ncbi.nlm.nih.gov/articles/PMC10205778/)
42. [NoLiMa: Long-Context Evaluation Beyond Literal Matching](https://arxiv.org/html/2502.05167v1)
43. [NoLiMa: Long-Context Evaluation Beyond Literal Matching](https://proceedings.mlr.press/v267/modarressi25a.html)
44. [llama.cpp: tools/server/README.md](https://fossies.org/linux/llama.cpp/tools/server/README.md)
45. [Native LLM and MLLM Inference at Scale on Apple Silicon](https://arxiv.org/pdf/2601.19139)
46. [Batch Prompting: Efficient Inference with Large Language Model APIs Zhoujun](https://arxiv.org/pdf/2301.08721)
47. [Batch Prompting: Efficient Inference with Large Language Model APIs](https://arxiv.org/html/2301.08721v2.pdf)
48. [Researchers waste 80% of LLM annotation costs by classifying one text at a time†](https://arxiv.org/html/2604.03684v1)
49. [Researchers waste 80% of LLM annotation costs by classifying one text at a time](https://arxiv.org/pdf/2604.03684)
50. [Gemma 4 31B - API Pricing & Benchmarks](https://openrouter.ai/google/gemma-4-31b-it)
51. [GPU Cloud Pricing | Per-Second H100, A100, RTX | Runpod](https://www.runpod.io/pricing)
52. [GPU cloud pricing: rent NVIDIA H100, H200, and B200 | Lambda](https://lambda.ai/service/gpu-cloud/pricing)
