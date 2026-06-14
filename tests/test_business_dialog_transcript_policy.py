"""Tests for disabled-by-default business-dialog transcript-use policy."""

from __future__ import annotations

import json

from ai_secretary.telephony.transcript_policy import (
    TranscriptCandidate,
    TranscriptUsePolicy,
    evaluate_business_dialog_transcript_use,
    transcript_use_policy_from_env,
)


def test_default_disabled_keeps_existing_behavior() -> None:
    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text="__FAKE_TRANSCRIPT_PLACEHOLDER__", age_ms=0),
    )

    assert decision.enabled is False
    assert decision.allowed is False
    assert decision.reason == "business_dialog_transcript_disabled"
    assert decision.used_for_dialog is False
    assert decision.to_safe_details()["business_dialog_transcript_used_for_dialog"] is False


def test_explicit_disabled_blocks_transcript_use() -> None:
    policy = transcript_use_policy_from_env({"BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED": "false"})

    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text="__FAKE_TRANSCRIPT_PLACEHOLDER__", age_ms=0),
        policy=policy,
    )

    assert decision.allowed is False
    assert decision.reason == "business_dialog_transcript_disabled"


def test_missing_transcript_fails_closed() -> None:
    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text="", age_ms=0),
        policy=TranscriptUsePolicy(enabled=True),
    )

    assert decision.allowed is False
    assert decision.reason == "missing_transcript"
    assert decision.length_bucket == "zero"


def test_stale_transcript_fails_closed() -> None:
    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text="__FAKE_TRANSCRIPT_PLACEHOLDER__", age_ms=30_001),
        policy=TranscriptUsePolicy(enabled=True, max_age_ms=30_000),
    )

    assert decision.allowed is False
    assert decision.reason == "stale_transcript"
    assert decision.age_bucket == "stale"


def test_low_confidence_transcript_fails_closed() -> None:
    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text="__FAKE_TRANSCRIPT_PLACEHOLDER__", confidence=0.61, age_ms=0),
        policy=TranscriptUsePolicy(enabled=True, min_confidence=0.7),
    )

    assert decision.allowed is False
    assert decision.reason == "low_confidence_transcript"
    assert decision.confidence_bucket == "low"


def test_incomplete_metadata_fails_closed() -> None:
    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text="__FAKE_TRANSCRIPT_PLACEHOLDER__", age_ms=None),
        policy=TranscriptUsePolicy(enabled=True, max_age_ms=30_000),
    )

    assert decision.allowed is False
    assert decision.reason == "incomplete_transcript_metadata"


def test_redaction_guard_inactive_fails_closed() -> None:
    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text="__FAKE_TRANSCRIPT_PLACEHOLDER__", age_ms=0, redaction_active=False),
        policy=TranscriptUsePolicy(enabled=True),
    )

    assert decision.allowed is False
    assert decision.reason == "redaction_guard_inactive"


def test_enabled_valid_transcript_allows_policy_result_without_logging_raw_text() -> None:
    transcript = "__FAKE_TRANSCRIPT_PLACEHOLDER__"
    decision = evaluate_business_dialog_transcript_use(
        TranscriptCandidate(text=transcript, confidence=0.92, age_ms=0),
        policy=TranscriptUsePolicy(enabled=True, min_confidence=0.7, max_age_ms=30_000),
    )

    serialized = json.dumps(decision.to_safe_details(), ensure_ascii=False)
    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert decision.length_bucket == "nonzero_redacted"
    assert decision.confidence_bucket == "high"
    assert decision.age_bucket == "fresh"
    assert transcript not in serialized
