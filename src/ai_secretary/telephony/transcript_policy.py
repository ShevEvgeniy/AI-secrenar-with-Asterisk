"""Business-dialog transcript-use policy.

This module intentionally returns only safe metadata. It never returns raw
transcript text or transcript deltas in policy details.
"""

from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS = 30_000


@dataclass(frozen=True)
class TranscriptUsePolicy:
    enabled: bool = False
    min_confidence: float | None = None
    max_age_ms: int | None = DEFAULT_BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS
    redact_logs: bool = True
    fail_closed: bool = True


@dataclass(frozen=True)
class TranscriptCandidate:
    text: str | None = None
    confidence: float | None = None
    age_ms: int | None = None
    metadata_complete: bool = True
    redaction_active: bool = True


@dataclass(frozen=True)
class TranscriptUseDecision:
    enabled: bool
    allowed: bool
    reason: str
    length_bucket: str
    confidence_bucket: str
    age_bucket: str
    redaction_required: bool
    used_for_dialog: bool

    def to_safe_details(self) -> dict[str, bool | str]:
        return {
            "business_dialog_transcript_policy_enabled": self.enabled,
            "business_dialog_transcript_allowed": self.allowed,
            "business_dialog_transcript_reason": self.reason,
            "business_dialog_transcript_length_bucket": self.length_bucket,
            "business_dialog_transcript_confidence_bucket": self.confidence_bucket,
            "business_dialog_transcript_age_bucket": self.age_bucket,
            "business_dialog_transcript_redaction_required": self.redaction_required,
            "business_dialog_transcript_used_for_dialog": self.used_for_dialog,
        }


def transcript_use_policy_from_env(environ: dict[str, str] | None = None) -> TranscriptUsePolicy:
    env = environ if environ is not None else os.environ
    return TranscriptUsePolicy(
        enabled=_env_bool(env, "BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED", False),
        min_confidence=_env_optional_float(env, "BUSINESS_DIALOG_TRANSCRIPT_MIN_CONFIDENCE"),
        max_age_ms=_env_optional_int(env, "BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS", DEFAULT_BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS),
        redact_logs=_env_bool(env, "BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS", True),
        fail_closed=_env_bool(env, "BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED", True),
    )


def evaluate_business_dialog_transcript_use(
    candidate: TranscriptCandidate,
    *,
    policy: TranscriptUsePolicy | None = None,
) -> TranscriptUseDecision:
    policy = policy or TranscriptUsePolicy()
    length_bucket = _length_bucket(candidate.text)
    confidence_bucket = _confidence_bucket(candidate.confidence)
    age_bucket = _age_bucket(candidate.age_ms, policy.max_age_ms)

    reason = _reject_reason(candidate, policy)
    allowed = reason is None
    return TranscriptUseDecision(
        enabled=policy.enabled,
        allowed=allowed,
        reason="allowed" if allowed else reason,
        length_bucket=length_bucket,
        confidence_bucket=confidence_bucket,
        age_bucket=age_bucket,
        redaction_required=policy.redact_logs,
        used_for_dialog=allowed,
    )


def _reject_reason(candidate: TranscriptCandidate, policy: TranscriptUsePolicy) -> str | None:
    if not policy.enabled:
        return "business_dialog_transcript_disabled"
    if not policy.redact_logs:
        return "redaction_guard_inactive"
    if not candidate.redaction_active:
        return "redaction_guard_inactive"
    if not candidate.metadata_complete:
        return "incomplete_transcript_metadata"
    if not candidate.text or not candidate.text.strip():
        return "missing_transcript"
    if policy.max_age_ms is not None:
        if candidate.age_ms is None:
            return "incomplete_transcript_metadata"
        if candidate.age_ms > policy.max_age_ms:
            return "stale_transcript"
    if policy.min_confidence is not None:
        if candidate.confidence is None:
            return "incomplete_transcript_metadata"
        if candidate.confidence < policy.min_confidence:
            return "low_confidence_transcript"
    return None


def _length_bucket(text: str | None) -> str:
    if not text or not text.strip():
        return "zero"
    return "nonzero_redacted"


def _confidence_bucket(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= 0.9:
        return "high"
    if confidence >= 0.7:
        return "medium"
    return "low"


def _age_bucket(age_ms: int | None, max_age_ms: int | None) -> str:
    if age_ms is None:
        return "unknown"
    if age_ms < 0:
        return "invalid"
    if max_age_ms is not None and age_ms > max_age_ms:
        return "stale"
    return "fresh"


def _env_bool(env: dict[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_optional_float(env: dict[str, str], name: str) -> float | None:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _env_optional_int(env: dict[str, str], name: str, default: int | None) -> int | None:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default
