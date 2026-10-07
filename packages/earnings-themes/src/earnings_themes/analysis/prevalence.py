"""Distinct coverage units, hierarchy/family views, and reproducible analysis runs."""

from collections import Counter

import polars as pl
from earnings_core import digest

from earnings_themes.codebook import Codebook, codebook_hash
from earnings_themes.support.records import CodebookReference

from .completion import document_completions
from .consume import reverify_analysis_inputs
from .coverage import build_coverage
from .problems import AnalysisError
from .records import (
    TABLE_SCHEMAS,
    AnalysisInputs,
    AnalysisPolicy,
    AnalysisRun,
    AnalysisRunRecord,
    AnalysisTables,
    PrevalenceRow,
    ThemeFamilyMap,
    validate_analysis_tables,
)
from .rows import _run_hash, build_observations


def _views(
    book: Codebook, families: ThemeFamilyMap | None
) -> list[tuple[str, str, set[str]]]:
    parents = {t.theme_id: t.parent_id for t in book.themes}
    if len(parents) != len(book.themes) or codebook_hash(book) != book.content_hash:
        raise AnalysisError("mixed_codebook")
    descendants = {theme: {theme} for theme in parents}
    for theme, ancestor in parents.items():
        seen = {theme}
        while ancestor is not None:
            if ancestor not in parents or ancestor in seen:
                raise AnalysisError("hierarchy_conflict")
            descendants[ancestor].add(theme)
            seen.add(ancestor)
            ancestor = parents[ancestor]
    views = [("direct", t, {t}) for t in sorted(parents)]
    views += [
        ("parent", t, descendants[t])
        for t in sorted(parents)
        if len(descendants[t]) > 1
    ]
    if families is not None:
        families.validate_codebook(book)
        for family in sorted({f for _, f in families.memberships}):
            views.append(
                ("family", family, {t for t, f in families.memberships if f == family})
            )
    return views


def _counts(rows):
    units = {
        (r["entity_id"], r["period_end"])
        for r in rows
        if r["eligibility_status"] == "eligible"
    }
    return {
        "expected_count": len(units),
        "available_count": len(
            {
                (r["entity_id"], r["period_end"])
                for r in rows
                if r["available"] and r["eligibility_status"] == "eligible"
            }
        ),
        "parsed_count": len(
            {
                (r["entity_id"], r["period_end"])
                for r in rows
                if r["parsed"] and r["eligibility_status"] == "eligible"
            }
        ),
        "observable_count": len(
            {(r["entity_id"], r["period_end"]) for r in rows if r["observable"]}
        ),
        "excluded_count": len(
            units - {(r["entity_id"], r["period_end"]) for r in rows if r["observable"]}
        ),
        "missing_period_count": len(
            units - {(r["entity_id"], r["period_end"]) for r in rows if r["observable"]}
        ),
    }


def _rates(rows, positives):
    observed = {(r["entity_id"], r["period_end"]) for r in rows if r["observable"]}
    positive = positives & observed
    issuers = {e for e, _ in observed}
    equal_sum = sum(
        sum(e == issuer for e, _ in positive) / sum(e == issuer for e, _ in observed)
        for issuer in sorted(issuers)
    )
    return {
        "issuer_period": (float(len(positive)), len(observed)),
        "issuer_window": (float(len({e for e, _ in positive})), len(issuers)),
        "firm_quarter": (float(len(positive)), len(observed)),
        "equal_issuer_mean": (equal_sum, len(issuers)),
    }


