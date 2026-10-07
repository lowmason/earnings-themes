"""Entirely invented hand matrix, independent of any research/gold reader.

The mixed-policy matrix is count-only adjudication data, never one accepted run.
The public input constructor binds a separate actual scripted source/support/run.
"""

import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, date, datetime
from importlib import import_module
from types import SimpleNamespace

import polars as pl
from earnings_core import (
    ArtifactRef,
    CanonicalDocument,
    DocumentElement,
    ElementType,
    MaskCategory,
    OverlayMask,
    RightsStatus,
    TextSpan,
    digest,
    sha256_hex,
)
from earnings_themes.analysis import records as r
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import codebook_hash
from earnings_themes.coding.records import CodingPolicy
from earnings_themes.extraction.records import Parameters
from earnings_themes.support.records import (
    CodebookReference,
    JudgeIdentity,
    RuntimeIdentity,
)

_coding = import_module("packages.earnings-themes.tests.coding.cases")
FixturePolicy = _coding.FixturePolicy
invented_codebook = _coding.invented_codebook
make_assessed_case = _coding.make_assessed_case
make_coding_run = _coding.make_coding_run
make_proposal_job = _coding.make_proposal_job
make_sources = _coding.make_sources

NOW = datetime(2026, 10, 5, tzinfo=UTC)
Q1 = date(2025, 3, 31)
Q2 = date(2025, 6, 30)
HASH = digest("invented-stage10-binding")
EVENTS = (
    "A-Q1",
    "A-Q2",
    "B-Q1",
    "B-Q2",
    "C-Q1",
    "D-Q1",
    "E-Q1",
    "F-Q1",
    "G-Q1",
    "H-Q1",
)


def make_book(base):
    book = invented_codebook(base)
    child = book.themes[0].model_copy(
        update={
            "theme_id": "capacity_expansion",
            "parent_id": "capacity",
            "label": "Invented expansion",
        }
    )
    book = book.model_copy(
        update={
            "codebook_id": "stage10-invented",
            "themes": (book.themes[0], child, book.themes[1]),
        }
    )
    return book.model_copy(update={"content_hash": codebook_hash(book)})


def reference(book):
    return CodebookReference(
        codebook_id=book.codebook_id,
        codebook_version=book.codebook_version,
        content_hash=book.content_hash,
    )


def event(event_id):
    issuer = event_id[0]
    return r.ExpectedEvent(
        event_id=event_id,
        entity_id=issuer,
        cik=str(ord(issuer)).zfill(10),
        period_end=Q2 if event_id.endswith("Q2") else Q1,
        fiscal_year=2025,
        fiscal_quarter=2 if event_id.endswith("Q2") else 1,
        eligibility_status="eligible",
        eligibility_reason="member_at_publication",
        membership_assertion_id="invented-membership-" + issuer,
        event_manifest_hash=HASH,
        pilot_hash=HASH,
    )


def make_policy(event_ids=EVENTS):
    return r.AnalysisPolicy(
        population_id="stage10-invented",
        event_ids=tuple(sorted(event_ids)),
        population_hash=HASH,
        mask_policy_id="invented-mask",
        mask_policy_version="1",
        include_family_view=True,
        scope="fixture",
    )


def make_families(book):
    values = {
        "schema_version": 1,
        "mapping_id": "invented-families",
        "version": 1,
        "codebook": reference(book).model_dump(mode="json"),
        "memberships": (
            ("capacity", "operations"),
            ("capacity_expansion", "expansion"),
            ("capacity_expansion", "operations"),
        ),
        "family_labels": (
            ("expansion", "Invented expansion"),
            ("operations", "Invented operations"),
        ),
    }
    values["content_hash"] = r.family_map_hash(values)
    return r.ThemeFamilyMap.model_validate_json(__import__("json").dumps(values))


