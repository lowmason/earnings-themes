"""layout-1, the layout extractor, and its mapping onto walker-1's text (Stage 3, plan B)."""

from earnings_ingestion.layout.align import MAPPING_POLICY
from earnings_ingestion.layout.blocks import LAYOUT_VERSION
from earnings_ingestion.layout.extract import LayoutExtractor
from earnings_ingestion.layout.records import AlignmentFailure, LayoutExtraction

__all__ = [
    "LAYOUT_VERSION",
    "MAPPING_POLICY",
    "AlignmentFailure",
    "LayoutExtraction",
    "LayoutExtractor",
]
