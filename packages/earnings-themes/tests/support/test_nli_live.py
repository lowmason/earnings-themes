"""Explicit local V4 nodes; no weight acquisition or discovery."""

import os
import socket
from pathlib import Path

import pytest
from earnings_themes.support.records import parse_support
from earnings_themes.support.scorers import _request


def _local_smoke(variable, kind, monkeypatch):
    path = os.environ.get(variable)
    if not path:
        pytest.skip("external local model configuration absent; V4 remains pending")
    assert os.environ.get("HF_HUB_OFFLINE") == "1"
    assert os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    # An unpatched syscall must fail under the process-level runner before patches.
    probe = socket.socket()
    try:
        with pytest.raises(PermissionError):
            probe.connect(("127.0.0.1", 9))
    finally:
        probe.close()
    attempts = []

    def blocked(*args, **kwargs):
        attempts.append(1)
        raise AssertionError("network_attempt")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    from earnings_themes.support.nli import (
        DebertaScorer,
        LocalScorerConfig,
        MiniCheckScorer,
    )

    try:
        import json

        config = parse_support(json.loads(Path(path).read_bytes()), LocalScorerConfig)
    except Exception:  # noqa: BLE001 - never print external configuration
        pytest.fail("invalid_local_configuration", pytrace=False)
    assert config.kind == kind
    scorer = (MiniCheckScorer if kind == "minicheck" else DebertaScorer)(config)
    request = _request(
        "The imaginary workshop sells blue gadgets.", "The gadgets are blue."
    )
    tokens = scorer.count_tokens(request)
    reply = scorer.score(request)
    assert reply.score is not None and 0 <= reply.score <= 1
    assert reply.input_tokens == tokens and tokens <= scorer.identity.input_limit
    assert reply.identity == scorer.identity and reply.input_hash == request.input_hash
    from earnings_themes.support.records import SupportRunRecord

    from .test_records import payloads

    payload = payloads()["SupportRunRecord"]
    payload["scorer_identity"] = scorer.identity.model_dump(mode="json")
    manifest = parse_support(payload, SupportRunRecord)
    assert manifest.scorer_identity == scorer.identity
    assert attempts == []


@pytest.mark.live
def test_minicheck_local_primary(monkeypatch):
    _local_smoke("EARNINGS_SUPPORT_PRIMARY_CONFIG", "minicheck", monkeypatch)


@pytest.mark.live
def test_deberta_local_alternative(monkeypatch):
    _local_smoke("EARNINGS_SUPPORT_ALTERNATIVE_CONFIG", "deberta", monkeypatch)