def metadata(bundle, expected):
    raw = ("Invented raw snapshot for " + expected.event_id).encode()
    artifact = ArtifactRef.for_bytes(
        raw,
        media_type="text/plain",
        storage_ref="invented/" + digest(raw.hex()) + ".txt",
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="Invented fixture permission",
    )
    row = r.DocumentMetadata(
        doc_id=bundle.document.doc_id,
        event_id=expected.event_id,
        entity_id=expected.entity_id,
        cik=expected.cik,
        publisher="Invented publisher",
        source_url="https://example.invalid/invented-release",
        source_document_id=bundle.document.source_document_id,
        raw_artifact=artifact,
        raw_hash=artifact.content_sha256,
        canonical_hash=bundle.document.canonical_hash,
        canonicalization_version=bundle.document.canonicalization_version,
        parser_version="invented-1",
        canonical_manifest_hash=HASH,
        mask_policy_id="invented-mask",
        mask_policy_version="1",
        mask_manifest_hash=HASH,
        filing_at=None,
        published_at=None,
        event_at=None,
        retrieved_at=NOW,
        period_end=expected.period_end,
        fiscal_year=expected.fiscal_year,
        fiscal_quarter=expected.fiscal_quarter,
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="Invented fixture permission",
        access_status="available",
        retain_text=True,
        export_text=True,
        retain_raw=True,
        export_raw=True,
        retain_capture=False,
    )
    return row, r.RawSnapshot(row.doc_id, artifact, raw)


def mask_hash(payload):
    manifest = payload["manifest"]
    document = payload["document"]
    return digest(
        {
            "doc_id": document["doc_id"],
            "canonical_hash": document["canonical_hash"],
            "mask_policy_id": manifest["mask_policy_id"],
            "mask_policy_version": manifest["mask_policy_version"],
            "masks": payload["masks"],
        }
    )


def canonical_snapshot(bundle, meta, raw):
    from earnings_core import apply_masks
    from earnings_ingestion.canonical import CanonicalizationManifest, Canonicalized
    from earnings_ingestion.canonical.serialize import to_fixture_json

    manifest = CanonicalizationManifest(
        canonicalization_version=bundle.document.canonicalization_version,
        components={"parser": "invented-1"},
        lxml_version="invented-1",
        libxml2_version="invented-1",
        python_version="invented-1",
        source_document_id=bundle.document.source_document_id,
        raw_sha256=meta.raw_hash,
        raw_bytes=len(raw.data),
        encoding="utf-8",
        encoding_basis="invented",
        element_counts=dict(Counter(e.type.value for e in bundle.elements)),
        image_count=0,
        replacement_characters=0,
        retypes={},
        limitations=(),
        mask_policy_id=meta.mask_policy_id,
        mask_policy_version=meta.mask_policy_version,
        mask_count=len(bundle.masks),
    )
    result = Canonicalized(
        document=bundle.document,
        elements=bundle.elements,
        masked=apply_masks(
            bundle.document,
            bundle.masks,
            policy_id=meta.mask_policy_id,
            policy_version=meta.mask_policy_version,
        ),
        manifest=manifest,
    )
    return r.CanonicalSnapshot(
        bundle.document.doc_id, to_fixture_json(result).encode("utf-8")
    )


