import earnings_core

PUBLIC = {
    "LEVELED_TYPES",
    "SCHEMA_VERSION",
    "VALIDATOR_VERSION",
    "ArtifactRef",
    "CanonicalDocument",
    "DocumentElement",
    "ElementType",
    "MaskCategory",
    "MaskedDocument",
    "OverlayMask",
    "Rejection",
    "RejectionReason",
    "RightsStatus",
    "SpanCandidate",
    "SpanLocator",
    "TableCellContext",
    "TextChunk",
    "TextOrigin",
    "TextSpan",
    "VerifiedSpan",
    "apply_masks",
    "derive_doc_id",
    "derive_element_id",
    "document_integrity_problem",
    "hash_canonical_text",
    "make_locator",
    "occurrences",
    "parse_span_candidate",
    "resolve_locator",
    "resolve_pointer",
    "sha256_hex",
    "validate_elements",
    "validate_span",
}


def test_the_package_root_exports_exactly_the_public_api() -> None:
    assert set(earnings_core.__all__) == PUBLIC
    for name in PUBLIC:
        assert getattr(earnings_core, name) is not None


def test_the_scaffold_placeholder_is_gone() -> None:
    assert not hasattr(earnings_core, "hello")


def test_versions_are_pinned() -> None:
    assert earnings_core.SCHEMA_VERSION == 2
    assert earnings_core.VALIDATOR_VERSION == "2"
