"""Build the cohort from the curated files, the registers, and saved artifacts.

``build`` fetches nothing (A §410): every fact it uses is in a committed file or an
artifact saved under ``data/raw/cohort/``. It stops with ``CohortError`` on what no
review can settle: an unregistered source, a missing artifact, or a citation that no
longer cites what it hashed. Everything a reviewer can decide becomes a finding.

1. Verify every citation in ``evidence.toml`` and every stored override citation.
2. Turn the anchor's rows and the changes into statements and reconstruct intervals.
3. Resolve every security to an issuer from SEC's saved records.
4. Compare each snapshot, fund filing, and check list with the reconstruction.
5. Collect the findings, apply acknowledgements, and assemble the report.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from earnings_ingestion.cohort.config import (
    UNIVERSE_DIR,
    ChangeEvidence,
    CohortConfig,
    Row,
    SnapshotEvidence,
    load_cohort_config,
)
from earnings_ingestion.cohort.corroboration import (
    FundFiling,
    current_filings,
    difference_findings,
    gap_findings,
    match_holdings,
    reconcile,
)
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.findings import acknowledge, make_finding
from earnings_ingestion.cohort.intervals import Statement, count_findings, reconstruct
from earnings_ingestion.cohort.locators import (
    ArtifactText,
    CitableArtifact,
    LocatorError,
)
from earnings_ingestion.cohort.records import (
    AssertedAction,
    BoundTiming,
    CitedIdentity,
    CohortReport,
    EvidenceClass,
    EvidenceLocator,
    Finding,
    FindingKind,
    Issuer,
    IssuerMapping,
    LocatorKind,
    MembershipAssertion,
    MembershipInterval,
    Override,
    OverrideKind,
    SecurityRecord,
    SnapshotReconciliation,
    SourceRights,
    SourceRole,
    UniverseDefinition,
    UniverseManifest,
)
from earnings_ingestion.cohort.register import (
    MEMBERSHIP_REGISTER,
    SEC_REGISTER,
    SEC_SOURCE_ID,
    RegisterEntry,
    Registers,
    load_registers,
)
from earnings_ingestion.cohort.resolution import SecEvidence, resolve
from earnings_ingestion.fetch.store import ArtifactStore, StoredArtifact
from earnings_ingestion.sec.data import (
    SecDataError,
    raw_document_name,
    read_company_tickers,
    read_nport_holdings,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_page_url,
    submissions_url,
)

COHORT_STORE = Path("data") / "raw" / "cohort"
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
LIMITATIONS = (
    (
        "Fund holdings are an ETF proxy: they corroborate the reconstruction and"
        " never add or remove a member."
    ),
    (
        "SEC identity records were retrieved after the cutoff: they establish issuer"
        " identity, never membership."
    ),
    (
        "Intervals are resolved to the day; ordering a change and a release on one"
        " day is Stage 5's eligibility decision."
    ),
)


class CohortError(ValueError):
    """Problems no review can settle; the build stops and lists every one."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class _Item:
    """A verified snapshot or change, with its artifact and row locators."""

    config: SnapshotEvidence | ChangeEvidence
    entry: RegisterEntry
    stored: StoredArtifact
    rows: dict[tuple[str, str], EvidenceLocator]
    date_locator: EvidenceLocator | None

    @property
    def retrieved_at(self) -> datetime:
        return self.stored.retrievals[0].retrieved_at

    def citation(self) -> CitableArtifact:
        return CitableArtifact(
            source_id=self.config.source_id,
            url=self.config.url,
            artifact=self.stored.ref,
            retrieved_at=self.retrieved_at,
            text=ArtifactText(self.stored.body, self.stored.ref.media_type),
        )


def _is_anchor(item: _Item) -> bool:
    return isinstance(item.config, SnapshotEvidence) and item.config.role == "anchor"


def _members(item: SnapshotEvidence | ChangeEvidence) -> tuple[Row, ...]:
    return item.members if isinstance(item, SnapshotEvidence) else item.entries


def _action(row: Row) -> str:
    return getattr(row, "action", AssertedAction.MEMBER_AT.value)


def content_hash(manifest: UniverseManifest) -> str:
    """SHA-256 of a manifest's canonical JSON without its version, hash, and time."""
    data = manifest.model_dump(mode="json")
    for key in ("universe_version", "content_hash", "created_at"):
        del data["definition"][key]
    return digest(data)