def prevalence(
    tables: AnalysisTables,
    coverage: pl.DataFrame,
    book: Codebook,
    policy: AnalysisPolicy,
    families: ThemeFamilyMap | None,
) -> pl.DataFrame:
    """Count only complete coverage units; each issuer contributes at most once."""
    try:
        frames = dict(tables.frames)
        frames["coverage"] = coverage
        checked = validate_analysis_tables(AnalysisTables(frames))
        policy = AnalysisPolicy.model_validate(policy.model_dump())
        if families is not None and not policy.include_family_view:
            raise AnalysisError("policy_mismatch")
        views = _views(book, families)
        rows = list(checked.frames["coverage"].iter_rows(named=True))
        if {r["event_id"] for r in rows} != set(policy.event_ids) or any(
            r["policy_scope"] != policy.scope for r in rows
        ):
            raise AnalysisError("policy_mismatch")
        completions = list(checked.frames["completions"].iter_rows(named=True))
        if any(
            r["analysis_policy_hash"] != policy.content_hash
            or r["codebook"]
            != CodebookReference(
                codebook_id=book.codebook_id,
                codebook_version=book.codebook_version,
                content_hash=book.content_hash,
            ).model_dump(mode="python")
            for r in completions
        ):
            raise AnalysisError("policy_mismatch")
        observations = checked.frames["observations"]
        if observations.height and (
            set(observations["codebook_hash"]) != {book.content_hash}
            or set(observations["policy_scope"]) != {policy.scope}
        ):
            raise AnalysisError("mixed_codebook")
        # Document-qualified membership is checked before the m:1 coverage join.
        by_event = {r["event_id"]: r for r in rows if r["doc_type"] == "release"}
        for observation in observations.iter_rows(named=True):
            slot = by_event.get(observation["event_id"])
            if (
                slot is None
                or observation["doc_id"] not in slot["doc_ids"]
                or (observation["entity_id"], observation["period_end"])
                != (slot["entity_id"], slot["period_end"])
                or observation["theme_id"] not in {t.theme_id for t in book.themes}
            ):
                raise AnalysisError("invalid_references")
        positive_frame = (
            observations.filter(
                pl.col("headline_eligible") & (pl.col("mask_ids").list.len() == 0)
            )
            .join(
                coverage.select("event_id", "doc_type", "speaker_role", "observable"),
                on=["event_id", "doc_type", "speaker_role"],
                how="inner",
                validate="m:1",
            )
            .filter(pl.col("observable"))
        )
        output = []
        partitions = sorted({(r["doc_type"], r["speaker_role"]) for r in rows})
        for doc_type, role in partitions:
            selected = [
                r
                for r in rows
                if (r["doc_type"], r["speaker_role"]) == (doc_type, role)
            ]
            periods = sorted({r["period_end"] for r in selected})
            if not periods:
                continue
            for kind, view_id, themes in views:
                positives = {
                    (r["entity_id"], r["period_end"])
                    for r in positive_frame.iter_rows(named=True)
                    if (r["doc_type"], r["speaker_role"]) == (doc_type, role)
                    and r["theme_id"] in themes
                }
                groups = [
                    (
                        period,
                        [r for r in selected if r["period_end"] == period],
                        ("issuer_period",),
                    )
                    for period in periods
                ]
                groups.append(
                    (
                        None,
                        selected,
                        ("issuer_window", "firm_quarter", "equal_issuer_mean"),
                    )
                )
                for period, group, units in groups:
                    rates = _rates(group, positives)
                    reasons = sorted(
                        {
                            reason
                            for r in group
                            if not r["observable"]
                            for reason in r["missing_reasons"]
                        }
                    )
                    for unit in units:
                        numerator, denominator = rates[unit]
                        restrictions = tuple(reasons)
                        output.append(
                            PrevalenceRow(
                                population_hash=policy.population_hash,
                                period_end=period,
                                window_start=None if period else periods[0],
                                window_end=None if period else periods[-1],
                                doc_type=doc_type,
                                speaker_role=role,
                                view_kind=kind,
                                view_id=view_id,
                                codebook_id=book.codebook_id,
                                codebook_version=book.codebook_version,
                                codebook_hash=book.content_hash,
                                analysis_policy_hash=policy.content_hash,
                                family_map_hash=families.content_hash
                                if kind == "family"
                                else None,
                                unit=unit,
                                numerator=numerator,
                                denominator=denominator,
                                rate=numerator / denominator if denominator else None,
                                reason=None if denominator else "empty_denominator",
                                **_counts(group),
                                restrictions=tuple(dict.fromkeys(restrictions)),
                                policy_scope=policy.scope,
                            )
                        )
        return pl.DataFrame(
            [r.model_dump(mode="python") for r in output],
            schema=TABLE_SCHEMAS["prevalence"],
        )
    except AnalysisError:
        raise
    except Exception:  # noqa: BLE001 - protect arbitrary source/model diagnostics
        raise AnalysisError("input_changed") from None