def make_inputs(
    base,
    template,
    root,
    *,
    review=False,
    claims=None,
    themes=("capacity_expansion",),
    documents=1,
    quote_labels=("U1", "U2"),
    first_text=None,
    contribution="supporting",
    caches=False,
    masked=False,
    themes_by_document=None,
    copy_first_text=None,
    assignment_action=None,
    retain_text=True,
    classification_reply=None,
    event_ids_by_document=None,
    extraction_options=None,
    selected_expected=None,
    extra_acquisition=(),
    original_slots=None,
    claim_order=None,
    support_ceilings=None,
    selected_universe_hash="c" * 64,
):
    first_text = first_text or "Invented 🛠 press expanded."
    text = first_text + "\nInvented 🛠 press expanded."
    document = CanonicalDocument.create(
        source_document_id="stage10-invented-A-Q1",
        canonicalization_version="invented-1",
        canonical_text=text,
    )
    boundary = text.index("\n")
    elements = tuple(
        DocumentElement.create(
            document, ElementType.PARAGRAPH, TextSpan(start=start, end=end)
        )
        for start, end in ((0, boundary), (boundary + 1, len(text)))
    )
    masks = (
        (
            OverlayMask(
                doc_id=document.doc_id,
                canonical_hash=document.canonical_hash,
                span=elements[0].span,
                category=MaskCategory.SAFE_HARBOR,
                policy_id="invented-mask",
                policy_version="1",
            ),
        )
        if masked
        else ()
    )
    bundle = Bundle("stage10-invented", document, elements, masks)
    bundles = [bundle]
    for i in range(1, documents):
        other_doc = CanonicalDocument.create(
            source_document_id="stage10-invented-copy-" + str(i),
            canonicalization_version="invented-1",
            canonical_text=(copy_first_text + text[boundary:])
            if copy_first_text
            else text,
        )
        other_elements = tuple(
            DocumentElement.create(
                other_doc,
                ElementType.PARAGRAPH,
                TextSpan(start=e.span.start, end=e.span.end),
            )
            for e in elements
        )
        bundles.append(Bundle("stage10-invented", other_doc, other_elements, ()))
    if extraction_options and extraction_options.get("no_units"):
        bundles = [replace(b, elements=()) for b in bundles]
        bundle = bundles[0]
    claim_texts = (
        ("Invented equipment grew.", "Invented second equipment claim.")
        if claims is None
        else claims
    )
    if extraction_options:
        from earnings_themes.extraction.adapters import (
            AdapterError,
            ModelReply,
            ScriptedAdapter,
        )
        from earnings_themes.extraction.cache import CachedAdapter
        from earnings_themes.extraction.records import (
            Ceilings,
            ExtractionPolicy,
            ExtractionProblem,
        )
        from earnings_themes.extraction.run import extract_run
        from earnings_themes.extraction.store import StoredRun, read_run, write_run
        from earnings_themes.support.records import SupportSources

        options = extraction_options
        mode = options.get("mode", "complete")

        def reply(request):
            if (
                mode == "failed"
                or mode == "partial"
                and not request.subject.window_id.startswith("w-0-")
            ):
                raise AdapterError(ExtractionProblem.TRANSPORT_ERROR)
            if mode == "replay":
                raise AssertionError("fixture_replay_dispatch_forbidden")
            return ModelReply(
                model="scripted",
                text=json.dumps(
                    {
                        "candidates": [
                            {"quote_labels": ["U1"], "claim": c} for c in claim_texts
                        ]
                    }
                ),
            )

        adapter = ScriptedAdapter(reply)
        if mode == "replay":
            adapter = CachedAdapter(adapter, root / "extraction-cache", "replay")
        result = extract_run(
            tuple(replace(b, elements=b.elements[:1]) for b in bundles)
            if mode == "subset"
            else tuple(bundles),
            adapter,
            ExtractionPolicy(window_budget=options.get("budget", 4000)),
            template,
            Ceilings(
                requests_per_document=options.get("requests", 8),
                requests_per_run=options.get("run_requests", 8 * documents),
                tokens_per_run=1000000,
            ),
            run_id="invented-extraction",
            started_at=NOW,
            software={"fixture": "1"},
        )
        stored = read_run(
            write_run(root / "extraction", StoredRun.of(result), tuple(bundles))
        )
        sources = SupportSources(stored, tuple(bundles), make_book(base), HASH)
    else:
        sources = make_sources(
            make_book(base),
            bundle,
            template,
            claim_texts=claim_texts,
            quote_labels=quote_labels,
            other_bundles=tuple(bundles[1:]),
            extraction_directory=root / "extraction",
        )
    selected_events = (
        tuple(selected_expected[:documents])
        if selected_expected is not None
        else tuple(
            event(key) for key in (event_ids_by_document or ("A-Q1",) * documents)
        )
    )
    expected_rows = tuple(
        sorted(
            selected_expected
            or {row.event_id: row for row in selected_events}.values(),
            key=lambda row: row.event_id,
        )
    )
    metadata_rows = []
    raw_rows = []
    canonical_rows = []
    acquisitions = []
    for i, selected in enumerate(bundles):
        expected = selected_events[i]
        meta, raw = metadata(selected, expected)
        if not retain_text:
            meta = meta.model_copy(update={"retain_text": False, "export_text": False})
        canonical = canonical_snapshot(selected, meta, raw)
        payload = json.loads(canonical.data)
        meta = meta.model_copy(
            update={
                "canonical_manifest_hash": digest(payload["manifest"]),
                "mask_manifest_hash": mask_hash(payload),
            }
        )
        metadata_rows.append(meta)
        if meta.retain_raw:
            raw_rows.append(raw)
        canonical_rows.append(canonical)
        acquisitions.append(
            r.AcquisitionStatus(
                event_id=expected.event_id,
                document_id=original_slots[i].document_id
                if original_slots
                else "release-A-Q1-" + str(i),
                state="parsed",
                missing_reason=None,
                failure_reason=None,
                doc_id=selected.document.doc_id,
                source_document_id=selected.document.source_document_id,
                raw_hash=meta.raw_hash,
                accession=None,
                exhibit=None,
                retrieved_at=NOW,
                state_run_id="invented-acquisition",
                state_schema_version=1,
                pilot_hash=expected.pilot_hash,
            )
        )
    acquisitions.extend(extra_acquisition)
    from earnings_themes.analysis.consume import analysis_provenance_hash

    provenance = analysis_provenance_hash(
        selected_universe_hash=selected_universe_hash,
        expected=expected_rows,
        acquisition=tuple(acquisitions),
        metadata=tuple(metadata_rows),
        canonical_snapshots=tuple(canonical_rows),
    )
    sources = replace(sources, provenance_hash=provenance)
    identity = JudgeIdentity(
        family="invented-classifier",
        runtime=RuntimeIdentity(
            model_id="invented-classifier",
            revision="1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="1",
        ),
        input_limit=10000,
        output_limit=2048,
        hosting="scripted",
        weight_license=None,
    )
    text_policy = "Classify the invented expansion."

    policy = CodingPolicy(
        prompt_text=text_policy,
        prompt_hash=sha256_hex(text_policy.encode()),
        parameters=Parameters(max_tokens=64),
    )
    job = make_proposal_job(sources, policy, identity, root)
    per_doc_themes = (
        dict(zip((b.document.doc_id for b in bundles), themes_by_document))
        if themes_by_document is not None
        else {}
    )
    replies = (
        [
            {"theme_ids": list(per_doc_themes.get(c.doc_id, themes)), "attributes": {}}
            for c in sources.stored_run.claims
        ]
        if classification_reply is None
        else [classification_reply] * (2 * len(sources.stored_run.claims))
    )
    proposals, _ = job.run(
        replies, claim_order=claim_order(sources) if claim_order else None
    )
    assessed = make_assessed_case(
        proposals, sources, root, contribution=contribution, ceilings=support_ceilings
    )
    assignment_policy = None if review else FixturePolicy(proposals, assessed.support)
    if assignment_action is not None and not review:
        from earnings_themes.coding.records import PolicyVote

        class ActionPolicy(FixturePolicy):
            def evaluate(self, view):
                return PolicyVote(action=assignment_action)

        assignment_policy = ActionPolicy(proposals, assessed.support)
        assignment_policy.reference = assignment_policy.reference.model_copy(
            update={
                "policy_id": "invented-row-action",
                "policy_hash": digest(("invented-row-action", assignment_action)),
            }
        )
    coding = make_coding_run(assessed, assignment_policy)
    from earnings_themes.coding.store import read_coding_run, write_coding_run

    coding = read_coding_run(
        write_coding_run(
            root / "coding", coding, sources, assessed.support, assignment_policy
        )
    )
    from earnings_themes.coding.cache import CodingCache
    from earnings_themes.support.cache import SupportCache

    return r.AnalysisInputs(
        sources=sources,
        support=assessed.support,
        coding=coding,
        assignment_policy=assignment_policy,
        expected=expected_rows,
        acquisition=tuple(acquisitions),
        metadata=tuple(metadata_rows),
        copies=(),
        no_theme=(),
        provenance_hash=sources.provenance_hash,
        selected_universe_hash=selected_universe_hash,
        raw_verification=(
            r.RawCacheVerification(
                stage="extraction",
                status="not_bound",
                bindings=(),
                method="schema-1-no-raw-bindings",
                version="1",
            ),
        ),
        raw_caches=r.RawCacheInputs(
            CodingCache(root / "classifier-cache", "replay") if caches else None,
            SupportCache(root / "support-cache", "replay") if caches else None,
        ),
        raw_snapshots=tuple(raw_rows),
        analysis_policy=make_policy(
            tuple(row.event_id for row in expected_rows)
        ).model_copy(update={"population_hash": expected_rows[0].pilot_hash}),
        canonical_snapshots=tuple(canonical_rows),
        fixture_authorization=r.FixtureAuthorization(
            "stage10-invented",
            expected_rows[0].event_manifest_hash,
            expected_rows[0].pilot_hash,
            provenance,
        ),
    )