@dataclass(frozen=True)
class CohortBuild:
    """Everything a manifest holds except its version, content hash, and time."""

    config: CohortConfig
    source_register_version: str
    sources: tuple[SourceRights, ...]
    securities: tuple[SecurityRecord, ...]
    assertions: tuple[MembershipAssertion, ...]
    intervals: tuple[MembershipInterval, ...]
    mappings: tuple[IssuerMapping, ...]
    issuers: tuple[Issuer, ...]
    candidate_issuer_ids: tuple[str, ...]
    overrides: tuple[Override, ...]
    report: CohortReport
    stale_acknowledgements: tuple[str, ...] = field(default=())

    def manifest(self, version: int, created_at: datetime) -> UniverseManifest:
        universe = self.config.universe
        draft = UniverseManifest(
            definition=UniverseDefinition(
                universe_id=universe.universe_id,
                universe_version=version,
                universe_name=universe.universe_name,
                period_end_start=universe.period_end_start,
                period_end_stop=universe.period_end_stop,
                public_information_cutoff=universe.public_information_cutoff,
                membership_reference=universe.membership_reference,
                expected_member_count=universe.expected_member_count,
                source_register_version=self.source_register_version,
                selection_policy_version=universe.selection_policy_version,
                content_hash="0" * 64,
                created_at=created_at,
            ),
            sources=self.sources,
            securities=self.securities,
            assertions=self.assertions,
            intervals=self.intervals,
            mappings=self.mappings,
            issuers=self.issuers,
            candidate_issuer_ids=self.candidate_issuer_ids,
            overrides=self.overrides,
            report=self.report,
        )
        definition = draft.definition.model_copy(
            update={"content_hash": content_hash(draft)}
        )
        return draft.model_copy(update={"definition": definition})

    @property
    def content_hash(self) -> str:
        return self.manifest(1, EPOCH).definition.content_hash


def build(
    repo: Path,
    *,
    config_dir: Path = UNIVERSE_DIR,
    store_root: Path = COHORT_STORE,
    register: Path = MEMBERSHIP_REGISTER,
    sec_register: Path = SEC_REGISTER,
) -> CohortBuild:
    """The cohort that ``repo``'s committed files and saved artifacts support."""
    config = load_cohort_config(repo / config_dir)
    registers = load_registers(repo, register, sec_register)
    return _Builder(config, registers, ArtifactStore(repo / store_root, repo)).run()