def build_analysis(
    inputs: AnalysisInputs, policy: AnalysisPolicy, families: ThemeFamilyMap | None
) -> AnalysisRun:
    """Repeat current consuming gates and fill fourteen typed, content-bound frames."""
    try:
        bound = reverify_analysis_inputs(inputs)
        if policy != bound.inputs.analysis_policy:
            raise AnalysisError("policy_mismatch")
        tables = build_observations(bound)
        completions = document_completions(bound)
        coverage = build_coverage(bound, completions)
        frames = dict(tables.frames)
        frames["completions"] = pl.DataFrame(
            [c.model_dump(mode="python") for c in completions],
            schema=TABLE_SCHEMAS["completions"],
        )
        frames["coverage"] = coverage
        tables = AnalysisTables(frames)
        frames["prevalence"] = prevalence(
            tables, coverage, bound.inputs.sources.codebook, policy, families
        )
        tables = validate_analysis_tables(AnalysisTables(frames))
        source = bound.inputs.sources.stored_run.record
        coding, support = bound.inputs.coding.record, bound.inputs.support.record
        metadata = bound.metadata
        expected = bound.expected
        event_hashes = {e.event_manifest_hash for e in expected}
        pilot_hashes = {e.pilot_hash for e in expected}
        if len(event_hashes) > 1 or len(pilot_hashes) > 1:
            raise AnalysisError("input_changed")
        states = Counter(
            row["latest_state"]
            for row in coverage.filter(pl.col("doc_type") == "release").iter_rows(
                named=True
            )
        )
        reasons = Counter(
            reason
            for row in coverage.filter(pl.col("doc_type") == "release").iter_rows(
                named=True
            )
            for reason in row["missing_reasons"]
        )
        software = dict(coding.software)
        lock_hash = software.get("lock_hash")
        if lock_hash is None:
            raise AnalysisError("input_changed")
        prompts = {
            "extraction": source.configuration.prompt_sha256,
            "coding": coding.coding_policy.prompt_hash,
        }
        # Schema 1 publishes support prompt hashes only on actual judge attempts.
        # Empty targets honestly retain no invented support prompt reference.
        prompts.update(
            ("support-" + h, h)
            for h in {a.prompt_hash for a in bound.inputs.support.attempts}
        )
        if reverify_analysis_inputs(inputs).binding_hash != bound.binding_hash:
            raise AnalysisError("input_changed")
        record = AnalysisRunRecord(
            run_id="analysis-"
            + digest(
                {
                    "binding_hash": bound.binding_hash,
                    "family_map": families.model_dump(mode="json")
                    if families
                    else None,
                }
            ),
            created_at=coding.started_at,
            scope=policy.scope,
            audience="local",
            population_hash=policy.population_hash,
            event_manifest_hash=next(iter(event_hashes), digest([])),
            pilot_hash=next(iter(pilot_hashes), policy.population_hash),
            universe_hash=bound.inputs.selected_universe_hash,
            documents=tuple(sorted((m.doc_id, m.canonical_hash) for m in metadata)),
            canonical_manifests=tuple(
                sorted((m.doc_id, m.canonical_manifest_hash) for m in metadata)
            ),
            mask_manifests=tuple(
                sorted((m.doc_id, m.mask_manifest_hash) for m in metadata)
            ),
            source_run_hash=coding.source_run_hash,
            coding_run_hash=_run_hash(bound.inputs.coding),
            support_run_hash=bound.decisions.support_run_hash,
            configuration_hashes=tuple(
                sorted(
                    (
                        ("extraction", source.configuration_hash),
                        ("coding", coding.configuration_hash),
                        ("support", support.configuration_hash),
                    )
                )
            ),
            prompt_hashes=tuple(sorted(prompts.items())),
            identity_hashes=tuple(
                sorted(
                    (
                        (
                            "extraction",
                            digest(
                                source.configuration.identity.model_dump(mode="json")
                            ),
                        ),
                        (
                            "classifier",
                            digest(coding.classifier_identity.model_dump(mode="json")),
                        ),
                        (
                            "scorer",
                            digest(support.scorer_identity.model_dump(mode="json")),
                        ),
                        *[
                            (
                                "judge-" + str(i),
                                digest(identity.model_dump(mode="json")),
                            )
                            for i, identity in enumerate(support.judge_identities)
                        ],
                    )
                )
            ),
            codebook=coding.codebook,
            assignment_policy=coding.policy,
            analysis_policy=policy,
            family_map=families,
            completion_hashes=tuple(
                sorted(
                    (c.doc_id, digest(c.model_dump(mode="json"))) for c in completions
                )
            ),
            copy_hashes=tuple(
                sorted(
                    (r["doc_id"], digest(r))
                    for r in tables.frames["copies"].iter_rows(named=True)
                )
            ),
            validator_version=source.configuration.validator_version,
            software=tuple(sorted(software.items())),
            lock_hash=lock_hash,
            counts_by_state=tuple(sorted(states.items())),
            counts_by_decision=coding.counts_by_decision,
            counts_by_reason=tuple(sorted(reasons.items())),
            raw_verification=bound.inputs.raw_verification,
            table_hashes=tuple(
                sorted(
                    (name, digest(frame.to_dicts()))
                    for name, frame in tables.frames.items()
                )
            ),
            evidence_hashes=(),
            binding_hash=bound.binding_hash,
        )
        return AnalysisRun(record, tables)
    except AnalysisError:
        raise
    except Exception:  # noqa: BLE001 - no source-bearing errors escape
        raise AnalysisError("input_changed") from None
