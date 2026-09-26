"""What the controlled browser displayed for one saved source (Stage 3, plan B).

``RenderedCapture`` is browser-specific ingestion provenance, never a core contract
(B2): it establishes what the browser displayed under a recorded policy, not quote
exactness or a canonical span. docs/data-dictionary.md documents every field.
"""

import json
from enum import StrEnum
from typing import Self

from earnings_core import ArtifactRef
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex, sha256_hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.canonical.records import IngestionRecord


class CaptureStatus(StrEnum):
    """The browser spec's four capture outcomes."""

    COMPLETED = "completed"
    """Every resource the rendering needs was present."""
    PARTIAL = "partial"
    """Rendered, but a blocked or missing stylesheet, font, or frame may change it."""
    FAILED = "failed"
    """The browser ran, and no usable rendering came back."""
    UNAVAILABLE = "unavailable"
    """No pinned browser could run here."""


class CaptureReason(StrEnum):
    """Why a capture is not ``completed``."""

    BROWSER_UNAVAILABLE = "browser_unavailable"
    """The pinned browser or driver is not installed, or none is pinned here."""
    STARTUP_FAILURE = "startup_failure"
    """The browser or driver did not start, or is not the pinned version."""
    TIMEOUT = "timeout"
    """Navigation or capture ran past its bound."""
    BLOCKED_REQUIRED_RESOURCE = "blocked_required_resource"
    """A stylesheet, font, or frame the page asked for was blocked or missing."""
    DOCUMENT_LOAD_FAILURE = "document_load_failure"
    """The saved file did not load, or the page left it."""
    CAPTURE_FAILURE = "capture_failure"
    """Reading text, layout, or a screenshot failed, or request interception stopped."""


class _Part(BaseModel):
    """A nested part of a capture: immutable, closed, and strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class BlockedRequest(_Part):
    """One request the page made and the capture refused (B7: recorded and blocked)."""

    url: str
    resource_type: str
    """CDP's resource type, such as ``Image``, ``Stylesheet``, or ``Document``."""
    required: bool
    """A stylesheet, font, or subframe document: its absence makes the capture partial."""


class LayoutRun(_Part):
    """One text node's raw DOM text and computed style, or a ``<br>``."""

    text: str
    br: bool
    visible: bool
    bold: bool
    underline: bool
    superscript: bool
    symbol_font: bool
    font_size: NonNegativeFloat


class LayoutBlock(_Part):
    """The runs one block element holds directly, split where a nested block starts.

    ``heading_level`` and ``list_item`` come from the nearest heading or list item
    around it; ``table``, ``row``, and ``cell`` locate its nearest table cell.
    """

    tag: str
    display: str
    heading_level: PositiveInt | None
    list_item: bool
    list_depth: NonNegativeInt
    table: NonNegativeInt | None
    row: NonNegativeInt | None
    cell: NonNegativeInt | None
    x: int
    y: int
    width: NonNegativeInt
    height: NonNegativeInt
    runs: tuple[LayoutRun, ...]


class LayoutCell(_Part):
    """A rendered cell: whether it is a ``th``, and its spans."""

    header: bool
    colspan: PositiveInt
    rowspan: PositiveInt


class LayoutRow(_Part):
    """A rendered row of a table's own: whether it sits in ``thead``, and its cells."""

    head: bool
    cells: tuple[LayoutCell, ...]


class LayoutTable(_Part):
    """A rendered table's own rows in document order, and the cell holding the table.

    ``parent_table``, ``parent_row`` and ``parent_cell`` locate the nearest cell of
    another table that holds this one; all three are ``None`` for a table in no cell.
    """

    parent_table: NonNegativeInt | None
    parent_row: NonNegativeInt | None
    parent_cell: NonNegativeInt | None
    rows: tuple[LayoutRow, ...]


class LayoutMetadata(_Part):
    """Every block and table of the rendered body, in document order."""

    blocks: tuple[LayoutBlock, ...]
    tables: tuple[LayoutTable, ...]


class RenderedCapture(IngestionRecord):
    """One capture of one saved source under one capture policy (B1, B2, B7).

    ``cache_key`` covers the raw hash, the policy, the browser, driver, and Selenium,
    the platform and render configuration, and the metadata script's version and
    text; never a timestamp. A failed or unavailable capture holds no text, layout, or screenshot:
    a failure is never an empty successful capture.
    """

    capture_id: str
    cache_key: Sha256Hex
    source_document_id: IdPart
    raw_sha256: Sha256Hex
    capture_policy: IdPart
    capture_policy_version: IdPart
    metadata_version: IdPart
    browser_engine: str
    browser_version: str
    driver_version: str
    selenium_version: str
    os_name: str
    os_version: str
    architecture: str
    viewport_width: PositiveInt
    viewport_height: PositiveInt
    device_scale_factor: PositiveInt
    locale: str
    timezone: str
    font_set: str
    document_charset: str
    script_policy: str
    network_policy: str
    image_policy: str
    missing_resource_policy: str
    rendered_text: str
    rendered_text_sha256: Sha256Hex
    layout: LayoutMetadata
    layout_sha256: Sha256Hex
    screenshots: tuple[ArtifactRef, ...]
    blocked_requests: tuple[BlockedRequest, ...]
    captured_at: AwareDatetime
    duration_seconds: NonNegativeFloat
    status: CaptureStatus
    reason: CaptureReason | None
    detail: str

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.rendered_text_sha256 != sha256_hex(self.rendered_text.encode("utf-8")):
            raise ValueError("rendered_text_sha256 is not the rendered text's hash")
        if self.layout_sha256 != layout_hash(self.layout):
            raise ValueError("layout_sha256 is not the layout's hash")
        if (self.reason is None) != (self.status is CaptureStatus.COMPLETED):
            raise ValueError("a reason is recorded exactly when not completed")
        if self.status is CaptureStatus.PARTIAL and (
            self.reason is not CaptureReason.BLOCKED_REQUIRED_RESOURCE
        ):
            raise ValueError("a partial capture's reason is blocked_required_resource")
        if self.status in (CaptureStatus.FAILED, CaptureStatus.UNAVAILABLE) and (
            self.rendered_text or self.layout.blocks or self.screenshots
        ):
            raise ValueError("a failed or unavailable capture holds no rendering")
        return self


def layout_hash(layout: LayoutMetadata) -> str:
    """SHA-256 of the layout as ASCII JSON with sorted keys and no spaces."""
    payload = json.dumps(
        layout.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256_hex(payload.encode("ascii"))