class _Builder:
    def __init__(
        self, config: CohortConfig, registers: Registers, store: ArtifactStore
    ):
        self.config = config
        self.universe = config.universe
        self.cutoff = config.universe.public_information_cutoff
        self.registers = registers
        self.store = store
        self.problems: list[str] = []
        self.used = {SEC_SOURCE_ID}
        self.overrides = config.overrides.overrides

    # -- step 1: citations ---------------------------------------------------

    def _entry(self, source_id: str, role: SourceRole) -> RegisterEntry | None:
        try:
            entry = self.registers.entry(source_id)
        except ValueError as exc:
            self.problems.append(str(exc))
            return None
        if role not in entry.roles:
            self.problems.append(f"source {source_id!r} is not registered for {role}")
            return None
        self.used.add(source_id)
        return entry

    def _stored(self, source_id: str, sha256: str) -> StoredArtifact | None:
        try:
            rights = self.registers.rights(source_id)
            stored = self.store.get(
                source_id,
                sha256,
                rights_status=rights.rights_status,
                rights_basis=rights.rights_basis,
            )
        except (FileNotFoundError, ValueError) as exc:
            self.problems.append(str(exc))
            return None
        self.used.add(source_id)
        return stored

    def _latest(self, source_id: str, url: str) -> StoredArtifact | None:
        try:
            rights = self.registers.rights(source_id)
            stored = self.store.latest(
                source_id,
                url,
                rights_status=rights.rights_status,
                rights_basis=rights.rights_basis,
            )
        except (FileNotFoundError, ValueError) as exc:
            self.problems.append(str(exc))
            return None
        if stored is None:
            self.problems.append(f"nothing saved from {url} for {source_id}")
            return None
        self.used.add(source_id)
        return stored

    def _item(self, item: SnapshotEvidence | ChangeEvidence) -> _Item | None:
        if isinstance(item, ChangeEvidence):
            role = SourceRole.CHANGE
        else:
            role = SourceRole(item.role)
        entry = self._entry(item.source_id, role)
        stored = (
            None
            if entry is None
            else self._stored(item.source_id, item.artifact_sha256)
        )
        if entry is None or stored is None:
            return None
        where = item.evidence_id
        if (
            role is SourceRole.CHANGE
            and entry.evidence_class is not EvidenceClass.OFFICIAL
        ):
            self.problems.append(f"{where}: a change must be official evidence")
        if item.url not in {r.request_url for r in stored.retrievals}:
            self.problems.append(
                f"{where}: {item.url} is not where its artifact came from"
            )
        text = ArtifactText(stored.body, stored.ref.media_type)

        def span(start: int, end: int, cited: str) -> EvidenceLocator:
            return EvidenceLocator(
                kind=LocatorKind.TEXT_SPAN,
                canonicalization_version=text.version,
                canonical_sha256=item.canonical_sha256,
                start=start,
                end=end,
                cited_sha256=cited,
            )

        rows: dict[tuple[str, str], EvidenceLocator] = {}
        date_locator = None
        try:
            for row in _members(item):
                locator = span(*row.span, row.cited_sha256)
                cited = text.cited(locator)
                for fact in (row.name, row.ticker):
                    if fact not in cited:
                        self.problems.append(
                            f"{where}: the text cited for {row.security_id}"
                            f" does not state {fact!r}"
                        )
                rows[(row.security_id, _action(row))] = locator
            if isinstance(item, ChangeEvidence):
                date_locator = span(*item.date_span, item.date_cited_sha256)
                text.verify(date_locator)
        except LocatorError as exc:
            self.problems.append(f"{where}: {exc}")
            return None
        return _Item(item, entry, stored, rows, date_locator)

    def _override_citations(self) -> None:
        for override in self.overrides:
            for citation in override.citations:
                if citation.artifact_sha256 is None:
                    continue
                stored = self._stored(citation.source_id, citation.artifact_sha256)
                if stored is None or citation.locator is None:
                    continue
                try:
                    ArtifactText(stored.body, stored.ref.media_type).verify(
                        citation.locator
                    )
                except LocatorError as exc:
                    self.problems.append(f"{override.override_id}: {exc}")

    # -- step 2: membership ----------------------------------------------------

    def _anchor(self, items: list[_Item]) -> tuple[_Item | None, Finding | None]:
        anchors = [i for i in items if _is_anchor(i)]
        if not anchors:
            return None, self._missing_anchor("no anchor snapshot is curated", [])
        (anchor,) = anchors
        snapshot = anchor.config
        reasons = []
        if anchor.entry.evidence_class not in (
            EvidenceClass.OFFICIAL,
            EvidenceClass.SECONDARY,
        ):
            reasons.append(f"{anchor.entry.evidence_class} evidence is not a roster")
        if snapshot.published_on > snapshot.as_of:
            reasons.append(
                f"published {snapshot.published_on}, after its as-of date"
                f" {snapshot.as_of}: a later snapshot is never backdated"
            )
        if snapshot.as_of > self.universe.period_end_start:
            reasons.append(f"dated after the window's start, {snapshot.as_of}")
        if snapshot.published_on > self.cutoff:
            reasons.append("first published after the cutoff")
        if reasons:
            detail = f"{snapshot.evidence_id} cannot anchor: {'; '.join(reasons)}"
            return None, self._missing_anchor(detail, [snapshot.evidence_id])
        return anchor, None

    @staticmethod
    def _missing_anchor(detail: str, evidence_ids: list[str]) -> Finding:
        return make_finding(
            FindingKind.MISSING_ANCHOR,
            "anchor",
            detail,
            blocking=True,
            evidence_ids=evidence_ids,
        )

    @staticmethod
    def _statements(anchor: _Item | None, changes: list[_Item]) -> list[Statement]:
        statements = []
        for item in ([anchor] if anchor else []) + changes:
            config = item.config
            is_change = isinstance(config, ChangeEvidence)
            for row in _members(config):
                action = AssertedAction(_action(row))
                statements.append(
                    Statement(
                        assertion_id=f"{config.evidence_id}:{row.security_id}:{action}",
                        security_id=row.security_id,
                        action=action,
                        on=config.effective_on if is_change else config.as_of,
                        timing=config.timing if is_change else BoundTiming.UNSPECIFIED,
                        evidence_id=config.evidence_id,
                        published_on=config.published_on,
                    )
                )
        return statements

    # -- step 3: identity ------------------------------------------------------

    def _sec(self, securities: tuple[SecurityRecord, ...]) -> SecEvidence | None:
        tickers = self._latest(SEC_SOURCE_ID, COMPANY_TICKERS_URL)
        if tickers is None:
            return None
        try:
            entries = read_company_tickers(tickers.body)
        except (SecDataError, ValueError) as exc:
            self.problems.append(f"company_tickers.json: {exc}")
            return None
        cited = {i.ticker for s in securities for i in s.identities}
        ciks = {e.cik for e in entries if e.ticker in cited}
        ciks |= {o.cik for o in self.overrides if o.kind is OverrideKind.SET_ISSUER}
        registrants = {}
        for cik in sorted(ciks):
            url = submissions_url(cik)
            stored = self._latest(SEC_SOURCE_ID, url)
            if stored is None:
                continue
            try:
                registrant = read_submissions(stored.body)
            except (SecDataError, ValueError) as exc:
                self.problems.append(f"{url}: {exc}")
                continue
            registrants[cik] = (registrant, self._citable(SEC_SOURCE_ID, url, stored))
        return SecEvidence(
            tickers=self._citable(SEC_SOURCE_ID, COMPANY_TICKERS_URL, tickers),
            ticker_entries=entries,
            registrants=registrants,
        )

    @staticmethod
    def _citable(source_id: str, url: str, stored: StoredArtifact) -> CitableArtifact:
        return CitableArtifact(
            source_id=source_id,
            url=url,
            artifact=stored.ref,
            retrieved_at=stored.retrievals[0].retrieved_at,
            text=ArtifactText(stored.body, stored.ref.media_type),
        )

    # -- step 4: corroboration ------------------------------------------------

    def _fund_filings(self) -> list[FundFiling]:
        proxy = self.universe.etf_proxy
        if proxy is None:
            return []
        self._entry(proxy.source_id, SourceRole.CORROBORATION)
        url = submissions_url(proxy.cik)
        stored = self._latest(SEC_SOURCE_ID, url)
        if stored is None:
            return []
        try:
            registrant = read_submissions(stored.body)
            filings = list(registrant.filings)
            for page in registrant.older_pages:
                older = self._latest(SEC_SOURCE_ID, submissions_page_url(page.name))
                if older is not None:
                    filings.extend(read_submissions_page(older.body))
        except (SecDataError, ValueError) as exc:
            self.problems.append(f"{url}: {exc}")
            return []
        funds = []
        for filing in filings:
            if filing.form not in proxy.forms or filing.report_date is None:
                continue
            if not (
                self.universe.period_end_start <= filing.report_date <= self.cutoff
            ):
                continue
            document = archive_url(
                proxy.cik, filing.accession, raw_document_name(filing.primary_document)
            )
            saved = self._latest(proxy.source_id, document)
            if saved is None:
                continue
            try:
                report = read_nport_holdings(saved.body)
            except SecDataError as exc:
                self.problems.append(f"{document}: {exc}")
                continue
            if report.report_date != filing.report_date:
                self.problems.append(
                    f"{document}: reports {report.report_date}, but EDGAR lists"
                    f" {filing.report_date}"
                )
                continue
            funds.append(
                FundFiling(
                    filing, report, self._citable(proxy.source_id, document, saved)
                )
            )
        return funds

    # -- the whole ------------------------------------------------------------

    def run(self) -> CohortBuild:
        evidence = self.config.evidence
        items = [self._item(item) for item in (*evidence.snapshots, *evidence.changes)]
        for check in evidence.checks:
            self._entry(check.source_id, SourceRole.CHECK)
        self._override_citations()
        if self.problems:
            raise CohortError(self.problems)
        items = [item for item in items if item is not None]

        anchor, missing = self._anchor(items)
        changes = [i for i in items if isinstance(i.config, ChangeEvidence)]
        statements = self._statements(anchor, changes)
        rejections = {
            o.membership_assertion_id: o.override_id
            for o in self.overrides
            if o.kind is OverrideKind.REJECT_ASSERTION
        }
        membership = reconstruct(
            statements,
            anchor_date=None if anchor is None else anchor.config.as_of,
            cutoff=self.cutoff,
            rejections=rejections,
        )
        counts = count_findings(
            membership.intervals,
            anchor_date=None if anchor is None else anchor.config.as_of,
            cutoff=self.cutoff,
            expected=self.universe.expected_member_count,
        )

        usable = [i for i in items if not _is_anchor(i) or i is anchor]
        securities = self._securities(usable)
        timely = self._timely(securities, usable)
        known = {s.security_id for s in securities}
        for o in self.overrides:
            if o.kind is OverrideKind.HOLDING_ALIAS and o.security_id not in known:
                self.problems.append(f"{o.override_id}: no security {o.security_id}")
        stop = self.cutoff + timedelta(days=1)
        in_scope = frozenset(
            i.security_id
            for i in membership.intervals
            if i.overlaps(self.universe.period_end_start, stop)
        )
        sec = self._sec(timely)
        funds = self._fund_filings()
        if self.problems or sec is None:
            raise CohortError(self.problems)
        resolution = resolve(timely, sec, self.overrides, in_scope)

        reconciliations, fund_findings = self._reconciliations(
            items, funds, timely, securities, membership.intervals
        )
        findings = [
            *([missing] if missing else []),
            *membership.findings,
            *counts,
            *resolution.findings,
            *fund_findings,
            *difference_findings(reconciliations),
            *gap_findings(
                reconciliations,
                start=self.universe.period_end_start,
                cutoff=self.cutoff,
            ),
            *self._withheld(items, funds),
        ]
        findings, stale = acknowledge(findings, self.overrides)

        mappings = {m.security_id: m for m in resolution.mappings}
        assertions = self._assertions(statements, items, membership, mappings)
        candidates = sorted(
            {
                mappings[s].issuer_id
                for s in in_scope
                if s in mappings and mappings[s].issuer_id is not None
            }
        )
        report = CohortReport(
            universe_id=self.universe.universe_id,
            anchor_evidence_id=None if anchor is None else anchor.config.evidence_id,
            limitations=self._limitations(anchor),
            findings=tuple(sorted(findings, key=lambda f: f.finding_id)),
            reconciliations=tuple(
                sorted(reconciliations, key=lambda r: (r.as_of, r.snapshot_id))
            ),
        )
        return CohortBuild(
            config=self.config,
            source_register_version=self.registers.version(self.used),
            sources=tuple(self.registers.rights(s) for s in sorted(self.used)),
            securities=securities,
            assertions=assertions,
            intervals=tuple(
                sorted(
                    membership.intervals,
                    key=lambda i: (i.security_id, i.effective_from),
                )
            ),
            mappings=resolution.mappings,
            issuers=resolution.issuers,
            candidate_issuer_ids=tuple(candidates),
            overrides=tuple(sorted(self.overrides, key=lambda o: o.override_id)),
            report=report,
            stale_acknowledgements=stale,
        )

    def _securities(self, items: list[_Item]) -> tuple[SecurityRecord, ...]:
        identities: dict[str, list[CitedIdentity]] = defaultdict(list)
        for item in items:
            config = item.config
            observed = (
                config.effective_on
                if isinstance(config, ChangeEvidence)
                else config.as_of
            )
            for row in _members(config):
                identities[row.security_id].append(
                    CitedIdentity(
                        evidence_id=config.evidence_id,
                        observed_on=observed,
                        name=row.name,
                        ticker=row.ticker,
                    )
                )
        return tuple(
            SecurityRecord(
                security_id=security_id,
                identities=tuple(
                    sorted(found, key=lambda i: (i.observed_on, i.evidence_id))
                ),
            )
            for security_id, found in sorted(identities.items())
        )

    def _timely(
        self, securities: tuple[SecurityRecord, ...], items: list[_Item]
    ) -> tuple[SecurityRecord, ...]:
        """The records with only rows published by the cutoff: what identity and
        holdings matching may use (P-C4)."""
        published = {i.config.evidence_id: i.config.published_on for i in items}
        return tuple(
            s.model_copy(
                update={
                    "identities": tuple(
                        i
                        for i in s.identities
                        if published[i.evidence_id] <= self.cutoff
                    )
                }
            )
            for s in securities
        )

    def _reconciliations(self, items, funds, timely, securities, intervals):
        reconciliations: list[SnapshotReconciliation] = []
        for item in items:
            config = item.config
            if (
                not isinstance(config, SnapshotEvidence)
                or config.role != "corroboration"
            ):
                continue
            reconciliations.append(
                reconcile(
                    config.evidence_id,
                    source_id=config.source_id,
                    evidence_class=item.entry.evidence_class,
                    as_of=config.as_of,
                    published_on=config.published_on,
                    cutoff=self.cutoff,
                    listed=[row.security_id for row in config.members],
                    unmatched=(),
                    intervals=intervals,
                    citation=item.citation().cite(*item.rows.values()),
                )
            )
        current, findings = current_filings(funds, self.cutoff)
        proxy = self.universe.etf_proxy
        for fund in current:
            matched, unmatched = match_holdings(fund.report, timely, self.overrides)
            reconciliations.append(
                reconcile(
                    f"{proxy.source_id}:{fund.filing.accession}",
                    source_id=proxy.source_id,
                    evidence_class=EvidenceClass.ETF_PROXY,
                    as_of=fund.report.report_date,
                    published_on=fund.filing.filing_date,
                    cutoff=self.cutoff,
                    listed=matched,
                    unmatched=unmatched,
                    intervals=intervals,
                    citation=fund.artifact.cite(),
                )
            )
        tickers = defaultdict(set)
        for security in securities:
            for identity in security.identities:
                tickers[identity.ticker].add(security.security_id)
        for check in self.config.evidence.checks:
            listed = set().union(*(tickers.get(m.ticker, set()) for m in check.members))
            reconciliations.append(
                reconcile(
                    check.evidence_id,
                    source_id=check.source_id,
                    evidence_class=self.registers.entry(check.source_id).evidence_class,
                    as_of=check.as_of,
                    published_on=check.published_on,
                    cutoff=self.cutoff,
                    listed=listed,
                    unmatched=[
                        m.ticker for m in check.members if m.ticker not in tickers
                    ],
                    intervals=intervals,
                    citation=None,
                )
            )
        return reconciliations, findings

    def _withheld(self, items: list[_Item], funds: list[FundFiling]) -> list[Finding]:
        late = [
            (i.config.evidence_id, i.config.published_on)
            for i in items
            if i.config.published_on > self.cutoff
        ]
        late += [
            (c.evidence_id, c.published_on)
            for c in self.config.evidence.checks
            if c.published_on > self.cutoff
        ]
        late += [
            (f.filing.accession, f.filing.filing_date)
            for f in funds
            if f.filing.filing_date > self.cutoff
        ]
        return [
            make_finding(
                FindingKind.WITHHELD,
                subject,
                f"{subject} was first published {published}, after the cutoff"
                f" {self.cutoff}; it is reported and never applied",
                blocking=False,
                evidence_ids=[subject],
            )
            for subject, published in sorted(late)
        ]

    def _assertions(self, statements, items, membership, mappings):
        by_id = {i.config.evidence_id: i for i in items}
        assertions = []
        for s in sorted(statements, key=lambda s: s.assertion_id):
            item = by_id[s.evidence_id]
            config = item.config
            is_change = isinstance(config, ChangeEvidence)
            interval = membership.supports.get(s.assertion_id)
            mapping = mappings.get(s.security_id)
            locators = [item.rows[(s.security_id, s.action.value)]]
            if item.date_locator is not None:
                locators.append(item.date_locator)
            assertions.append(
                MembershipAssertion(
                    membership_assertion_id=s.assertion_id,
                    universe_id=self.universe.universe_id,
                    security_id=s.security_id,
                    issuer_id=None if mapping is None else mapping.issuer_id,
                    cik=None if mapping is None else mapping.cik,
                    asserted_action=s.action,
                    asserted_date=s.on,
                    asserted_timing=s.timing,
                    effective_from=None
                    if interval is None
                    else interval.effective_from,
                    effective_from_basis=None
                    if interval is None
                    else interval.effective_from_basis,
                    effective_from_timing=None
                    if interval is None
                    else interval.effective_from_timing,
                    effective_to=None if interval is None else interval.effective_to,
                    effective_to_timing=None
                    if interval is None
                    else interval.effective_to_timing,
                    announcement_date=config.announced_on if is_change else None,
                    source_snapshot_date=None if is_change else config.as_of,
                    publication_date=config.published_on,
                    publication_time=config.published_at,
                    retrieved_at=item.retrieved_at,
                    source_id=config.source_id,
                    evidence_id=config.evidence_id,
                    url=config.url,
                    evidence_locators=tuple(locators),
                    raw_content_hash=config.artifact_sha256,
                    rights_status=item.entry.rights_status,
                    status=membership.statuses[s.assertion_id],
                    resolved_by=membership.rejected_by.get(s.assertion_id),
                )
            )
        return tuple(assertions)

    @staticmethod
    def _limitations(anchor: _Item | None) -> tuple[str, ...]:
        if anchor is None:
            return LIMITATIONS
        first = (
            f"The anchor, {anchor.config.evidence_id}, is {anchor.entry.evidence_class}"
            f" evidence dated {anchor.config.as_of}: that date bounds each anchored"
            " start from below."
        )
        return (first, *LIMITATIONS)