def make_counting_case(book, assignment_policy):
    policy = make_policy()
    families = make_families(book)
    expected = tuple(event(key) for key in EVENTS)
    bookref = reference(book)
    quotes = []
    observations = []
    claims = []
    links = []
    copies = []
    completions = []
    coverage = []
    classifications = []
    decisions = []
    novelty = []
    assignment_claims = []
    for key, theme, masks in (
        ("A-Q1", "capacity_expansion", ()),
        ("B-Q1", "capacity", ("invented-mask-B",)),
    ):
        e = event(key)
        doc = "invented-doc-" + key
        quote = "invented-quote"
        q = r.QuoteAudit(
            doc_id=doc,
            quote_id=quote,
            canonical_hash=HASH,
            start=2,
            end=18,
            element_id="invented-element",
            validator_version="exact-cp-1",
            mask_ids=masks,
            source_run_id="invented-source",
            source_run_hash=HASH,
            metadata_ref=HASH,
            quote_text="Invented 🛠 text",
        )
        quotes.append(q)
        observations.append(
            r.Observation(
                **q.model_dump(),
                event_id=key,
                entity_id=e.entity_id,
                cik=e.cik,
                period_end=e.period_end,
                fiscal_year=e.fiscal_year,
                fiscal_quarter=e.fiscal_quarter,
                theme_id=theme,
                assignment_id="invented-assignment-" + key,
                codebook_id=book.codebook_id,
                codebook_version=book.codebook_version,
                codebook_hash=book.content_hash,
                headline_eligible=not bool(masks),
                disclosure_group="invented-group-" + key,
                policy_kind="fixture",
                policy_hash=assignment_policy.policy_hash,
                policy_scope="fixture",
                coding_run_id="invented-coding",
                coding_run_hash=HASH,
                support_run_id="invented-support",
                support_run_hash=HASH,
                evidence_id="invented-evidence-" + key,
                published_at=None,
                retrieved_at=NOW,
                extracted_at=NOW,
            )
        )
        for index in range(2 if key == "A-Q1" else 1):
            claim = f"invented-claim-{key}-{index}"
            claims.append(
                r.ClaimAudit(
                    doc_id=doc,
                    claim_id=claim,
                    window_id="invented-window",
                    attempt_id="invented-attempt",
                    interpretation_hash=HASH,
                    interpretation="Invented interpretation",
                    original_quote_ids=(quote,),
                    source_run_id="invented-source",
                    source_run_hash=HASH,
                )
            )
            links.append(r.ClaimEvidence(doc_id=doc, claim_id=claim, quote_id=quote))
            classification_id = "invented-classification-" + claim
            decision_id = "invented-decision-" + claim
            classifications.append(
                r.ClassificationAudit(
                    classification_id=classification_id,
                    coding_run_id="invented-coding",
                    doc_id=doc,
                    claim_id=claim,
                    input_hash=HASH,
                    codebook=bookref,
                    status="completed",
                    reason=None,
                    attempt_ids=("invented-attempt",),
                    proposed_theme_ids=(theme,),
                )
            )
            decisions.append(
                r.DecisionAudit(
                    decision_id=decision_id,
                    coding_run_id="invented-coding",
                    doc_id=doc,
                    claim_id=claim,
                    theme_id=theme,
                    target_id="invented-target-" + claim,
                    codebook=bookref,
                    policy=assignment_policy,
                    status="accepted",
                    reason="policy_accept",
                    support_status="assessed",
                    flags=(),
                    missing=(),
                    original_quote_ids=(quote,),
                    supported_quote_ids=(quote,),
                    proposal_hash=HASH,
                    input_hash=HASH,
                    support_run_hash=HASH,
                )
            )
            from earnings_themes.coding.records import AssignmentClaimLink

            assignment_claims.append(
                AssignmentClaimLink(
                    assignment_id="invented-assignment-" + key,
                    doc_id=doc,
                    claim_id=claim,
                    decision_id=decision_id,
                    target_id="invented-target-" + claim,
                )
            )
        for suffix in ("", "-copy") if key == "A-Q1" else ("",):
            copies.append(
                r.CopyRow(
                    doc_id=doc + suffix,
                    event_id=key,
                    disclosure_group="invented-group-" + key,
                    representative_doc_id=doc,
                    canonical_hash=HASH,
                    copy_assertion_id="invented-copy-A" if key == "A-Q1" else None,
                    copy_assertion_hash=HASH if key == "A-Q1" else None,
                    rule_version="same-event-disclosure/1",
                    status="consistent",
                )
            )
    original_doc = "invented-doc-A-Q1"
    copied_doc = original_doc + "-copy"
    for rows in (
        observations,
        quotes,
        claims,
        links,
        classifications,
        decisions,
        assignment_claims,
    ):
        for row in tuple(rows):
            if row.doc_id != original_doc:
                continue
            updates = {"doc_id": copied_doc}
            for field in (
                "assignment_id",
                "claim_id",
                "classification_id",
                "decision_id",
                "target_id",
                "evidence_id",
            ):
                if field in type(row).model_fields:
                    updates[field] = getattr(row, field) + "-copy"
            rows.append(type(row).model_validate({**row.model_dump(), **updates}))
    outcomes = {
        "A-Q1": ("completed", (), 1, 0, 0, 0, 0, 0, 0, 0, True),
        "A-Q2": (
            "completed-no-theme",
            ("explicit_no_theme",),
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            True,
        ),
        "B-Q1": ("completed", (), 1, 1, 0, 0, 0, 0, 0, 0, True),
        "B-Q2": ("unavailable", ("not_found",), 0, 0, 0, 0, 0, 0, 0, 0, False),
        "C-Q1": ("partial", ("calibration_required",), 0, 0, 1, 0, 0, 0, 0, 0, False),
        "D-Q1": ("failed", ("parse_failed",), 0, 0, 0, 0, 0, 0, 0, 0, False),
        "E-Q1": ("restricted", ("rights_restricted",), 0, 0, 0, 0, 0, 0, 0, 0, False),
        "F-Q1": ("partial", ("valid_unmatched",), 0, 0, 0, 0, 0, 0, 0, 1, False),
        "G-Q1": ("partial", ("no_theme_unconfirmed",), 0, 0, 0, 1, 0, 0, 0, 0, False),
        "H-Q1": (
            "partial",
            ("assessment_refused", "assessment_flagged", "assessment_incomplete"),
            0,
            0,
            2,
            0,
            1,
            1,
            1,
            0,
            False,
        ),
    }
    declarations = []
    acquisitions = []
    for e in expected:
        (
            state,
            reasons,
            accepted,
            masked,
            review,
            rejected,
            refused,
            flagged,
            incomplete,
            unmatched,
            observable,
        ) = outcomes[e.event_id]
        available = state not in ("unavailable", "restricted", "failed")
        doc = "invented-doc-" + e.event_id
        declaration = None
        if e.event_id == "A-Q2":
            declaration = r.NoThemeDeclaration(
                doc_id=doc,
                canonical_hash=HASH,
                source_run_hash=HASH,
                coding_run_hash=HASH,
                support_run_hash=HASH,
                codebook=bookref,
                analysis_policy_hash=policy.content_hash,
                assignment_policy=assignment_policy,
                actor_id="invented-fixture-actor",
                declared_at=NOW,
                policy_scope="fixture",
            )
            declarations.append(declaration)
        if available:
            completion = r.DocumentCompletion(
                doc_id=doc,
                event_id=e.event_id,
                canonical_hash=HASH,
                source_run_hash=HASH,
                coding_run_hash=HASH,
                support_run_hash=HASH,
                codebook=bookref,
                assignment_policy=None if e.event_id == "C-Q1" else assignment_policy,
                analysis_policy_hash=policy.content_hash,
                traversal_complete=e.event_id != "H-Q1",
                classification_complete=True,
                assessment_complete=e.event_id != "H-Q1",
                decision_complete=e.event_id != "H-Q1",
                eligible_units=2,
                completed_windows=1,
                failed_windows=1 if e.event_id == "H-Q1" else 0,
                accepted_count=accepted,
                masked_count=masked,
                rejected_count=rejected,
                review_count=review,
                refused_count=refused,
                flagged_count=flagged,
                incomplete_count=incomplete,
                unmatched_count=unmatched,
                processing_state=state,
                reasons=reasons,
                declaration_hash=digest(declaration.model_dump(mode="json"))
                if declaration
                else None,
                observable=observable,
                policy_scope="fixture",
            )
            completions.append(completion)
            if e.event_id == "A-Q1":
                completions.append(
                    r.DocumentCompletion.model_validate(
                        {**completion.model_dump(), "doc_id": copied_doc}
                    )
                )
        acquisition_state = "parsed" if available else state
        acquisitions.append(
            r.AcquisitionStatus(
                event_id=e.event_id,
                document_id="release-" + e.event_id,
                state=acquisition_state,
                missing_reason=None if available else reasons[0],
                failure_reason="parse_failed" if state == "failed" else None,
                doc_id=doc if available else None,
                source_document_id="invented-source-" + e.event_id
                if available
                else None,
                raw_hash=HASH if available else None,
                accession=None,
                exhibit=None,
                retrieved_at=NOW if available else None,
                state_run_id="invented-state",
                state_schema_version=1,
                pilot_hash=HASH,
            )
        )
        fields = {
            "event_id": e.event_id,
            "entity_id": e.entity_id,
            "cik": e.cik,
            "period_end": e.period_end,
            "fiscal_year": e.fiscal_year,
            "fiscal_quarter": e.fiscal_quarter,
            "eligibility_status": e.eligibility_status,
            "eligibility_reason": e.eligibility_reason,
            "membership_assertion_id": e.membership_assertion_id,
            "expected": True,
            "available": available,
            "parsed": available,
            "observable": observable,
            "availability": "available"
            if available
            else "unavailable"
            if state == "failed"
            else state,
            "document_id": "release-" + e.event_id,
            "doc_ids": (doc, copied_doc)
            if e.event_id == "A-Q1"
            else (doc,)
            if available
            else (),
            "latest_state": state,
            "state_run_id": "invented-state",
            "state_schema_version": 1,
            "missing_reasons": reasons,
            "policy_scope": "fixture",
            "accepted_count": accepted,
            "masked_count": masked,
            "review_count": review,
            "rejected_count": rejected,
            "refused_count": refused,
            "flagged_count": flagged,
            "incomplete_count": incomplete,
            "unmatched_count": unmatched,
            "copy_refs": (HASH,) if e.event_id == "A-Q1" else (),
            "metadata_refs": (HASH,) if available else (),
            "completion_refs": (HASH,) if available else (),
        }
        coverage.append(
            r.CoverageRow(doc_type="release", speaker_role="not_applicable", **fields)
        )
        fields.update(
            available=False,
            parsed=False,
            observable=False,
            availability="not_yet_checked",
            document_id=None,
            doc_ids=(),
            latest_state="expected",
            state_run_id=None,
            state_schema_version=None,
            missing_reasons=("transcript_not_in_scope",),
            accepted_count=0,
            masked_count=0,
            review_count=0,
            rejected_count=0,
            refused_count=0,
            flagged_count=0,
            incomplete_count=0,
            unmatched_count=0,
            copy_refs=(),
            metadata_refs=(),
            completion_refs=(),
        )
        coverage.append(
            r.CoverageRow(doc_type="transcript", speaker_role="unknown", **fields)
        )
    # These are independent hand-normalized audit rows, not a mixed accepted run.
    for key, reason, support_status in (
        ("C-Q1", "calibration_required", "assessed"),
        ("F-Q1", "no_theme_fit", None),
        ("G-Q1", "policy_reject", "assessed"),
        ("H-Q1", "assessment_refused", "refused"),
        ("H-Q1", "assessment_flagged", "flagged"),
        ("H-Q1", "assessment_incomplete", "incomplete"),
    ):
        doc = "invented-doc-" + key
        claim = "invented-claim-" + key + "-" + reason
        quote = "invented-quote"
        if not any(row.doc_id == doc for row in quotes):
            quotes.append(
                r.QuoteAudit(
                    doc_id=doc,
                    quote_id=quote,
                    canonical_hash=HASH,
                    start=2,
                    end=18,
                    element_id="invented-element",
                    validator_version="exact-cp-1",
                    mask_ids=(),
                    source_run_id="invented-source",
                    source_run_hash=HASH,
                    metadata_ref=HASH,
                    quote_text="Invented audit 🛠 text",
                )
            )
        claims.append(
            r.ClaimAudit(
                doc_id=doc,
                claim_id=claim,
                window_id="invented-window",
                attempt_id="invented-attempt",
                interpretation_hash=HASH,
                interpretation="Invented audit interpretation",
                original_quote_ids=(quote,),
                source_run_id="invented-source",
                source_run_hash=HASH,
            )
        )
        links.append(r.ClaimEvidence(doc_id=doc, claim_id=claim, quote_id=quote))
        classification_id = "invented-classification-" + claim
        classifications.append(
            r.ClassificationAudit(
                classification_id=classification_id,
                coding_run_id="invented-coding",
                doc_id=doc,
                claim_id=claim,
                input_hash=HASH,
                codebook=bookref,
                status="completed",
                reason=None,
                attempt_ids=("invented-attempt",),
                proposed_theme_ids=() if key == "F-Q1" else ("capacity",),
            )
        )
        if key == "F-Q1":
            from earnings_themes.coding.records import NoveltyItem

            novelty.append(
                NoveltyItem(
                    novelty_id="invented-novelty",
                    coding_run_id="invented-coding",
                    classification_id=classification_id,
                    source_run_id="invented-source",
                    doc_id=doc,
                    claim_id=claim,
                    codebook=bookref,
                    input_hash=HASH,
                    original_quote_ids=(quote,),
                )
            )
        else:
            decisions.append(
                r.DecisionAudit(
                    decision_id="invented-decision-" + claim,
                    coding_run_id="invented-coding",
                    doc_id=doc,
                    claim_id=claim,
                    theme_id="capacity",
                    target_id="invented-target-" + claim,
                    codebook=bookref,
                    policy=None if key == "C-Q1" else assignment_policy,
                    status="rejected"
                    if key == "G-Q1"
                    else "refused"
                    if support_status == "refused"
                    else "review",
                    reason=reason,
                    support_status=support_status,
                    flags=("invented-support-flag",)
                    if support_status == "flagged"
                    else (),
                    missing=("missing_assessment",)
                    if support_status == "incomplete"
                    else (),
                    original_quote_ids=(quote,),
                    supported_quote_ids=(),
                    proposal_hash=HASH,
                    input_hash=HASH,
                    support_run_hash=HASH,
                )
            )
    rejections = [
        r.RejectionAudit(
            source_run_id="invented-source",
            doc_id="invented-doc-H-Q1",
            window_id="invented-window",
            attempt_id="invented-attempt",
            candidate_index=0,
            reason="unknown_label",
            element_ids=(),
        )
    ]
    rows = {
        "observations": observations,
        "quotes": quotes,
        "claims": claims,
        "claim_evidence": links,
        "assignment_claims": assignment_claims,
        "classifications": classifications,
        "decisions": decisions,
        "novelty": novelty,
        "rejections": rejections,
        "completions": completions,
        "coverage": coverage,
        "prevalence": [],
        "copies": copies,
        "evidence": [],
    }
    frames = {
        name: pl.DataFrame(
            [row.model_dump(mode="python") for row in rows[name]],
            schema=schema,
            strict=True,
        )
        for name, schema in r.TABLE_SCHEMAS.items()
    }
    return SimpleNamespace(
        book=book,
        policy=policy,
        families=families,
        expected=expected,
        acquisition=tuple(acquisitions),
        declarations=tuple(declarations),
        observations=tuple(observations),
        claim_evidence=tuple(links),
        copies=tuple(copies),
        completions=tuple(completions),
        coverage=tuple(coverage),
        tables=r.AnalysisTables(frames),
        rows=rows,
    )
