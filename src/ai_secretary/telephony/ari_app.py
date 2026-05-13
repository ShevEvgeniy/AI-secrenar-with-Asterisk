"""ARI app listener entry point."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..config.settings import Settings
from ..core.runner import run_pipeline, run_pipeline_from_transcript
from ..rag.embeddings import warmup_embeddings
from ..stt.live_streaming import (
    LiveStreamingProofError,
    LiveStreamingProofHandle,
    LiveStreamingProofResult,
    is_live_external_media_channel,
    live_streaming_config,
    live_streaming_stage_allowed,
    start_live_streaming_proof,
)
from ..stt.realtime_whisper import RealtimeTranscriptionConfig, RealtimeWhisperAdapter
from ..stt.whisper_api import WhisperAPIClient
from ..storage.callbacks import (
    CallbackOutcomeType,
    append_callback_record,
    build_callback_record,
    callback_records_path,
)
from ..storage.files import save_bytes, save_json
from ..tts.silero import SileroTTS
from .ari_client import AriClient
from .call_session import CallSession, CallState, DialogStage
from .dialog import (
    CITY_RETRY_STATIC_PROMPT,
    PROMPTS,
    apply_turn,
    build_turn_record,
    next_prompt,
    required_fields_missing,
    should_stop_dialog,
)
from .publish_to_asterisk import publish_wav_to_asterisk
from .routing import (
    Department,
    DEFAULT_TRANSFER_CONTEXT,
    DEFAULT_TRANSFER_EXTEN,
    DEFAULT_TRANSFER_PRIORITY,
    business_hours_for_department,
    classify_department_intent,
    route_for_department,
)

PROMPT_1_SOUND_ID = "sound:ai_secretary/_system/prompt_1"
PROMPT_CLARIFY_SOUND_ID = "sound:ai_secretary/_system/prompt_intent_clarify"
PROMPT_2_SOUND_ID = "sound:ai_secretary/_system/prompt_2"
PROMPT_3_SOUND_ID = "sound:ai_secretary/_system/prompt_3"
PROMPT_CITY_RETRY_SOUND_ID = "sound:ai_secretary/_system/prompt_city_retry"
PROMPT_4_SOUND_ID = "sound:ai_secretary/_system/prompt_4_v2"
PHONE_CONFIRM_PREFIX_SOUND_ID = "sound:ai_secretary/_system/phone_confirm_prefix"
PHONE_CONFIRM_SUFFIX_SOUND_ID = "sound:ai_secretary/_system/phone_confirm_suffix"
PHONE_CONFIRM_HOLDING_SOUND_ID = "sound:ai_secretary/_system/holding_phone_check"
FALLBACK_SOUND_ID = "sound:ai_secretary/_system/fallback"
TRANSFER_SOUND_ID = "sound:ai_secretary/_system/transfer"
TRANSFER_ACCOUNTING_SOUND_ID = "sound:ai_secretary/_system/transfer_accounting"
TRANSFER_DELIVERY_SOUND_ID = "sound:ai_secretary/_system/transfer_delivery"
AFTER_HOURS_SALES_SOUND_ID = "sound:ai_secretary/_system/after_hours_sales_v2"
AFTER_HOURS_ACCOUNTING_SOUND_ID = "sound:ai_secretary/_system/after_hours_accounting_v2"
AFTER_HOURS_DELIVERY_SOUND_ID = "sound:ai_secretary/_system/after_hours_delivery_v2"
SAFE_FINISH_BASELINE_SOUND_ID = "sound:ai_secretary/_system/safe_finish"
SAFE_FINISH_MISSING_REQUIRED_SOUND_ID = "sound:ai_secretary/_system/safe_finish_missing_required_data"
SAFE_FINISH_INTENT_NOT_RESOLVED_SOUND_ID = "sound:ai_secretary/_system/safe_finish_intent_not_resolved"
SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID = "sound:ai_secretary/_system/safe_finish_phone_not_confirmed"
PROMPT_FALLBACK_SOUND_IDS: dict[DialogStage, str] = {
    DialogStage.ISSUE: "sound:ai_secretary/_system/fallback_prompt_1",
    DialogStage.INTENT_CLARIFY: "sound:ai_secretary/_system/fallback_prompt_intent_clarify",
    DialogStage.NAME: "sound:ai_secretary/_system/fallback_prompt_2",
    DialogStage.CITY: "sound:ai_secretary/_system/fallback_prompt_3",
    DialogStage.PHONE: "sound:ai_secretary/_system/fallback_prompt_4",
}
TRANSFER_FALLBACK_SOUND_ID = "sound:ai_secretary/_system/fallback_transfer"
DEFAULT_RECORD_WAIT_PAD_SECONDS = 3
DEFAULT_ISSUE_GUARD_DELAY_MS = 350
DEFAULT_ISSUE_PLAYBACK_TIMEOUT_SECONDS = 15
DEFAULT_INTENT_CLARIFY_GUARD_DELAY_MS = 300
DEFAULT_INTENT_CLARIFY_PLAYBACK_TIMEOUT_SECONDS = 15
DEFAULT_PHONE_CONFIRM_GUARD_DELAY_MS = 400
DEFAULT_PHONE_CONFIRM_PLAYBACK_TIMEOUT_SECONDS = 15
DEFAULT_NAME_GUARD_DELAY_MS = 400
DEFAULT_NAME_PLAYBACK_TIMEOUT_SECONDS = 15
DEFAULT_AFTER_HOURS_GUARD_DELAY_MS = 400
DEFAULT_AFTER_HOURS_PLAYBACK_TIMEOUT_SECONDS = 20
DEFAULT_SAFE_FINISH_PLAYBACK_TIMEOUT_SECONDS = 20
DEFAULT_LATENCY_SILENCE_WARN_MS = 5000
DEFAULT_LATENCY_SILENCE_CRITICAL_MS = 10000
DEFAULT_PHONE_CONFIRM_HOLDING_PLAYBACK_TIMEOUT_SECONDS = 5
NAME_STT_LANGUAGE = "ru"
NAME_STT_PROMPT = (
    "Русская речь. Ожидается короткий ответ с именем клиента: имя, имя и отчество "
    "или разговорная форма имени. Примеры: Иван, Александр, Саня, Дмитрий, Ольга, "
    "Светлана Ивановна, Сергей Петрович."
)
CITY_STT_LANGUAGE = "ru"
CITY_STT_PROMPT = (
    "Ожидается название российского города или региона на русском языке, например: Москва, "
    "Санкт-Петербург, Самара, Нижний Тагил, Ростов-на-Дону, Екатеринбург, Краснодар, Московская область."
)
BUILTIN_GENERAL_FALLBACK_MEDIA = ("sound:please-try-again", "sound:pls-try-call-later")
BUILTIN_PROMPT_FALLBACK_MEDIA: dict[DialogStage, str] = {
    DialogStage.ISSUE: "sound:please-try-again",
    DialogStage.NAME: "sound:please-try-again",
    DialogStage.CITY: "sound:please-try-again",
    DialogStage.PHONE: "sound:please-try-again",
}
BUILTIN_TRANSFER_FALLBACK_MEDIA = ("sound:pls-wait-connect-call", "sound:please-hold-while-try")
TRANSFER_SOUND_IDS: dict[Department, str] = {
    "sales": TRANSFER_SOUND_ID,
    "accounting": TRANSFER_ACCOUNTING_SOUND_ID,
    "delivery": TRANSFER_DELIVERY_SOUND_ID,
}
PHONE_CONFIRM_PREFIX_PHRASE = "\u041f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e \u043b\u0438 \u044f \u0437\u0430\u043f\u0438\u0441\u0430\u043b\u0430 \u0432\u0430\u0448 \u043d\u043e\u043c\u0435\u0440"
PHONE_CONFIRM_SUFFIX_PHRASE = "\u0432\u0435\u0440\u043d\u043e?"
PHONE_CONFIRM_HOLDING_PHRASE = "\u0421\u0435\u043a\u0443\u043d\u0434\u0443, \u043f\u0440\u043e\u0432\u0435\u0440\u044f\u044e \u043d\u043e\u043c\u0435\u0440."
PHONE_CONFIRM_DIGIT_SOUND_IDS: dict[str, str] = {
    digit: f"sound:ai_secretary/_system/digits/{digit}" for digit in "0123456789"
}
PHONE_CONFIRM_DIGIT_PHRASES: dict[str, str] = {
    "0": "\u043d\u043e\u043b\u044c",
    "1": "\u043e\u0434\u0438\u043d",
    "2": "\u0434\u0432\u0430",
    "3": "\u0442\u0440\u0438",
    "4": "\u0447\u0435\u0442\u044b\u0440\u0435",
    "5": "\u043f\u044f\u0442\u044c",
    "6": "\u0448\u0435\u0441\u0442\u044c",
    "7": "\u0441\u0435\u043c\u044c",
    "8": "\u0432\u043e\u0441\u0435\u043c\u044c",
    "9": "\u0434\u0435\u0432\u044f\u0442\u044c",
}
TRANSFER_PHRASES: dict[Department, str] = {
    "sales": "\u0425\u043e\u0440\u043e\u0448\u043e, \u044f \u0441\u043e\u0435\u0434\u0438\u043d\u044f\u044e \u0432\u0430\u0441 \u0441 \u043e\u0442\u0434\u0435\u043b\u043e\u043c \u043f\u0440\u043e\u0434\u0430\u0436.",
    "accounting": "\u0425\u043e\u0440\u043e\u0448\u043e, \u044f \u0441\u043e\u0435\u0434\u0438\u043d\u044f\u044e \u0432\u0430\u0441 \u0441 \u0431\u0443\u0445\u0433\u0430\u043b\u0442\u0435\u0440\u0438\u0435\u0439.",
    "delivery": "\u0425\u043e\u0440\u043e\u0448\u043e, \u044f \u0441\u043e\u0435\u0434\u0438\u043d\u044f\u044e \u0432\u0430\u0441 \u0441 \u043e\u0442\u0434\u0435\u043b\u043e\u043c \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438.",
}
AFTER_HOURS_SOUND_IDS: dict[Department, str] = {
    "sales": AFTER_HOURS_SALES_SOUND_ID,
    "accounting": AFTER_HOURS_ACCOUNTING_SOUND_ID,
    "delivery": AFTER_HOURS_DELIVERY_SOUND_ID,
}
AFTER_HOURS_PHRASES: dict[Department, str] = {
    "sales": (
        "\u041e\u0442\u0434\u0435\u043b \u043f\u0440\u043e\u0434\u0430\u0436 \u0441\u0435\u0439\u0447\u0430\u0441 "
        "\u043d\u0435 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442. \u041c\u044b \u0437\u0430\u043f\u0438\u0441\u0430\u043b\u0438 "
        "\u0432\u0430\u0448\u0435 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435, \u0438 \u043e\u0442\u0434\u0435\u043b "
        "\u043f\u0440\u043e\u0434\u0430\u0436 \u043f\u0435\u0440\u0435\u0437\u0432\u043e\u043d\u0438\u0442 \u0432\u0430\u043c "
        "\u0432 \u0440\u0430\u0431\u043e\u0447\u0435\u0435 \u0432\u0440\u0435\u043c\u044f. \u0421\u043f\u0430\u0441\u0438\u0431\u043e "
        "\u0437\u0430 \u0437\u0432\u043e\u043d\u043e\u043a. \u0414\u043e \u0441\u0432\u0438\u0434\u0430\u043d\u0438\u044f."
    ),
    "accounting": (
        "\u0411\u0443\u0445\u0433\u0430\u043b\u0442\u0435\u0440\u0438\u044f \u0441\u0435\u0439\u0447\u0430\u0441 "
        "\u043d\u0435 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442. \u041c\u044b \u0437\u0430\u043f\u0438\u0441\u0430\u043b\u0438 "
        "\u0432\u0430\u0448\u0435 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435, \u0438 \u0431\u0443\u0445\u0433\u0430\u043b\u0442\u0435\u0440\u0438\u044f "
        "\u043f\u0435\u0440\u0435\u0437\u0432\u043e\u043d\u0438\u0442 \u0432\u0430\u043c \u0432 \u0440\u0430\u0431\u043e\u0447\u0435\u0435 "
        "\u0432\u0440\u0435\u043c\u044f. \u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 "
        "\u0437\u0432\u043e\u043d\u043e\u043a. \u0414\u043e \u0441\u0432\u0438\u0434\u0430\u043d\u0438\u044f."
    ),
    "delivery": (
        "\u041e\u0442\u0434\u0435\u043b \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438 \u0441\u0435\u0439\u0447\u0430\u0441 "
        "\u043d\u0435 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442. \u041c\u044b \u0437\u0430\u043f\u0438\u0441\u0430\u043b\u0438 "
        "\u0432\u0430\u0448\u0435 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435, \u0438 \u043e\u0442\u0434\u0435\u043b "
        "\u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438 \u043f\u0435\u0440\u0435\u0437\u0432\u043e\u043d\u0438\u0442 \u0432\u0430\u043c "
        "\u0432 \u0440\u0430\u0431\u043e\u0447\u0435\u0435 \u0432\u0440\u0435\u043c\u044f. \u0421\u043f\u0430\u0441\u0438\u0431\u043e "
        "\u0437\u0430 \u0437\u0432\u043e\u043d\u043e\u043a. \u0414\u043e \u0441\u0432\u0438\u0434\u0430\u043d\u0438\u044f."
    ),
}
SAFE_FINISH_BASELINE_PHRASE = (
    "\u0418\u0437\u0432\u0438\u043d\u0438\u0442\u0435, \u044f \u043d\u0435 \u0441\u043c\u043e\u0433\u043b\u0430 "
    "\u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u043e \u0437\u0430\u043f\u0438\u0441\u0430\u0442\u044c "
    "\u0432\u0430\u0448\u0438 \u0434\u0430\u043d\u043d\u044b\u0435. \u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, "
    "\u043f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u0435 \u0435\u0449\u0451 \u0440\u0430\u0437, \u0438 \u044f "
    "\u043f\u043e\u0441\u0442\u0430\u0440\u0430\u044e\u0441\u044c \u043f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e "
    "\u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435 "
    "\u0438 \u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c \u0432\u0430\u0441 \u0441\u043e "
    "\u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u043e\u043c."
)
SAFE_FINISH_PHRASES: dict[str, str] = {
    "baseline": SAFE_FINISH_BASELINE_PHRASE,
    "missing_required_data": (
        "\u0418\u0437\u0432\u0438\u043d\u0438\u0442\u0435, \u044f \u043d\u0435 \u0441\u043c\u043e\u0433\u043b\u0430 "
        "\u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u043e \u0437\u0430\u043f\u0438\u0441\u0430\u0442\u044c "
        "\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435. "
        "\u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, \u043f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u0435 "
        "\u0435\u0449\u0451 \u0440\u0430\u0437, \u0438 \u044f \u043f\u043e\u0441\u0442\u0430\u0440\u0430\u044e\u0441\u044c "
        "\u043f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e \u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u0442\u044c "
        "\u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435 \u0438 \u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c "
        "\u0432\u0430\u0441 \u0441\u043e \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u043e\u043c."
    ),
    "intent_not_resolved": (
        "\u0418\u0437\u0432\u0438\u043d\u0438\u0442\u0435, \u044f \u043d\u0435 \u0441\u043c\u043e\u0433\u043b\u0430 "
        "\u043d\u0430\u0434\u0451\u0436\u043d\u043e \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442\u044c "
        "\u043d\u0443\u0436\u043d\u044b\u0439 \u043e\u0442\u0434\u0435\u043b. \u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, "
        "\u043f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u0435 \u0435\u0449\u0451 \u0440\u0430\u0437, \u0438 \u044f "
        "\u043f\u043e\u0441\u0442\u0430\u0440\u0430\u044e\u0441\u044c \u043f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e "
        "\u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435 "
        "\u0438 \u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c \u0432\u0430\u0441 \u0441\u043e "
        "\u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u043e\u043c."
    ),
    "phone_not_confirmed": (
        "\u0418\u0437\u0432\u0438\u043d\u0438\u0442\u0435, \u044f \u043d\u0435 \u0441\u043c\u043e\u0433\u043b\u0430 "
        "\u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c \u043d\u043e\u043c\u0435\u0440 "
        "\u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430 \u0434\u043b\u044f \u0441\u0432\u044f\u0437\u0438. "
        "\u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, \u043f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u0435 "
        "\u0435\u0449\u0451 \u0440\u0430\u0437, \u0438 \u044f \u043f\u043e\u0441\u0442\u0430\u0440\u0430\u044e\u0441\u044c "
        "\u043f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e \u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u0442\u044c "
        "\u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435 \u0438 \u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c "
        "\u0432\u0430\u0441 \u0441\u043e \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u043e\u043c."
    ),
}
SAFE_FINISH_SOUND_IDS: dict[str, str] = {
    "baseline": SAFE_FINISH_BASELINE_SOUND_ID,
    "missing_required_data": SAFE_FINISH_MISSING_REQUIRED_SOUND_ID,
    "intent_not_resolved": SAFE_FINISH_INTENT_NOT_RESOLVED_SOUND_ID,
    "phone_not_confirmed": SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID,
}
SAFE_FINISH_REASON_ALIASES: dict[str, str] = {
    "name_retry_limit": "missing_required_data",
    "city_retry_limit": "missing_required_data",
    "dialog_retry_limit": "missing_required_data",
    "intent_retry_limit": "intent_not_resolved",
    "intent_not_resolved": "intent_not_resolved",
    "phone_retry_limit": "phone_not_confirmed",
    "phone_not_confirmed": "phone_not_confirmed",
    "missing_required_data": "missing_required_data",
}

_SYSTEM_SOUND_TEXTS: dict[str, str] = {
    PROMPT_1_SOUND_ID: PROMPTS[DialogStage.ISSUE],
    PROMPT_CLARIFY_SOUND_ID: PROMPTS[DialogStage.INTENT_CLARIFY],
    PROMPT_2_SOUND_ID: PROMPTS[DialogStage.NAME],
    PROMPT_3_SOUND_ID: PROMPTS[DialogStage.CITY],
    PROMPT_CITY_RETRY_SOUND_ID: CITY_RETRY_STATIC_PROMPT,
    PROMPT_4_SOUND_ID: PROMPTS[DialogStage.PHONE],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.ISSUE]: PROMPTS[DialogStage.ISSUE],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.INTENT_CLARIFY]: PROMPTS[DialogStage.INTENT_CLARIFY],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.NAME]: PROMPTS[DialogStage.NAME],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.CITY]: PROMPTS[DialogStage.CITY],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.PHONE]: PROMPTS[DialogStage.PHONE],
    PHONE_CONFIRM_PREFIX_SOUND_ID: PHONE_CONFIRM_PREFIX_PHRASE,
    PHONE_CONFIRM_SUFFIX_SOUND_ID: PHONE_CONFIRM_SUFFIX_PHRASE,
    **{PHONE_CONFIRM_DIGIT_SOUND_IDS[digit]: text for digit, text in PHONE_CONFIRM_DIGIT_PHRASES.items()},
    PHONE_CONFIRM_HOLDING_SOUND_ID: PHONE_CONFIRM_HOLDING_PHRASE,
    FALLBACK_SOUND_ID: "Одну секунду, пожалуйста.",
    TRANSFER_SOUND_ID: TRANSFER_PHRASES["sales"],
    TRANSFER_ACCOUNTING_SOUND_ID: TRANSFER_PHRASES["accounting"],
    TRANSFER_DELIVERY_SOUND_ID: TRANSFER_PHRASES["delivery"],
    AFTER_HOURS_SALES_SOUND_ID: AFTER_HOURS_PHRASES["sales"],
    AFTER_HOURS_ACCOUNTING_SOUND_ID: AFTER_HOURS_PHRASES["accounting"],
    AFTER_HOURS_DELIVERY_SOUND_ID: AFTER_HOURS_PHRASES["delivery"],
    TRANSFER_FALLBACK_SOUND_ID: TRANSFER_PHRASES["sales"],
    SAFE_FINISH_BASELINE_SOUND_ID: SAFE_FINISH_PHRASES["baseline"],
    SAFE_FINISH_MISSING_REQUIRED_SOUND_ID: SAFE_FINISH_PHRASES["missing_required_data"],
    SAFE_FINISH_INTENT_NOT_RESOLVED_SOUND_ID: SAFE_FINISH_PHRASES["intent_not_resolved"],
    SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID: SAFE_FINISH_PHRASES["phone_not_confirmed"],
}
_system_sound_status: dict[str, bool] = {sound_id: False for sound_id in _SYSTEM_SOUND_TEXTS}
_system_sounds_done = False
_system_sounds_lock: asyncio.Lock | None = None
_system_sounds_task: asyncio.Task[dict[str, bool]] | None = None


@dataclass(frozen=True)
class TranscriptionArtifact:
    """The exact audio artifact passed to transcription."""

    call_id: str
    channel_id: str
    stage: DialogStage
    turn_idx: int
    record_name: str
    path: Path
    size_bytes: int
    sha256: str

    def details(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "channel_id": self.channel_id,
            "stage": self.stage.value,
            "turn_idx": self.turn_idx,
            "record_name": self.record_name,
            "audio_path": str(self.path.as_posix()),
            "audio_size_bytes": self.size_bytes,
            "audio_sha256": self.sha256,
        }


@dataclass(frozen=True)
class RecordProfile:
    """Per-stage recording contour for the turn-based dialog."""

    max_duration_seconds: int
    max_silence_seconds: int
    wait_timeout_seconds: int

    def details(self) -> dict[str, int]:
        return {
            "max_duration_seconds": self.max_duration_seconds,
            "max_silence_seconds": self.max_silence_seconds,
            "wait_timeout_seconds": self.wait_timeout_seconds,
        }


@dataclass(frozen=True)
class RecordingEarlyStopPolicy:
    """Stage-specific TALK_DETECT early-stop contour."""

    enabled: bool
    stable_silence_ms: int
    min_talking_ms: int
    min_recording_ms: int
    require_talking_started: bool
    talk_detect_silence_ms: int = 0
    talk_detect_talking_threshold: int = 128
    reason: str = ""

    def details(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "stable_silence_ms": self.stable_silence_ms,
            "min_talking_ms": self.min_talking_ms,
            "min_recording_ms": self.min_recording_ms,
            "require_talking_started": self.require_talking_started,
            "talk_detect_silence_ms": self.talk_detect_silence_ms,
            "talk_detect_talking_threshold": self.talk_detect_talking_threshold,
            "reason": self.reason,
        }


@dataclass
class RecordingEventSubscription:
    queue: asyncio.Queue[dict[str, Any]]
    unsubscribe: Callable[[asyncio.Queue[dict[str, Any]]], None]

    def close(self) -> None:
        self.unsubscribe(self.queue)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _env_int_optional(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    try:
        value = int(raw.strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def _stage_env_int(stage: DialogStage, suffix: str, default: int) -> int:
    stage_name = stage.value.upper()
    for name in (
        f"RECORD_{stage_name}_{suffix}",
        f"RECORD_SLOT_{suffix}",
        f"RECORD_{suffix}",
    ):
        value = _env_int_optional(name)
        if value is not None:
            return value
    return default


def _record_profile_for_stage(stage: DialogStage) -> RecordProfile:
    """Return stage-specific turn-recording limits without changing architecture."""
    defaults = {
        DialogStage.ISSUE: (8, 2),
        DialogStage.NAME: (6, 2),
        DialogStage.CITY: (7, 3),
        DialogStage.PHONE: (14, 4),
        DialogStage.PHONE_CONFIRM: (6, 3),
    }
    default_duration, default_silence = defaults.get(stage, (4, 1))
    max_duration = _stage_env_int(stage, "MAX_DURATION_SECONDS", default_duration)
    max_silence = _stage_env_int(stage, "MAX_SILENCE_SECONDS", default_silence)
    wait_pad = _stage_env_int(stage, "WAIT_PAD_SECONDS", DEFAULT_RECORD_WAIT_PAD_SECONDS)
    wait_timeout = _stage_env_int(stage, "WAIT_TIMEOUT_SECONDS", max(3, max_duration + max_silence + wait_pad))
    return RecordProfile(
        max_duration_seconds=max_duration,
        max_silence_seconds=max_silence,
        wait_timeout_seconds=wait_timeout,
    )


def _recording_early_stop_enabled() -> bool:
    return os.getenv("RECORDING_EARLY_STOP_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}


def _talk_detect_value_for_policy(policy: RecordingEarlyStopPolicy) -> str:
    override = os.getenv("TALK_DETECT_SET_VALUE", "").strip()
    if override:
        return override
    return f"{policy.talk_detect_silence_ms},{policy.talk_detect_talking_threshold}"


def _recording_early_stop_policy_for_stage(
    stage: DialogStage,
    profile: dict[str, Any] | None = None,
) -> RecordingEarlyStopPolicy:
    if not _recording_early_stop_enabled():
        return RecordingEarlyStopPolicy(False, 0, 0, 0, True, 0, 128, "disabled")
    if stage == DialogStage.NAME:
        return RecordingEarlyStopPolicy(True, 350, 120, 400, True, 250, 128, "short_slot")
    if stage == DialogStage.CITY:
        if profile and profile.get("city_retry_reliable_mode"):
            return RecordingEarlyStopPolicy(True, 1400, 500, 2500, True, 1100, 128, "city_retry_conservative_talk_detect")
        return RecordingEarlyStopPolicy(True, 800, 200, 900, True, 600, 128, "short_slot_reliable")
    if stage == DialogStage.PHONE_CONFIRM:
        return RecordingEarlyStopPolicy(True, 300, 80, 250, True, 220, 128, "yes_no")
    if stage == DialogStage.INTENT_CLARIFY:
        return RecordingEarlyStopPolicy(True, 550, 150, 500, True, 350, 128, "short_slot")
    if stage == DialogStage.ISSUE:
        return RecordingEarlyStopPolicy(True, 1600, 500, 2500, True, 900, 128, "free_form_conservative")
    if stage == DialogStage.PHONE:
        return RecordingEarlyStopPolicy(False, 2800, 800, 7000, True, 0, 128, "phone_digit_safety_skip")
    return RecordingEarlyStopPolicy(False, 0, 0, 0, True, 0, 128, "unsupported_stage")


def _publish_total_timeout_sec() -> int:
    value = _env_int("PUBLISH_TOTAL_TIMEOUT_SEC", 35)
    return value if value > 0 else 35


def _phone_confirm_guard_delay_ms() -> int:
    return _env_int("PHONE_CONFIRM_GUARD_DELAY_MS", DEFAULT_PHONE_CONFIRM_GUARD_DELAY_MS)


def _phone_confirm_playback_timeout_sec() -> int:
    value = _env_int("PHONE_CONFIRM_PLAYBACK_TIMEOUT_SECONDS", DEFAULT_PHONE_CONFIRM_PLAYBACK_TIMEOUT_SECONDS)
    return value if value > 0 else DEFAULT_PHONE_CONFIRM_PLAYBACK_TIMEOUT_SECONDS


def _city_early_stop_min_audio_bytes() -> int:
    value = _env_int("CITY_EARLY_STOP_MIN_AUDIO_BYTES", 2048)
    return value if value > 0 else 2048


def _phone_confirm_early_stop_min_audio_bytes() -> int:
    value = _env_int("PHONE_CONFIRM_EARLY_STOP_MIN_AUDIO_BYTES", 2048)
    return value if value > 0 else 2048


def _early_stop_download_retry_count() -> int:
    value = _env_int("EARLY_STOP_DOWNLOAD_RETRY_COUNT", 3)
    return value if value > 0 else 3


def _early_stop_download_retry_base_ms() -> int:
    value = _env_int("EARLY_STOP_DOWNLOAD_RETRY_BASE_MS", 120)
    return value if value > 0 else 120


def _name_guard_delay_ms() -> int:
    return _env_int("NAME_GUARD_DELAY_MS", DEFAULT_NAME_GUARD_DELAY_MS)


def _name_playback_timeout_sec() -> int:
    value = _env_int("NAME_PLAYBACK_TIMEOUT_SECONDS", DEFAULT_NAME_PLAYBACK_TIMEOUT_SECONDS)
    return value if value > 0 else DEFAULT_NAME_PLAYBACK_TIMEOUT_SECONDS


def _stage_prompt_guard_delay_ms(stage: DialogStage) -> int:
    if stage == DialogStage.ISSUE:
        return _env_int("ISSUE_GUARD_DELAY_MS", DEFAULT_ISSUE_GUARD_DELAY_MS)
    if stage == DialogStage.INTENT_CLARIFY:
        return _env_int("INTENT_CLARIFY_GUARD_DELAY_MS", DEFAULT_INTENT_CLARIFY_GUARD_DELAY_MS)
    if stage == DialogStage.NAME:
        return _name_guard_delay_ms()
    return 0


def _stage_prompt_playback_timeout_sec(stage: DialogStage) -> int:
    if stage == DialogStage.ISSUE:
        value = _env_int("ISSUE_PLAYBACK_TIMEOUT_SECONDS", DEFAULT_ISSUE_PLAYBACK_TIMEOUT_SECONDS)
        return value if value > 0 else DEFAULT_ISSUE_PLAYBACK_TIMEOUT_SECONDS
    if stage == DialogStage.INTENT_CLARIFY:
        value = _env_int("INTENT_CLARIFY_PLAYBACK_TIMEOUT_SECONDS", DEFAULT_INTENT_CLARIFY_PLAYBACK_TIMEOUT_SECONDS)
        return value if value > 0 else DEFAULT_INTENT_CLARIFY_PLAYBACK_TIMEOUT_SECONDS
    if stage == DialogStage.NAME:
        return _name_playback_timeout_sec()
    if stage == DialogStage.SAFE_FINISH:
        value = _env_int("SAFE_FINISH_PLAYBACK_TIMEOUT_SECONDS", DEFAULT_SAFE_FINISH_PLAYBACK_TIMEOUT_SECONDS)
        return value if value > 0 else DEFAULT_SAFE_FINISH_PLAYBACK_TIMEOUT_SECONDS
    return DEFAULT_NAME_PLAYBACK_TIMEOUT_SECONDS


def _requires_prompt_playback_barrier(stage: DialogStage) -> bool:
    return stage in {DialogStage.ISSUE, DialogStage.INTENT_CLARIFY, DialogStage.NAME, DialogStage.SAFE_FINISH}


def _after_hours_guard_delay_ms() -> int:
    return _env_int("AFTER_HOURS_GUARD_DELAY_MS", DEFAULT_AFTER_HOURS_GUARD_DELAY_MS)


def _after_hours_playback_timeout_sec() -> int:
    value = _env_int("AFTER_HOURS_PLAYBACK_TIMEOUT_SECONDS", DEFAULT_AFTER_HOURS_PLAYBACK_TIMEOUT_SECONDS)
    return value if value > 0 else DEFAULT_AFTER_HOURS_PLAYBACK_TIMEOUT_SECONDS


def _system_sounds_publish_timeout_sec() -> int:
    value = _env_int("SYSTEM_SOUNDS_PUBLISH_TIMEOUT_SEC", 45)
    return value if value > 0 else 45


def _system_lock_get() -> asyncio.Lock:
    global _system_sounds_lock
    if _system_sounds_lock is None:
        _system_sounds_lock = asyncio.Lock()
    return _system_sounds_lock


def _system_rel_path(sound_id: str) -> str:
    return sound_id.replace("sound:", "") + ".wav"


def _append_system_diag(payload: dict[str, Any]) -> None:
    path = Path("tmp/diag/system_sounds_publish.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _append_system_event(payload: dict[str, Any]) -> None:
    path = Path("tmp/diag/events.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _publish_fail_reason(message: str, details: dict[str, Any] | None = None) -> str:
    reason = (details or {}).get("reason")
    if isinstance(reason, str) and reason:
        return reason
    lowered = (message or "").lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    return "publish_failed"


def _publish_result_reason(result: dict[str, Any]) -> str:
    return _publish_fail_reason(str(result.get("error") or ""), result.get("details") or {})


def _playback_id_from_result(result: dict[str, Any]) -> str:
    details = result.get("details") or {}
    payload = details.get("payload") or {}
    playback_id = payload.get("id")
    return str(playback_id or "")


def _event_channel_id(event: dict[str, Any]) -> str:
    channel = event.get("channel")
    if isinstance(channel, dict):
        value = channel.get("id")
        if value:
            return str(value)
    channel = event.get("channel_id")
    if channel:
        return str(channel)
    return ""


async def _maybe_enable_talk_detect(
    client: AriClient,
    session: CallSession,
    stage: DialogStage,
    turn_idx: int,
    policy: RecordingEarlyStopPolicy,
) -> bool:
    session.log_event(
        action="recording_policy_selected",
        status="ok",
        details={"stage": stage.value, "turn_idx": turn_idx, **policy.details()},
    )
    if not policy.enabled:
        session.log_event(
            action="recording_early_stop_skipped",
            status="skipped",
            reason=policy.reason or "policy_disabled",
            details={"stage": stage.value, "turn_idx": turn_idx, **policy.details()},
        )
        return False
    setter = getattr(client, "set_channel_variable_safe", None)
    if not callable(setter):
        session.log_event(
            action="talk_detect_unavailable",
            status="skipped",
            reason="ari_client_set_variable_unavailable",
            details={"stage": stage.value, "turn_idx": turn_idx, **policy.details()},
        )
        return False
    value = _talk_detect_value_for_policy(policy)
    session.log_event(
        action="talk_detect_enable_attempt",
        status="start",
        details={"stage": stage.value, "turn_idx": turn_idx, "variable": "TALK_DETECT(set)", "value": value},
    )
    result = await setter(session.channel_id, "TALK_DETECT(set)", value)
    if result.get("ok"):
        session.log_event(
            action="talk_detect_enabled",
            status="ok",
            details={"stage": stage.value, "turn_idx": turn_idx, "variable": "TALK_DETECT(set)", "value": value},
        )
        return True
    session.log_event(
        action="talk_detect_unavailable",
        status="fail",
        reason=result.get("reason") or "set_variable_failed",
        http_status=result.get("http_status"),
        details={"stage": stage.value, "turn_idx": turn_idx, **(result.get("details") or {})},
    )
    return False


async def _open_recording_event_subscription(
    client: AriClient,
    app_name: str,
    session: CallSession,
    *,
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
    policy: RecordingEarlyStopPolicy,
    talk_detect_enabled: bool,
) -> RecordingEventSubscription | None:
    if not (policy.enabled and talk_detect_enabled):
        return None
    subscribe = getattr(client, "_subscribe_ws", None)
    unsubscribe = getattr(client, "_unsubscribe_ws", None)
    if not callable(subscribe) or not callable(unsubscribe):
        session.log_event(
            action="talk_detect_unavailable",
            status="skipped",
            reason="ari_client_event_subscription_unavailable",
            details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
        )
        return None
    try:
        queue = await subscribe(app_name=app_name, subscribe_all=True)
    except Exception as exc:
        session.log_event(
            action="talk_detect_unavailable",
            status="fail",
            reason="ari_client_event_subscription_failed",
            details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "error": repr(exc)},
        )
        return None
    session.log_event(
        action="talk_detect_event_subscription_started",
        status="ok",
        details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
    )
    return RecordingEventSubscription(queue=queue, unsubscribe=unsubscribe)


async def _wait_for_recording_with_optional_early_stop(
    client: AriClient,
    app_name: str,
    session: CallSession,
    *,
    record_name: str,
    stage: DialogStage,
    turn_idx: int,
    timeout: int,
    policy: RecordingEarlyStopPolicy,
    talk_detect_enabled: bool,
    record_start: float,
    event_subscription: RecordingEventSubscription | None = None,
) -> dict[str, Any]:
    if not (policy.enabled and talk_detect_enabled):
        return await client.wait_for_recording_finished(app_name, record_name, timeout=timeout)

    stop_safe = getattr(client, "stop_live_recording_safe", None)
    if not callable(stop_safe):
        if event_subscription is not None:
            event_subscription.close()
        session.log_event(
            action="recording_stop_method_selected",
            status="fail",
            reason="safe_stop_unavailable",
            details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
        )
        session.log_event(
            action="recording_early_stop_skipped",
            status="skipped",
            reason="safe_stop_unavailable",
            details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
        )
        return await client.wait_for_recording_finished(app_name, record_name, timeout=timeout)

    session.log_event(
        action="recording_stop_method_selected",
        status="ok",
        details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "method": "live_recording_stop_store"},
    )
    talk_state: dict[str, Any] = {
        "started": False,
        "finished": False,
        "out_of_order_finished": False,
    }

    async def _wait() -> dict[str, Any]:
        subscription = event_subscription
        if subscription is None:
            subscription = await _open_recording_event_subscription(
                client,
                app_name,
                session,
                stage=stage,
                turn_idx=turn_idx,
                record_name=record_name,
                policy=policy,
                talk_detect_enabled=talk_detect_enabled,
            )
        if subscription is None:
            return await client.wait_for_recording_finished(app_name, record_name, timeout=timeout)
        queue = subscription.queue
        talking_started_at: float | None = None
        talking_finished_at: float | None = None
        stop_task: asyncio.Task[dict[str, Any]] | None = None
        stop_attempted = False
        early_stop_used = False

        def _is_current_recording_completion(event: dict[str, Any]) -> bool:
            recording = event.get("recording", {})
            return (
                isinstance(recording, dict)
                and recording.get("name") == record_name
                and event.get("type") in {"RecordingFinished", "RecordingFailed"}
            )

        def _log_stop_failure(stop_result: dict[str, Any]) -> None:
            session.log_event(
                action="recording_early_stop_failed",
                status="fail",
                reason=stop_result.get("reason"),
                http_status=stop_result.get("http_status"),
                details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, **(stop_result.get("details") or {})},
            )

        def _complete_from_early_stop(stale_event: dict[str, Any] | None = None) -> dict[str, Any]:
            nonlocal early_stop_used
            early_stop_used = True
            completed_at = time.perf_counter()
            dur_ms = int((completed_at - record_start) * 1000)
            session.log_event(
                action="recording_early_stop_used",
                status="ok",
                dur_ms=dur_ms,
                details={
                    "stage": stage.value,
                    "turn_idx": turn_idx,
                    "record_name": record_name,
                    "recording_tail_ms": int((completed_at - (talking_finished_at or record_start)) * 1000),
                },
            )
            if stale_event is not None:
                session.log_event(
                    action="recording_event_stale",
                    status="ignored",
                    reason="early_stop_already_completed",
                    details={
                        "stage": stage.value,
                        "turn_idx": turn_idx,
                        "record_name": record_name,
                        "event_type": stale_event.get("type"),
                    },
                )
            return {
                "type": "RecordingFinished",
                "recording": {"name": record_name},
                "recording_early_stop_used": True,
                "recording_completion_source": "talk_detect_early_stop",
            }

        try:
            while True:
                if stop_task is None:
                    event = await queue.get()
                else:
                    queue_task = asyncio.create_task(queue.get())
                    done, pending = await asyncio.wait({queue_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
                    if stop_task in done:
                        if queue_task in pending:
                            queue_task.cancel()
                        stop_result = stop_task.result()
                        if stop_result.get("ok"):
                            stale_event = None
                            if queue_task in done and not queue_task.cancelled():
                                candidate = queue_task.result()
                                if _is_current_recording_completion(candidate):
                                    stale_event = candidate
                            return _complete_from_early_stop(stale_event)
                        elif stop_result.get("reason") == "event_pending_during_guard":
                            stop_attempted = False
                            session.log_event(
                                action="recording_early_stop_skipped",
                                status="skipped",
                                reason="event_pending_during_guard",
                                details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
                            )
                        else:
                            _log_stop_failure(stop_result)
                        stop_task = None
                        if queue_task in done and not queue_task.cancelled():
                            event = queue_task.result()
                        else:
                            continue
                    else:
                        event = queue_task.result()
                        if _is_current_recording_completion(event) and stop_task is not None and not stop_task.done():
                            stop_result = await stop_task
                            stop_task = None
                            if stop_result.get("ok"):
                                return _complete_from_early_stop(event)
                            _log_stop_failure(stop_result)

                if event.get("type") == "__ws_closed__":
                    return {}
                event_type = event.get("type")
                recording = event.get("recording", {})
                if isinstance(recording, dict) and recording.get("name") == record_name:
                    if event_type in {"RecordingFinished", "RecordingFailed"}:
                        if stop_task is not None and not stop_task.done():
                            stop_task.cancel()
                        if event_type == "RecordingFinished" and early_stop_used:
                            event = {**event, "recording_early_stop_used": True}
                        if event_type == "RecordingFinished":
                            event = {**event, "recording_completion_source": event.get("recording_completion_source") or "normal_record_done"}
                        return event
                    continue
                if _event_channel_id(event) != session.channel_id:
                    continue
                if event_type == "ChannelTalkingStarted":
                    if stop_task is not None and not stop_task.done() and talk_state["out_of_order_finished"]:
                        session.log_event(
                            action="talk_detect_event_order_anomaly",
                            status="handled",
                            reason="late_started_after_finished",
                            details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
                        )
                        continue
                    talk_state["started"] = True
                    if stop_task is not None and not stop_task.done():
                        stop_task.cancel()
                        stop_task = None
                        stop_attempted = False
                        session.log_event(
                            action="recording_early_stop_skipped",
                            status="skipped",
                            reason="speech_resumed_during_guard",
                            details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
                        )
                    talking_started_at = time.perf_counter()
                    session.log_event(
                        action="channel_talking_started",
                        status="ok",
                        details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
                    )
                    continue
                if event_type != "ChannelTalkingFinished":
                    continue
                finished_at = time.perf_counter()
                talk_state["finished"] = True
                talking_finished_at = finished_at
                talking_ms = int((finished_at - talking_started_at) * 1000) if talking_started_at else None
                elapsed_ms = int((finished_at - record_start) * 1000)
                session.log_event(
                    action="channel_talking_finished",
                    status="ok",
                    dur_ms=talking_ms,
                    details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "elapsed_ms": elapsed_ms},
                )
                if policy.require_talking_started and talking_started_at is None:
                    talk_state["out_of_order_finished"] = True
                    session.log_event(
                        action="talk_detect_event_order_anomaly",
                        status="handled",
                        reason="finished_before_started",
                        details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "elapsed_ms": elapsed_ms, **policy.details()},
                    )
                if talking_ms is not None and talking_ms < policy.min_talking_ms:
                    session.log_event(
                        action="recording_early_stop_skipped",
                        status="skipped",
                        reason="talking_too_short",
                        details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "talking_ms": talking_ms, **policy.details()},
                    )
                    continue
                if elapsed_ms < policy.min_recording_ms:
                    session.log_event(
                        action="recording_early_stop_skipped",
                        status="skipped",
                        reason="recording_too_short",
                        details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "elapsed_ms": elapsed_ms, **policy.details()},
                    )
                    continue
                if stop_attempted:
                    continue
                stop_attempted = True
                async def _guarded_stop() -> dict[str, Any]:
                    await asyncio.sleep(policy.stable_silence_ms / 1000)
                    if not queue.empty():
                        return {"ok": False, "reason": "event_pending_during_guard", "http_status": None, "details": {}}
                    session.log_event(
                        action="recording_early_stop_attempt",
                        status="start",
                        details={
                            "stage": stage.value,
                            "turn_idx": turn_idx,
                            "record_name": record_name,
                            "stable_silence_ms": policy.stable_silence_ms,
                        },
                    )
                    return await stop_safe(record_name)

                stop_task = asyncio.create_task(_guarded_stop())
        finally:
            subscription.close()
            if stop_task is not None and not stop_task.done():
                stop_task.cancel()

    try:
        return await asyncio.wait_for(_wait(), timeout=timeout)
    except (TimeoutError, asyncio.TimeoutError):
        if talk_state["started"] and not talk_state["finished"]:
            session.log_event(
                action="talk_detect_started_without_finished",
                status="handled",
                details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
            )
            session.log_event(
                action="talk_detect_no_finished_event",
                status="handled",
                details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
            )
            session.log_event(
                action="record_wait_timeout_after_talking_started",
                status="handled",
                dur_ms=int((time.perf_counter() - record_start) * 1000),
                details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, **policy.details()},
            )
        if talk_state["started"] or talk_state["finished"]:
            session.log_event(
                action="recording_timeout_recovery_attempt",
                status="start",
                details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "method": "live_recording_stop_store"},
            )
            result = await stop_safe(record_name)
            if result.get("ok"):
                session.log_event(
                    action="recording_timeout_recovery_used",
                    status="ok",
                    dur_ms=int((time.perf_counter() - record_start) * 1000),
                    details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
                )
                return {
                    "type": "RecordingFinished",
                    "recording": {"name": record_name},
                    "recovered": True,
                    "recording_completion_source": "timeout_recovery",
                }
            session.log_event(
                action="recording_timeout_recovery_failed",
                status="fail",
                reason=result.get("reason"),
                http_status=result.get("http_status"),
                details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, **(result.get("details") or {})},
            )
        raise


def _latency_silence_warn_ms() -> int:
    value = _env_int("LATENCY_SILENCE_WARN_MS", DEFAULT_LATENCY_SILENCE_WARN_MS)
    return value if value > 0 else DEFAULT_LATENCY_SILENCE_WARN_MS


def _latency_silence_critical_ms() -> int:
    value = _env_int("LATENCY_SILENCE_CRITICAL_MS", DEFAULT_LATENCY_SILENCE_CRITICAL_MS)
    return value if value > 0 else DEFAULT_LATENCY_SILENCE_CRITICAL_MS


def _phone_confirm_holding_enabled() -> bool:
    return os.getenv("PHONE_CONFIRM_HOLDING_PROMPT_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}


def _phone_confirm_holding_playback_timeout_sec() -> int:
    value = _env_int(
        "PHONE_CONFIRM_HOLDING_PLAYBACK_TIMEOUT_SECONDS",
        DEFAULT_PHONE_CONFIRM_HOLDING_PLAYBACK_TIMEOUT_SECONDS,
    )
    return value if value > 0 else DEFAULT_PHONE_CONFIRM_HOLDING_PLAYBACK_TIMEOUT_SECONDS


def _phone_confirm_fast_path_media(profile: dict[str, Any]) -> list[str]:
    digits = str(profile.get("phone_digits") or "")
    if not digits or any(ch not in PHONE_CONFIRM_DIGIT_SOUND_IDS for ch in digits):
        return []
    return [
        PHONE_CONFIRM_PREFIX_SOUND_ID,
        *(PHONE_CONFIRM_DIGIT_SOUND_IDS[ch] for ch in digits),
        PHONE_CONFIRM_SUFFIX_SOUND_ID,
    ]


def _phone_confirm_fast_path_missing(profile: dict[str, Any], system_sounds: dict[str, bool]) -> list[str]:
    media = _phone_confirm_fast_path_media(profile)
    if not media:
        return ["phone_digits"]
    return [sound_id for sound_id in media if not system_sounds.get(sound_id, False)]


def _phone_confirm_fast_path_available(profile: dict[str, Any], system_sounds: dict[str, bool]) -> bool:
    return not _phone_confirm_fast_path_missing(profile, system_sounds)


def _latency_context_details(context: dict[str, Any] | None, *, playback_stage: DialogStage | None = None) -> dict[str, Any]:
    if not context:
        return {}
    details = {
        "stage": context.get("stage"),
        "turn_idx": context.get("turn_idx"),
        "stage_enter_ts": context.get("stage_enter_ts"),
        "next_stage": context.get("next_stage"),
        "outcome": context.get("outcome"),
    }
    if playback_stage is not None:
        details["playback_stage"] = playback_stage.value
    return {key: value for key, value in details.items() if value is not None}


def _log_latency_segment(
    session: CallSession,
    action: str,
    context: dict[str, Any] | None,
    *,
    status: str = "ok",
    reason: str | None = None,
    dur_ms: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    session.log_event(
        action=action,
        status=status,
        reason=reason,
        dur_ms=dur_ms,
        details={**_latency_context_details(context), **(details or {})},
    )


def _log_latency_playback_started(
    session: CallSession,
    context: dict[str, Any] | None,
    *,
    playback_stage: DialogStage,
    media: str,
    sound_id: str,
    prompt_text: str,
    dynamic: bool,
    playback_kind: str = "prompt",
) -> None:
    started_perf = time.perf_counter()
    speech_end_perf = context.get("client_speech_end_perf") if context else None
    speech_to_playback_ms: int | None = None
    if isinstance(speech_end_perf, (int, float)):
        speech_to_playback_ms = int((started_perf - float(speech_end_perf)) * 1000)
    details = {
        **_latency_context_details(context, playback_stage=playback_stage),
        "prompt_text": prompt_text,
        "dynamic": dynamic,
        "playback_kind": playback_kind,
        "speech_to_playback_start_ms": speech_to_playback_ms,
    }
    session.log_event(
        action="latency_playback_started",
        status="start",
        media=media,
        sound_id=sound_id,
        details=details,
    )
    if speech_to_playback_ms is None:
        return
    critical_ms = _latency_silence_critical_ms()
    warn_ms = _latency_silence_warn_ms()
    if speech_to_playback_ms > critical_ms:
        status = "critical"
    elif speech_to_playback_ms > warn_ms:
        status = "warning"
    else:
        return
    session.log_event(
        action="latency_silence_risk",
        status=status,
        media=media,
        sound_id=sound_id,
        dur_ms=speech_to_playback_ms,
        details={**details, "warn_ms": warn_ms, "critical_ms": critical_ms},
    )


async def _play_publish_failure_fallback(
    client: AriClient,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
    *,
    reason: str,
    publish_details: dict[str, Any],
) -> tuple[bool, bool]:
    played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
    session.log_event(
        action="publish_fallback",
        status="ok" if played else "fail",
        reason=None if played else "fallback_play_failed",
        details={
            "publish_reason": reason,
            "publish_details": publish_details,
        },
    )
    return played, moh_started


async def ensure_system_sounds(settings: Settings) -> dict[str, bool]:
    """Generate and publish static system sounds once per process."""
    global _system_sounds_done
    if _system_sounds_done:
        return dict(_system_sound_status)

    lock = _system_lock_get()
    async with lock:
        if _system_sounds_done:
            return dict(_system_sound_status)

        print("SYSTEM_SOUNDS_START")
        started = time.perf_counter()
        details: dict[str, dict[str, Any]] = {}
        local_dir = settings.storage_dir / "_system"
        local_dir.mkdir(parents=True, exist_ok=True)
        tts: SileroTTS | None = None
        timeout_sec = _system_sounds_publish_timeout_sec()

        cmd_timeout_sec = max(1, timeout_sec - 5)
        for sound_id, text in _SYSTEM_SOUND_TEXTS.items():
            item_start = time.perf_counter()
            file_name = sound_id.split("/")[-1] + ".wav"
            local_path = local_dir / file_name
            try:
                if not local_path.exists():
                    if tts is None:
                        tts = SileroTTS()
                    wav = await asyncio.to_thread(tts.synthesize, text)
                    save_bytes(local_path, wav)
                remote_rel = _system_rel_path(sound_id)
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        publish_wav_to_asterisk,
                        local_path,
                        remote_rel,
                        settings,
                        cmd_timeout_sec=cmd_timeout_sec,
                    ),
                    timeout=timeout_sec,
                )
                ok = bool(result.get("ok"))
                dur_ms = int((time.perf_counter() - item_start) * 1000)
                _system_sound_status[sound_id] = ok
                reason = None if ok else _publish_result_reason(result)
                details[sound_id] = {
                    "ok": ok,
                    "dur_ms": dur_ms,
                    "error": result.get("error"),
                    "publish_result": result,
                }
                event_payload = {
                    "ts": _now_iso(),
                    "action": "system_sound_publish",
                    "status": "ok" if ok else "fail",
                    "sound_id": sound_id,
                    "remote_path": str(result.get("remote_path") or ""),
                    "dur_ms": dur_ms,
                    "reason": reason,
                    "details": result.get("details") or {},
                }
                if not ok:
                    event_payload["details"] = {
                        **event_payload["details"],
                        "error": result.get("error"),
                        "stderr_snippet": str(result.get("error") or "")[:400],
                    }
                _append_system_event(event_payload)
                print("SYSTEM_SOUNDS_ITEM", sound_id, "ok" if ok else "fail", json.dumps(result, ensure_ascii=False))
            except asyncio.TimeoutError:
                dur_ms = int((time.perf_counter() - item_start) * 1000)
                _system_sound_status[sound_id] = False
                details[sound_id] = {
                    "ok": False,
                    "dur_ms": dur_ms,
                    "error": "publish_timeout",
                }
                print("SYSTEM_SOUNDS_ITEM_TIMEOUT", sound_id)
                _append_system_event(
                    {
                        "ts": _now_iso(),
                        "action": "system_sound_publish",
                        "status": "fail",
                        "sound_id": sound_id,
                        "remote_path": _system_rel_path(sound_id),
                        "dur_ms": dur_ms,
                        "reason": "timeout",
                        "details": {"stderr_snippet": "outer_timeout", "timeout_sec": timeout_sec},
                    }
                )
            except Exception as exc:
                dur_ms = int((time.perf_counter() - item_start) * 1000)
                _system_sound_status[sound_id] = False
                details[sound_id] = {
                    "ok": False,
                    "dur_ms": dur_ms,
                    "error": repr(exc),
                }
                print("SYSTEM_SOUNDS_ITEM_FAIL", sound_id, repr(exc))
                _append_system_event(
                    {
                        "ts": _now_iso(),
                        "action": "system_sound_publish",
                        "status": "fail",
                        "sound_id": sound_id,
                        "remote_path": _system_rel_path(sound_id),
                        "dur_ms": dur_ms,
                        "reason": _publish_fail_reason(str(exc)),
                        "details": {"stderr_snippet": str(exc)[:400]},
                    }
                )

        total_ms = int((time.perf_counter() - started) * 1000)
        _system_sounds_done = True
        payload = {
            "action": "system_sounds_publish_total",
            "status": "ok" if all(_system_sound_status.values()) else "fail",
            "dur_ms": total_ms,
            "details": {"sounds": dict(_system_sound_status), "items": details},
        }
        _append_system_diag(payload)
        _append_system_event({"ts": _now_iso(), **payload})
        print("SYSTEM_SOUNDS_DONE", payload["status"], total_ms, dict(_system_sound_status))
        return dict(_system_sound_status)


def _start_system_sounds_task(settings: Settings) -> None:
    global _system_sounds_task
    if _system_sounds_task is None or _system_sounds_task.done():
        print("SYSTEM_SOUNDS_BG_START")
        _system_sounds_task = asyncio.create_task(ensure_system_sounds(settings), name="system-sounds-publish")
        def _on_done(task: asyncio.Task[dict[str, bool]]) -> None:
            try:
                status = task.result()
                print("SYSTEM_SOUNDS_BG_OK", status)
            except Exception as exc:
                print("SYSTEM_SOUNDS_BG_FAIL", repr(exc))
            finally:
                print("READY_WAITING_FOR_CALLS")

        _system_sounds_task.add_done_callback(_on_done)


def _system_sounds_snapshot() -> dict[str, bool]:
    return dict(_system_sound_status)


async def _maybe_start_moh(client: AriClient, session: CallSession, started: bool, action: str) -> bool:
    if started:
        return True
    result = await client.moh_start_safe(session.channel_id, moh_class="default")
    if result["ok"]:
        print("MOH_START_OK", session.call_id)
        session.log_event(action=action, status="ok")
        return True
    print("MOH_START_FAIL", session.call_id, result.get("http_status"))
    session.log_event(
        action=action,
        status="fail",
        reason=result.get("reason"),
        http_status=result.get("http_status"),
        details=result.get("details"),
    )
    return False


async def _maybe_stop_moh(client: AriClient, session: CallSession, started: bool) -> bool:
    if not started:
        return False
    result = await client.moh_stop_safe(session.channel_id)
    if result["ok"]:
        print("MOH_STOP_OK", session.call_id)
        session.log_event(action="moh_stop", status="ok")
    else:
        print("MOH_STOP_FAIL", session.call_id, result.get("http_status"))
        session.log_event(
            action="moh_stop",
            status="fail",
            reason=result.get("reason"),
            http_status=result.get("http_status"),
            details=result.get("details"),
        )
    return False


async def _play_fallback(
    client: AriClient,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
) -> tuple[bool, bool]:
    candidates: list[str] = []
    if system_sounds.get(FALLBACK_SOUND_ID, False):
        candidates.append(FALLBACK_SOUND_ID)
    candidates.extend(BUILTIN_GENERAL_FALLBACK_MEDIA)

    fallback_played = False
    for media in candidates:
        started = time.perf_counter()
        moh_started = await _maybe_stop_moh(client, session, moh_started)
        result = await client.play_safe(session.channel_id, media)
        dur_ms = int((time.perf_counter() - started) * 1000)
        if result["ok"]:
            session.log_event(action="play_fallback", status="ok", media=media, sound_id=media, dur_ms=dur_ms)
            fallback_played = True
            break
        session.log_event(
            action="play_fallback",
            status="fail",
            reason=result.get("reason"),
            http_status=result.get("http_status"),
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details=result.get("details"),
        )
        if result.get("reason") != "channel_gone":
            moh_started = await _maybe_start_moh(client, session, moh_started, action="moh_start_after_fallback_fail")
        else:
            return False, moh_started

    return fallback_played, moh_started


def _safe_finish_phrase_key(reason: str) -> str:
    return SAFE_FINISH_REASON_ALIASES.get(reason, "baseline")


def _resolve_safe_finish_phrase(
    reason: str,
    system_sounds: dict[str, bool],
) -> tuple[str, str, str, str, bool]:
    phrase_key = _safe_finish_phrase_key(reason)
    phrase_text = SAFE_FINISH_PHRASES.get(phrase_key) or SAFE_FINISH_BASELINE_PHRASE
    sound_id = SAFE_FINISH_SOUND_IDS.get(phrase_key) or SAFE_FINISH_BASELINE_SOUND_ID
    if system_sounds.get(sound_id, False):
        return phrase_key, phrase_text, sound_id, sound_id, True

    baseline_media = SAFE_FINISH_BASELINE_SOUND_ID
    return "baseline", SAFE_FINISH_BASELINE_PHRASE, baseline_media, baseline_media, system_sounds.get(baseline_media, False)


async def _wait_for_safe_finish_playback(
    client: AriClient,
    app_name: str,
    session: CallSession,
    *,
    playback_id: str,
    media: str,
    sound_id: str,
    phrase_key: str,
    phrase_text: str,
    reason: str,
) -> bool:
    timeout = _stage_prompt_playback_timeout_sec(DialogStage.SAFE_FINISH)
    started = time.perf_counter()
    try:
        event = await client.wait_for_playback_finished(app_name, playback_id, timeout=timeout)
    except TimeoutError:
        event = {"type": "timeout"}
    except asyncio.TimeoutError:
        event = {"type": "timeout"}
    dur_ms = int((time.perf_counter() - started) * 1000)
    details = {
        "safe_finish_reason": reason,
        "phrase_key": phrase_key,
        "phrase_text": phrase_text,
        "playback_id": playback_id,
        "timeout_seconds": timeout,
    }
    if event.get("type") == "PlaybackFinished":
        session.log_event(
            action="safe_finish_phrase_playback_finished",
            status="ok",
            media=media,
            sound_id=sound_id,
            dur_ms=dur_ms,
            details=details,
        )
        session.log_event(
            action="safe_finish_phrase_played",
            status="ok",
            media=media,
            sound_id=sound_id,
            dur_ms=dur_ms,
            details=details,
        )
        return True
    if event.get("type") == "timeout":
        session.log_event(
            action="safe_finish_phrase_playback_timeout",
            status="handled",
            reason="playback_timeout",
            media=media,
            sound_id=sound_id,
            dur_ms=dur_ms,
            details=details,
        )
        session.log_event(
            action="safe_finish_phrase_played",
            status="handled",
            reason="playback_timeout",
            media=media,
            sound_id=sound_id,
            dur_ms=dur_ms,
            details=details,
        )
        return False
    session.log_event(
        action="safe_finish_phrase_playback_failed",
        status="fail",
        reason=event.get("type") or "playback_event_missing",
        media=media,
        sound_id=sound_id,
        dur_ms=dur_ms,
        details={**details, "playback_event": event},
    )
    session.log_event(
        action="safe_finish_phrase_played",
        status="fail",
        reason=event.get("type") or "playback_event_missing",
        media=media,
        sound_id=sound_id,
        dur_ms=dur_ms,
        details=details,
    )
    return False


def _persist_callback_record(
    session: CallSession,
    storage_dir: Path,
    *,
    outcome_type: CallbackOutcomeType,
    outcome_reason: str,
    department: str = "",
) -> None:
    """Fail-soft persistence for callback-worthy terminal outcomes."""
    path = callback_records_path(storage_dir)
    session.log_event(
        action="persistence_attempt",
        status="start",
        details={
            "outcome_type": outcome_type,
            "outcome_reason": outcome_reason,
            "path": str(path.as_posix()),
        },
    )
    try:
        record = build_callback_record(
            call_id=session.call_id,
            profile=session.dialog.profile,
            outcome_type=outcome_type,
            outcome_reason=outcome_reason,
            department=department,
        )
        record_id = append_callback_record(path, record)
    except Exception as exc:
        session.log_event(
            action="persistence_failure",
            status="fail",
            reason=repr(exc),
            details={
                "outcome_type": outcome_type,
                "outcome_reason": outcome_reason,
                "path": str(path.as_posix()),
            },
        )
        return

    session.log_event(
        action="persistence_success",
        status="ok",
        details={
            "outcome_type": outcome_type,
            "outcome_reason": outcome_reason,
            "record_id": record_id,
            "path": str(path.as_posix()),
        },
    )


async def _play_safe_finish_phrase(
    client: AriClient,
    settings: Settings,
    app_name: str,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
    reason: str,
) -> tuple[bool, bool]:
    phrase_key, phrase_text, sound_id, media, media_available = _resolve_safe_finish_phrase(reason, system_sounds)
    session.log_event(
        action="safe_finish_phrase_resolved",
        status="ok",
        media=media if media_available else "",
        sound_id=sound_id if media_available else "",
        details={
            "safe_finish_reason": reason,
            "phrase_key": phrase_key,
            "phrase_text": phrase_text,
            "resolved_sound_id": sound_id if media_available else "",
            "resolved_media": media if media_available else "",
            "static_media_available": media_available,
        },
    )
    if not media_available:
        played, moh_started = await _play_dynamic_prompt(
            client,
            settings,
            app_name,
            session,
            DialogStage.SAFE_FINISH,
            phrase_text,
            moh_started,
        )
        session.log_event(
            action="safe_finish_phrase_played",
            status="ok" if played else "fail",
            reason=None if played else "dynamic_prompt_failed",
            details={
                "safe_finish_reason": reason,
                "phrase_key": phrase_key,
                "phrase_text": phrase_text,
                "dynamic": True,
            },
        )
        return played, moh_started

    started = time.perf_counter()
    moh_started = await _maybe_stop_moh(client, session, moh_started)
    result = await client.play_safe(session.channel_id, media)
    dur_ms = int((time.perf_counter() - started) * 1000)
    if result["ok"]:
        playback_id = _playback_id_from_result(result)
        session.log_event(
            action="safe_finish_phrase_playback_started",
            status="ok" if playback_id else "handled",
            reason=None if playback_id else "playback_id_missing",
            media=media,
            sound_id=sound_id,
            dur_ms=dur_ms,
            details={
                "safe_finish_reason": reason,
                "phrase_key": phrase_key,
                "phrase_text": phrase_text,
                "playback_id": playback_id,
                **(result.get("details") or {}),
            },
        )
        if not playback_id:
            session.log_event(
                action="safe_finish_phrase_playback_failed",
                status="fail",
                reason="playback_id_missing",
                media=media,
                sound_id=sound_id,
                details={
                    "safe_finish_reason": reason,
                    "phrase_key": phrase_key,
                    "phrase_text": phrase_text,
                },
            )
            session.log_event(
                action="safe_finish_phrase_played",
                status="fail",
                reason="playback_id_missing",
                media=media,
                sound_id=sound_id,
                details={
                    "safe_finish_reason": reason,
                    "phrase_key": phrase_key,
                    "phrase_text": phrase_text,
                },
            )
            return False, moh_started
        finished = await _wait_for_safe_finish_playback(
            client,
            app_name,
            session,
            playback_id=playback_id,
            media=media,
            sound_id=sound_id,
            phrase_key=phrase_key,
            phrase_text=phrase_text,
            reason=reason,
        )
        return True, moh_started

    session.log_event(
        action="safe_finish_phrase_playback_failed",
        status="fail",
        reason=result.get("reason"),
        http_status=result.get("http_status"),
        media=media,
        sound_id=sound_id,
        dur_ms=dur_ms,
        details={
            "safe_finish_reason": reason,
            "phrase_key": phrase_key,
            "phrase_text": phrase_text,
            **(result.get("details") or {}),
        },
    )
    session.log_event(
        action="safe_finish_phrase_played",
        status="fail",
        reason=result.get("reason"),
        http_status=result.get("http_status"),
        media=media,
        sound_id=sound_id,
        dur_ms=dur_ms,
        details={
            "safe_finish_reason": reason,
            "phrase_key": phrase_key,
            "phrase_text": phrase_text,
            **(result.get("details") or {}),
        },
    )
    return False, moh_started


def _prompt_media_for_stage(stage: DialogStage, system_sounds: dict[str, bool]) -> str:
    if stage == DialogStage.ISSUE and system_sounds.get(PROMPT_1_SOUND_ID, False):
        return PROMPT_1_SOUND_ID
    if stage == DialogStage.INTENT_CLARIFY and system_sounds.get(PROMPT_CLARIFY_SOUND_ID, False):
        return PROMPT_CLARIFY_SOUND_ID
    if stage == DialogStage.NAME and system_sounds.get(PROMPT_2_SOUND_ID, False):
        return PROMPT_2_SOUND_ID
    if stage == DialogStage.CITY and system_sounds.get(PROMPT_3_SOUND_ID, False):
        return PROMPT_3_SOUND_ID
    if stage == DialogStage.PHONE and system_sounds.get(PROMPT_4_SOUND_ID, False):
        return PROMPT_4_SOUND_ID
    fallback_sound_id = PROMPT_FALLBACK_SOUND_IDS.get(stage)
    if fallback_sound_id and system_sounds.get(fallback_sound_id, False):
        return fallback_sound_id
    if system_sounds.get(FALLBACK_SOUND_ID, False):
        return FALLBACK_SOUND_ID
    return BUILTIN_PROMPT_FALLBACK_MEDIA.get(stage, BUILTIN_GENERAL_FALLBACK_MEDIA[0])


def _static_retry_prompt_media(
    stage: DialogStage,
    prompt_text: str,
    system_sounds: dict[str, bool],
) -> str | None:
    if (
        stage == DialogStage.CITY
        and prompt_text == CITY_RETRY_STATIC_PROMPT
        and system_sounds.get(PROMPT_CITY_RETRY_SOUND_ID, False)
    ):
        return PROMPT_CITY_RETRY_SOUND_ID
    return None


async def _play_transfer_and_continue(
    client: AriClient,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
    app_name: str = "",
    storage_dir: Path | None = None,
) -> tuple[bool, bool]:
    missing_fields = required_fields_missing(session.dialog.profile)
    if missing_fields:
        session.log_event(
            action="transfer_blocked_missing_required_data",
            status="ok",
            details={
                "missing_required_fields": missing_fields,
                "early_transfer_requested": bool(session.dialog.profile.get("early_transfer_requested")),
                "department": session.dialog.profile.get("department"),
                "department_intent": session.dialog.profile.get("department_intent"),
            },
        )
        return False, moh_started

    issue_text = str(session.dialog.profile.get("issue") or "")
    routing_decision = classify_department_intent(issue_text)
    profile_department = session.dialog.profile.get("department")
    if profile_department in TRANSFER_PHRASES:
        transfer_target = route_for_department(profile_department)
    else:
        transfer_target = routing_decision.target
    transfer_phrase = TRANSFER_PHRASES[transfer_target.department]
    transfer_sound_id = TRANSFER_SOUND_IDS[transfer_target.department]
    hours_decision = business_hours_for_department(transfer_target.department)
    if system_sounds.get(transfer_sound_id, False):
        media = transfer_sound_id
    elif system_sounds.get(TRANSFER_FALLBACK_SOUND_ID, False):
        media = TRANSFER_FALLBACK_SOUND_ID
    else:
        media = BUILTIN_TRANSFER_FALLBACK_MEDIA[0]
    session.log_event(
        action="department_intent",
        status="ok",
        details={
            **routing_decision.to_dict(),
            "issue": issue_text,
            "profile_department": profile_department,
            "resolved_department": transfer_target.department,
            "business_hours_mode": hours_decision.mode,
            "early_transfer_requested": bool(session.dialog.profile.get("early_transfer_requested")),
            "missing_required_fields": missing_fields,
            "clarification_result": session.dialog.profile.get("department_clarification_result"),
        },
    )
    session.log_event(
        action="business_hours_decision",
        status="ok",
        details={
            **hours_decision.to_dict(),
            "resolved_department": transfer_target.department,
            "transfer_target": transfer_target.to_dict(),
        },
    )
    if hours_decision.mode == "after_hours":
        after_hours_phrase = AFTER_HOURS_PHRASES[transfer_target.department]
        after_hours_sound_id = AFTER_HOURS_SOUND_IDS[transfer_target.department]
        if system_sounds.get(after_hours_sound_id, False):
            after_hours_media = after_hours_sound_id
        elif system_sounds.get(FALLBACK_SOUND_ID, False):
            after_hours_media = FALLBACK_SOUND_ID
        else:
            after_hours_media = BUILTIN_GENERAL_FALLBACK_MEDIA[0]
        session.log_event(
            action="after_hours_phrase_resolved",
            status="ok",
            media=after_hours_media,
            sound_id=after_hours_media,
            details={
                "department": transfer_target.department,
                "intent": routing_decision.intent,
                "intent_reason": routing_decision.reason,
                "business_hours_mode": hours_decision.mode,
                "phrase_text": after_hours_phrase,
                "department_sound_id": after_hours_sound_id,
                "resolved_sound_id": after_hours_media,
                "static_media_available": system_sounds.get(after_hours_sound_id, False),
            },
        )
        started = time.perf_counter()
        moh_started = await _maybe_stop_moh(client, session, moh_started)
        play_result = await client.play_safe(session.channel_id, after_hours_media)
        playback_id = _playback_id_from_result(play_result)
        dur_ms = int((time.perf_counter() - started) * 1000)
        session.log_event(
            action="play_after_hours_phrase",
            status="ok" if play_result["ok"] else "fail",
            reason=None if play_result["ok"] else play_result.get("reason"),
            http_status=None if play_result["ok"] else play_result.get("http_status"),
            media=after_hours_media,
            sound_id=after_hours_media,
            dur_ms=dur_ms,
            details={
                **(play_result.get("details") or {}),
                "department": transfer_target.department,
                "intent": routing_decision.intent,
                "intent_reason": routing_decision.reason,
                "business_hours_mode": hours_decision.mode,
                "phrase_text": after_hours_phrase,
                "department_sound_id": after_hours_sound_id,
                "resolved_sound_id": after_hours_media,
                "playback_id": playback_id,
            },
        )
        barrier_ok = False
        if play_result["ok"]:
            barrier_ok = await _wait_for_after_hours_playback_barrier(
                client,
                app_name,
                session,
                after_hours_media,
                playback_id,
                department=transfer_target.department,
                phrase_text=after_hours_phrase,
            )
        session.log_event(
            action="transfer_skipped_after_hours",
            status="ok",
            details={
                **transfer_target.to_dict(),
                "intent": routing_decision.intent,
                "intent_reason": routing_decision.reason,
                "business_hours_mode": hours_decision.mode,
                "playback_id": playback_id,
                "after_hours_playback_completed": barrier_ok,
                "transfer_skipped": True,
            },
        )
        _persist_callback_record(
            session,
            storage_dir or session.artifact_dir,
            outcome_type="after_hours_callback",
            outcome_reason=hours_decision.reason,
            department=transfer_target.department,
        )
        hangup_start = time.perf_counter()
        hangup_result = await client.hangup_safe(session.channel_id)
        session.transition(
            CallState.DONE if hangup_result.get("ok") else CallState.FAILED,
            action="after_hours_handoff",
            status="ok" if hangup_result.get("ok") else "fail",
            reason=None if hangup_result.get("ok") else hangup_result.get("reason"),
            http_status=None if hangup_result.get("ok") else hangup_result.get("http_status"),
            dur_ms=int((time.perf_counter() - hangup_start) * 1000),
            details={
                **(hangup_result.get("details") or {}),
                "department": transfer_target.department,
                "business_hours_mode": hours_decision.mode,
                "playback_id": playback_id,
                "after_hours_playback_completed": barrier_ok,
                "transfer_skipped": True,
            },
        )
        return True, moh_started
    session.log_event(
        action="transfer_phrase_resolved",
        status="ok",
        media=media,
        sound_id=media,
        details={
            "department": transfer_target.department,
            "intent": routing_decision.intent,
            "intent_reason": routing_decision.reason,
            "business_hours_mode": hours_decision.mode,
            "early_transfer_requested": bool(session.dialog.profile.get("early_transfer_requested")),
            "missing_required_fields": missing_fields,
            "phrase_text": transfer_phrase,
            "department_sound_id": transfer_sound_id,
            "resolved_sound_id": media,
        },
    )
    started = time.perf_counter()
    moh_started = await _maybe_stop_moh(client, session, moh_started)
    play_result = await client.play_safe(session.channel_id, media)
    dur_ms = int((time.perf_counter() - started) * 1000)
    if not play_result["ok"]:
        session.log_event(
            action="play_transfer_phrase",
            status="fail",
            reason=play_result.get("reason"),
            http_status=play_result.get("http_status"),
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details={
                **(play_result.get("details") or {}),
                "department": transfer_target.department,
                "intent": routing_decision.intent,
                "intent_reason": routing_decision.reason,
                "business_hours_mode": hours_decision.mode,
                "phrase_text": transfer_phrase,
                "department_sound_id": transfer_sound_id,
                "resolved_sound_id": media,
            },
        )
        return False, moh_started

    session.log_event(
        action="play_transfer_phrase",
        status="ok",
        media=media,
        sound_id=media,
        dur_ms=dur_ms,
        details={
            "department": transfer_target.department,
            "intent": routing_decision.intent,
            "intent_reason": routing_decision.reason,
            "business_hours_mode": hours_decision.mode,
            "phrase_text": transfer_phrase,
            "department_sound_id": transfer_sound_id,
            "resolved_sound_id": media,
        },
    )
    transfer_start = time.perf_counter()
    cont_result = await client.continue_safe(
        session.channel_id,
        context=transfer_target.context,
        extension=transfer_target.extension,
        priority=transfer_target.priority,
    )
    transfer_ms = int((time.perf_counter() - transfer_start) * 1000)
    if cont_result["ok"]:
        session.transition(
            CallState.DONE,
            action="transfer",
            status="ok",
            dur_ms=transfer_ms,
            details={
                **transfer_target.to_dict(),
                "intent": routing_decision.intent,
                "intent_reason": routing_decision.reason,
                "business_hours_mode": hours_decision.mode,
            },
        )
        return True, moh_started

    session.transition(
        CallState.FAILED,
        action="transfer",
        status="fail",
        reason=cont_result.get("reason"),
        http_status=cont_result.get("http_status"),
        dur_ms=transfer_ms,
        details={
            **(cont_result.get("details") or {}),
            **transfer_target.to_dict(),
            "intent": routing_decision.intent,
            "intent_reason": routing_decision.reason,
            "business_hours_mode": hours_decision.mode,
        },
    )
    return False, moh_started


async def _wait_for_after_hours_playback_barrier(
    client: AriClient,
    app_name: str,
    session: CallSession,
    media: str,
    playback_id: str,
    *,
    department: Department,
    phrase_text: str,
) -> bool:
    """Wait for after-hours handoff playback before hanging up."""
    barrier_timeout = _after_hours_playback_timeout_sec()
    guard_ms = _after_hours_guard_delay_ms()
    if not playback_id:
        session.log_event(
            action="after_hours_playback_barrier",
            status="fail",
            reason="playback_id_missing",
            media=media,
            sound_id=media,
            details={
                "department": department,
                "phrase_text": phrase_text,
                "playback_id": playback_id,
                "timeout_seconds": barrier_timeout,
                "guard_delay_ms": guard_ms,
            },
        )
        return False

    barrier_start = time.perf_counter()
    try:
        barrier_event = await client.wait_for_playback_finished(app_name, playback_id, timeout=barrier_timeout)
    except TimeoutError:
        barrier_event = {"type": "timeout"}
    except asyncio.TimeoutError:
        barrier_event = {"type": "timeout"}
    barrier_ms = int((time.perf_counter() - barrier_start) * 1000)
    if barrier_event.get("type") != "PlaybackFinished":
        session.log_event(
            action="after_hours_playback_barrier",
            status="fail",
            reason=str(barrier_event.get("type") or "playback_event_missing"),
            media=media,
            sound_id=media,
            dur_ms=barrier_ms,
            details={
                "department": department,
                "phrase_text": phrase_text,
                "playback_id": playback_id,
                "timeout_seconds": barrier_timeout,
                "guard_delay_ms": guard_ms,
            },
        )
        return False

    if guard_ms > 0:
        await asyncio.sleep(guard_ms / 1000)
    session.log_event(
        action="after_hours_playback_barrier",
        status="ok",
        media=media,
        sound_id=media,
        dur_ms=barrier_ms,
        details={
            "department": department,
            "phrase_text": phrase_text,
            "playback_id": playback_id,
            "timeout_seconds": barrier_timeout,
            "guard_delay_ms": guard_ms,
        },
    )
    return True


async def _play_phone_confirmation_prompt(
    client: AriClient,
    settings: Settings,
    app_name: str,
    session: CallSession,
    moh_started: bool,
    latency_context: dict[str, Any] | None = None,
) -> tuple[bool, bool]:
    system_sounds = _system_sounds_snapshot()
    short_retry_prompt = session.dialog.profile.get("phone_confirm_retry_prompt")
    short_retry_prompt_active = isinstance(short_retry_prompt, str) and bool(short_retry_prompt)
    if short_retry_prompt_active:
        session.log_event(
            action="phone_confirm_short_retry_prompt",
            status="ok",
            details={
                **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
                "prompt_text": short_retry_prompt,
                "fast_path_bypassed": True,
            },
        )
        missing_fast_path = [PHONE_CONFIRM_PREFIX_SOUND_ID]
    else:
        missing_fast_path = _phone_confirm_fast_path_missing(session.dialog.profile, system_sounds)
    if not missing_fast_path:
        return await _play_phone_confirmation_fast_prompt(client, app_name, session, moh_started, latency_context)
    if not short_retry_prompt_active:
        session.log_event(
            action="phone_confirm_fast_path_unavailable",
            status="handled",
            reason="missing_static_media",
            details={
                **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
                "phone_digits_present": bool(session.dialog.profile.get("phone_digits")),
                "missing_static_media": missing_fast_path,
            },
        )

    prompt_text = next_prompt(DialogStage.PHONE_CONFIRM, session.dialog.profile)
    started = time.perf_counter()
    prompt_path = session.artifact_dir / "phone_confirm_prompt.wav"
    tts_start = time.perf_counter()
    try:
        tts = SileroTTS()
        wav = await asyncio.to_thread(tts.synthesize, prompt_text)
        save_bytes(prompt_path, wav)
    except Exception as exc:
        session.log_event(
            action="phone_confirm_prompt_tts",
            status="fail",
            reason=repr(exc),
            dur_ms=int((time.perf_counter() - tts_start) * 1000),
            details={"prompt_text": prompt_text},
        )
        return False, moh_started
    session.log_event(
        action="phone_confirm_prompt_tts",
        status="ok",
        dur_ms=int((time.perf_counter() - tts_start) * 1000),
        details={"prompt_text": prompt_text},
    )
    _log_latency_segment(
        session,
        "latency_tts_done",
        latency_context,
        dur_ms=int((time.perf_counter() - tts_start) * 1000),
        details={"playback_stage": DialogStage.PHONE_CONFIRM.value, "prompt_text": prompt_text},
    )

    remote_rel_path = f"{settings.asterisk_sounds_subdir}/{session.call_id}/phone_confirm_prompt.wav"
    publish_start = time.perf_counter()
    publish_timeout_sec = _publish_total_timeout_sec()
    publish_cmd_timeout_sec = _env_int("PUBLISH_CMD_TIMEOUT_SEC", 15)
    try:
        publish_result = await asyncio.wait_for(
            asyncio.to_thread(
                publish_wav_to_asterisk,
                prompt_path,
                remote_rel_path,
                settings,
                cmd_timeout_sec=publish_cmd_timeout_sec,
            ),
            timeout=publish_timeout_sec,
        )
    except asyncio.TimeoutError:
        session.log_event(
            action="phone_confirm_prompt_publish",
            status="fail",
            reason="publish_timeout",
            dur_ms=int((time.perf_counter() - publish_start) * 1000),
            details={"remote_rel_path": remote_rel_path},
        )
        return False, moh_started

    publish_ms = int((time.perf_counter() - publish_start) * 1000)
    if not publish_result.get("ok"):
        session.log_event(
            action="phone_confirm_prompt_publish",
            status="fail",
            reason=_publish_result_reason(publish_result),
            dur_ms=publish_ms,
            details=publish_result,
        )
        return False, moh_started

    media = str(publish_result.get("sound_id"))
    session.log_event(
        action="phone_confirm_prompt_publish",
        status="ok",
        sound_id=media,
        remote_path=str(publish_result.get("remote_path") or ""),
        dur_ms=publish_ms,
        details=publish_result.get("details"),
    )
    _log_latency_segment(
        session,
        "latency_publish_done",
        latency_context,
        dur_ms=publish_ms,
        details={
            "playback_stage": DialogStage.PHONE_CONFIRM.value,
            "sound_id": media,
            "remote_path": str(publish_result.get("remote_path") or ""),
        },
    )

    moh_started = await _maybe_stop_moh(client, session, moh_started)
    _log_latency_playback_started(
        session,
        latency_context,
        playback_stage=DialogStage.PHONE_CONFIRM,
        media=media,
        sound_id=media,
        prompt_text=prompt_text,
        dynamic=True,
    )
    play_result = await client.play_safe(session.channel_id, media)
    playback_id = _playback_id_from_result(play_result)
    if not play_result["ok"]:
        dur_ms = int((time.perf_counter() - started) * 1000)
        session.log_event(
            action="play_prompt",
            status="fail",
            reason=play_result.get("reason"),
            http_status=play_result.get("http_status"),
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details={**(play_result.get("details") or {}), "stage": DialogStage.PHONE_CONFIRM.value},
        )
        return False, moh_started

    if not playback_id:
        dur_ms = int((time.perf_counter() - started) * 1000)
        session.log_event(
            action="phone_confirm_playback_barrier",
            status="fail",
            reason="playback_id_missing",
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details={"stage": DialogStage.PHONE_CONFIRM.value, "prompt_text": prompt_text},
        )
        return False, moh_started

    barrier_start = time.perf_counter()
    barrier_timeout = _phone_confirm_playback_timeout_sec()
    try:
        barrier_event = await client.wait_for_playback_finished(app_name, playback_id, timeout=barrier_timeout)
    except TimeoutError:
        barrier_event = {"type": "timeout"}
    except asyncio.TimeoutError:
        barrier_event = {"type": "timeout"}
    barrier_ms = int((time.perf_counter() - barrier_start) * 1000)
    if barrier_event.get("type") != "PlaybackFinished":
        _log_latency_segment(
            session,
            "latency_playback_finished",
            latency_context,
            status="fail",
            reason=str(barrier_event.get("type") or "playback_event_missing"),
            dur_ms=barrier_ms,
            details={
                "stage": DialogStage.PHONE_CONFIRM.value,
                "playback_id": playback_id,
                "media": media,
                "sound_id": media,
            },
        )
        session.log_event(
            action="phone_confirm_playback_barrier",
            status="fail",
            reason=barrier_event.get("type") or "playback_event_missing",
            media=media,
            sound_id=media,
            dur_ms=barrier_ms,
            details={
                "stage": DialogStage.PHONE_CONFIRM.value,
                "playback_id": playback_id,
                "timeout_seconds": barrier_timeout,
            },
        )
        return False, moh_started

    guard_ms = _phone_confirm_guard_delay_ms()
    if guard_ms > 0:
        await asyncio.sleep(guard_ms / 1000)
    dur_ms = int((time.perf_counter() - started) * 1000)
    session.log_event(
        action="phone_confirm_playback_barrier",
        status="ok",
        media=media,
        sound_id=media,
        dur_ms=barrier_ms,
        details={
            "stage": DialogStage.PHONE_CONFIRM.value,
            "playback_id": playback_id,
            "guard_delay_ms": guard_ms,
            "timeout_seconds": barrier_timeout,
        },
    )
    _log_latency_segment(
        session,
        "latency_playback_finished",
        latency_context,
        dur_ms=barrier_ms,
        details={
            "stage": DialogStage.PHONE_CONFIRM.value,
            "playback_id": playback_id,
            "media": media,
            "sound_id": media,
        },
    )
    session.log_event(
        action="play_prompt",
        status="ok",
        media=media,
        sound_id=media,
        dur_ms=dur_ms,
        details={"stage": DialogStage.PHONE_CONFIRM.value, "prompt_text": prompt_text},
    )
    return True, moh_started


async def _play_phone_confirmation_fast_prompt(
    client: AriClient,
    app_name: str,
    session: CallSession,
    moh_started: bool,
    latency_context: dict[str, Any] | None = None,
) -> tuple[bool, bool]:
    digits = str(session.dialog.profile.get("phone_digits") or "")
    media_sequence = _phone_confirm_fast_path_media(session.dialog.profile)
    prompt_text = next_prompt(DialogStage.PHONE_CONFIRM, session.dialog.profile)
    started = time.perf_counter()
    barrier_timeout = _phone_confirm_playback_timeout_sec()
    guard_ms = _phone_confirm_guard_delay_ms()

    session.log_event(
        action="phone_confirm_fast_path_used",
        status="ok",
        details={
            **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
            "phone_digits": digits,
            "media_sequence": media_sequence,
            "prompt_text": prompt_text,
            "dynamic_tts_required": False,
            "publish_required": False,
        },
    )

    moh_started = await _maybe_stop_moh(client, session, moh_started)
    playback_ids: list[str] = []
    barrier_total_ms = 0
    for index, media in enumerate(media_sequence):
        play_start = time.perf_counter()
        if index == 0:
            _log_latency_playback_started(
                session,
                latency_context,
                playback_stage=DialogStage.PHONE_CONFIRM,
                media=media,
                sound_id=media,
                prompt_text=prompt_text,
                dynamic=False,
                playback_kind="phone_confirm_fast_path",
            )
        play_result = await client.play_safe(session.channel_id, media)
        play_ms = int((time.perf_counter() - play_start) * 1000)
        playback_id = _playback_id_from_result(play_result)
        if not play_result["ok"]:
            session.log_event(
                action="phone_confirm_fast_path_play",
                status="fail",
                reason=play_result.get("reason"),
                http_status=play_result.get("http_status"),
                media=media,
                sound_id=media,
                dur_ms=play_ms,
                details={
                    **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
                    **(play_result.get("details") or {}),
                    "sequence_index": index,
                    "phone_digits": digits,
                },
            )
            return False, moh_started
        if not playback_id:
            session.log_event(
                action="phone_confirm_playback_barrier",
                status="fail",
                reason="playback_id_missing",
                media=media,
                sound_id=media,
                dur_ms=play_ms,
                details={
                    **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
                    "sequence_index": index,
                    "phone_digits": digits,
                },
            )
            return False, moh_started
        playback_ids.append(playback_id)

        barrier_start = time.perf_counter()
        try:
            barrier_event = await client.wait_for_playback_finished(app_name, playback_id, timeout=barrier_timeout)
        except TimeoutError:
            barrier_event = {"type": "timeout"}
        except asyncio.TimeoutError:
            barrier_event = {"type": "timeout"}
        barrier_ms = int((time.perf_counter() - barrier_start) * 1000)
        barrier_total_ms += barrier_ms
        if barrier_event.get("type") != "PlaybackFinished":
            _log_latency_segment(
                session,
                "latency_playback_finished",
                latency_context,
                status="fail",
                reason=barrier_event.get("type") or "playback_event_missing",
                dur_ms=barrier_ms,
                details={
                    "playback_stage": DialogStage.PHONE_CONFIRM.value,
                    "playback_kind": "phone_confirm_fast_path",
                    "sequence_index": index,
                    "playback_id": playback_id,
                    "media": media,
                    "sound_id": media,
                },
            )
            session.log_event(
                action="phone_confirm_playback_barrier",
                status="fail",
                reason=barrier_event.get("type") or "playback_event_missing",
                media=media,
                sound_id=media,
                dur_ms=barrier_ms,
                details={
                    **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
                    "sequence_index": index,
                    "playback_id": playback_id,
                    "timeout_seconds": barrier_timeout,
                    "phone_digits": digits,
                },
            )
            return False, moh_started

        session.log_event(
            action="phone_confirm_fast_path_play",
            status="ok",
            media=media,
            sound_id=media,
            dur_ms=play_ms,
            details={
                **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
                "sequence_index": index,
                "playback_id": playback_id,
                "barrier_ms": barrier_ms,
                "phone_digits": digits,
            },
        )

    if guard_ms > 0:
        await asyncio.sleep(guard_ms / 1000)
    total_ms = int((time.perf_counter() - started) * 1000)
    _log_latency_segment(
        session,
        "latency_playback_finished",
        latency_context,
        dur_ms=barrier_total_ms,
        details={
            "playback_stage": DialogStage.PHONE_CONFIRM.value,
            "playback_kind": "phone_confirm_fast_path",
            "playback_ids": playback_ids,
            "media_sequence": media_sequence,
        },
    )
    session.log_event(
        action="phone_confirm_playback_barrier",
        status="ok",
        media=media_sequence[-1],
        sound_id=media_sequence[-1],
        dur_ms=barrier_total_ms,
        details={
            **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
            "playback_ids": playback_ids,
            "guard_delay_ms": guard_ms,
            "timeout_seconds": barrier_timeout,
            "phone_digits": digits,
            "fast_path": True,
        },
    )
    session.log_event(
        action="play_prompt",
        status="ok",
        media=media_sequence[0],
        sound_id=media_sequence[0],
        dur_ms=total_ms,
        details={
            "stage": DialogStage.PHONE_CONFIRM.value,
            "prompt_text": prompt_text,
            "dynamic": False,
            "fast_path": True,
            "phone_digits": digits,
            "media_sequence": media_sequence,
        },
    )
    return True, moh_started


async def _wait_for_name_playback_barrier(
    client: AriClient,
    app_name: str,
    session: CallSession,
    media: str,
    playback_id: str,
    prompt_text: str,
    *,
    dynamic: bool,
) -> bool:
    """Wait for NAME prompt playback to finish before recording can start."""
    if not playback_id:
        session.log_event(
            action="name_playback_barrier",
            status="fail",
            reason="playback_id_missing",
            media=media,
            sound_id=media,
            details={
                "stage": DialogStage.NAME.value,
                "prompt_text": prompt_text,
                "dynamic": dynamic,
            },
        )
        return False

    barrier_start = time.perf_counter()
    barrier_timeout = _name_playback_timeout_sec()
    try:
        barrier_event = await client.wait_for_playback_finished(app_name, playback_id, timeout=barrier_timeout)
    except TimeoutError:
        barrier_event = {"type": "timeout"}
    except asyncio.TimeoutError:
        barrier_event = {"type": "timeout"}
    barrier_ms = int((time.perf_counter() - barrier_start) * 1000)
    if barrier_event.get("type") != "PlaybackFinished":
        _log_latency_segment(
            session,
            "latency_playback_finished",
            None,
            status="fail",
            reason=barrier_event.get("type") or "playback_event_missing",
            dur_ms=barrier_ms,
            details={
                "stage": DialogStage.NAME.value,
                "playback_id": playback_id,
                "media": media,
                "sound_id": media,
                "dynamic": dynamic,
            },
        )
        session.log_event(
            action="name_playback_barrier",
            status="fail",
            reason=barrier_event.get("type") or "playback_event_missing",
            media=media,
            sound_id=media,
            dur_ms=barrier_ms,
            details={
                "stage": DialogStage.NAME.value,
                "playback_id": playback_id,
                "prompt_text": prompt_text,
                "dynamic": dynamic,
                "timeout_seconds": barrier_timeout,
            },
        )
        return False

    guard_ms = _name_guard_delay_ms()
    if guard_ms > 0:
        await asyncio.sleep(guard_ms / 1000)
    session.log_event(
        action="name_playback_barrier",
        status="ok",
        media=media,
        sound_id=media,
        dur_ms=barrier_ms,
        details={
            "stage": DialogStage.NAME.value,
            "playback_id": playback_id,
            "prompt_text": prompt_text,
            "dynamic": dynamic,
            "guard_delay_ms": guard_ms,
            "timeout_seconds": barrier_timeout,
        },
    )
    _log_latency_segment(
        session,
        "latency_playback_finished",
        None,
        dur_ms=barrier_ms,
        details={
            "stage": DialogStage.NAME.value,
            "playback_id": playback_id,
            "media": media,
            "sound_id": media,
            "dynamic": dynamic,
        },
    )
    return True


async def _wait_for_prompt_playback_barrier(
    client: AriClient,
    app_name: str,
    session: CallSession,
    stage: DialogStage,
    media: str,
    playback_id: str,
    prompt_text: str,
    *,
    dynamic: bool,
) -> bool:
    """Wait for prompt playback to finish before opening the caller microphone."""
    if stage == DialogStage.NAME:
        return await _wait_for_name_playback_barrier(
            client,
            app_name,
            session,
            media,
            playback_id,
            prompt_text,
            dynamic=dynamic,
        )
    action = "prompt_playback_barrier"
    if not playback_id:
        guard_ms = _stage_prompt_guard_delay_ms(stage)
        if guard_ms > 0:
            await asyncio.sleep(guard_ms / 1000)
        session.log_event(
            action=action,
            status="handled",
            reason="playback_id_missing",
            media=media,
            sound_id=media,
            details={"stage": stage.value, "prompt_text": prompt_text, "dynamic": dynamic, "guard_delay_ms": guard_ms},
        )
        return True

    barrier_start = time.perf_counter()
    barrier_timeout = _stage_prompt_playback_timeout_sec(stage)
    try:
        barrier_event = await client.wait_for_playback_finished(app_name, playback_id, timeout=barrier_timeout)
    except TimeoutError:
        barrier_event = {"type": "timeout"}
    except asyncio.TimeoutError:
        barrier_event = {"type": "timeout"}
    barrier_ms = int((time.perf_counter() - barrier_start) * 1000)
    if barrier_event.get("type") != "PlaybackFinished":
        _log_latency_segment(
            session,
            "latency_playback_finished",
            None,
            status="fail",
            reason=barrier_event.get("type") or "playback_event_missing",
            dur_ms=barrier_ms,
            details={
                "stage": stage.value,
                "playback_id": playback_id,
                "media": media,
                "sound_id": media,
                "dynamic": dynamic,
            },
        )
        session.log_event(
            action=action,
            status="fail",
            reason=barrier_event.get("type") or "playback_event_missing",
            media=media,
            sound_id=media,
            dur_ms=barrier_ms,
            details={
                "stage": stage.value,
                "playback_id": playback_id,
                "prompt_text": prompt_text,
                "dynamic": dynamic,
                "timeout_seconds": barrier_timeout,
            },
        )
        return False

    guard_ms = _stage_prompt_guard_delay_ms(stage)
    if guard_ms > 0:
        await asyncio.sleep(guard_ms / 1000)
    session.log_event(
        action=action,
        status="ok",
        media=media,
        sound_id=media,
        dur_ms=barrier_ms,
        details={
            "stage": stage.value,
            "playback_id": playback_id,
            "prompt_text": prompt_text,
            "dynamic": dynamic,
            "guard_delay_ms": guard_ms,
            "timeout_seconds": barrier_timeout,
        },
    )
    _log_latency_segment(
        session,
        "latency_playback_finished",
        None,
        dur_ms=barrier_ms,
        details={
            "stage": stage.value,
            "playback_id": playback_id,
            "media": media,
            "sound_id": media,
            "dynamic": dynamic,
        },
    )
    return True


async def _play_dynamic_prompt(
    client: AriClient,
    settings: Settings,
    app_name: str,
    session: CallSession,
    stage: DialogStage,
    prompt_text: str,
    moh_started: bool,
    latency_context: dict[str, Any] | None = None,
) -> tuple[bool, bool]:
    started = time.perf_counter()
    safe_stage = stage.value.lower()
    prompt_path = session.artifact_dir / f"{safe_stage}_retry_prompt.wav"
    tts_start = time.perf_counter()
    try:
        tts = SileroTTS()
        wav = await asyncio.to_thread(tts.synthesize, prompt_text)
        save_bytes(prompt_path, wav)
    except Exception as exc:
        session.log_event(
            action="dynamic_prompt_tts",
            status="fail",
            reason=repr(exc),
            dur_ms=int((time.perf_counter() - tts_start) * 1000),
            details={"stage": stage.value, "prompt_text": prompt_text},
        )
        return False, moh_started
    session.log_event(
        action="dynamic_prompt_tts",
        status="ok",
        dur_ms=int((time.perf_counter() - tts_start) * 1000),
        details={"stage": stage.value, "prompt_text": prompt_text},
    )
    _log_latency_segment(
        session,
        "latency_tts_done",
        latency_context,
        dur_ms=int((time.perf_counter() - tts_start) * 1000),
        details={"playback_stage": stage.value, "prompt_text": prompt_text},
    )

    remote_rel_path = f"{settings.asterisk_sounds_subdir}/{session.call_id}/{safe_stage}_retry_prompt.wav"
    publish_start = time.perf_counter()
    publish_timeout_sec = _publish_total_timeout_sec()
    publish_cmd_timeout_sec = _env_int("PUBLISH_CMD_TIMEOUT_SEC", 15)
    try:
        publish_result = await asyncio.wait_for(
            asyncio.to_thread(
                publish_wav_to_asterisk,
                prompt_path,
                remote_rel_path,
                settings,
                cmd_timeout_sec=publish_cmd_timeout_sec,
            ),
            timeout=publish_timeout_sec,
        )
    except asyncio.TimeoutError:
        session.log_event(
            action="dynamic_prompt_publish",
            status="fail",
            reason="publish_timeout",
            dur_ms=int((time.perf_counter() - publish_start) * 1000),
            details={"stage": stage.value, "prompt_text": prompt_text, "remote_rel_path": remote_rel_path},
        )
        return False, moh_started

    publish_ms = int((time.perf_counter() - publish_start) * 1000)
    if not publish_result.get("ok"):
        session.log_event(
            action="dynamic_prompt_publish",
            status="fail",
            reason=_publish_result_reason(publish_result),
            dur_ms=publish_ms,
            details={"stage": stage.value, "prompt_text": prompt_text, "publish_result": publish_result},
        )
        return False, moh_started
    media = str(publish_result.get("sound_id"))
    session.log_event(
        action="dynamic_prompt_publish",
        status="ok",
        sound_id=media,
        remote_path=str(publish_result.get("remote_path") or ""),
        dur_ms=publish_ms,
        details={"stage": stage.value, "prompt_text": prompt_text},
    )
    _log_latency_segment(
        session,
        "latency_publish_done",
        latency_context,
        dur_ms=publish_ms,
        details={
            "playback_stage": stage.value,
            "sound_id": media,
            "remote_path": str(publish_result.get("remote_path") or ""),
        },
    )

    moh_started = await _maybe_stop_moh(client, session, moh_started)
    _log_latency_playback_started(
        session,
        latency_context,
        playback_stage=stage,
        media=media,
        sound_id=media,
        prompt_text=prompt_text,
        dynamic=True,
    )
    result = await client.play_safe(session.channel_id, media)
    if result["ok"]:
        if _requires_prompt_playback_barrier(stage):
            playback_id = _playback_id_from_result(result)
            if not await _wait_for_prompt_playback_barrier(
                client,
                app_name,
                session,
                stage,
                media,
                playback_id,
                prompt_text,
                dynamic=True,
            ):
                return False, moh_started
        dur_ms = int((time.perf_counter() - started) * 1000)
        session.log_event(
            action="play_prompt",
            status="ok",
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details={"stage": stage.value, "prompt_text": prompt_text, "dynamic": True},
        )
        return True, moh_started

    dur_ms = int((time.perf_counter() - started) * 1000)
    session.log_event(
        action="play_prompt",
        status="fail",
        reason=result.get("reason"),
        http_status=result.get("http_status"),
        media=media,
        sound_id=media,
        dur_ms=dur_ms,
        details={"stage": stage.value, "prompt_text": prompt_text, "dynamic": True, **(result.get("details") or {})},
    )
    return False, moh_started


async def _play_phone_confirm_holding_prompt(
    client: AriClient,
    app_name: str,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
    latency_context: dict[str, Any] | None,
) -> tuple[bool, bool]:
    if not _phone_confirm_holding_enabled():
        session.log_event(
            action="phone_confirm_holding_prompt",
            status="skipped",
            reason="disabled",
            details=_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
        )
        return False, moh_started
    if not system_sounds.get(PHONE_CONFIRM_HOLDING_SOUND_ID, False):
        session.log_event(
            action="phone_confirm_holding_prompt",
            status="skipped",
            reason="static_media_unavailable",
            sound_id=PHONE_CONFIRM_HOLDING_SOUND_ID,
            details=_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
        )
        return False, moh_started

    media = PHONE_CONFIRM_HOLDING_SOUND_ID
    started = time.perf_counter()
    moh_started = await _maybe_stop_moh(client, session, moh_started)
    _log_latency_playback_started(
        session,
        latency_context,
        playback_stage=DialogStage.PHONE_CONFIRM,
        media=media,
        sound_id=media,
        prompt_text=PHONE_CONFIRM_HOLDING_PHRASE,
        dynamic=False,
        playback_kind="holding",
    )
    result = await client.play_safe(session.channel_id, media)
    playback_id = _playback_id_from_result(result)
    play_ms = int((time.perf_counter() - started) * 1000)
    if not result["ok"]:
        session.log_event(
            action="phone_confirm_holding_prompt",
            status="fail",
            reason=result.get("reason"),
            http_status=result.get("http_status"),
            media=media,
            sound_id=media,
            dur_ms=play_ms,
            details={
                **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
                **(result.get("details") or {}),
                "prompt_text": PHONE_CONFIRM_HOLDING_PHRASE,
                "bounded": True,
            },
        )
        return False, moh_started

    barrier_ok = False
    barrier_ms: int | None = None
    barrier_timeout = _phone_confirm_holding_playback_timeout_sec()
    if playback_id:
        barrier_start = time.perf_counter()
        try:
            barrier_event = await client.wait_for_playback_finished(app_name, playback_id, timeout=barrier_timeout)
        except TimeoutError:
            barrier_event = {"type": "timeout"}
        except asyncio.TimeoutError:
            barrier_event = {"type": "timeout"}
        barrier_ms = int((time.perf_counter() - barrier_start) * 1000)
        barrier_ok = barrier_event.get("type") == "PlaybackFinished"

    session.log_event(
        action="phone_confirm_holding_prompt",
        status="ok" if barrier_ok else "handled",
        reason=None if barrier_ok else "playback_barrier_missing_or_timeout",
        media=media,
        sound_id=media,
        dur_ms=play_ms,
        details={
            **_latency_context_details(latency_context, playback_stage=DialogStage.PHONE_CONFIRM),
            "prompt_text": PHONE_CONFIRM_HOLDING_PHRASE,
            "bounded": True,
            "playback_id": playback_id,
            "timeout_seconds": barrier_timeout,
            "barrier_completed": barrier_ok,
            "barrier_ms": barrier_ms,
        },
    )
    _log_latency_segment(
        session,
        "latency_playback_finished",
        latency_context,
        status="ok" if barrier_ok else "handled",
        reason=None if barrier_ok else "playback_barrier_missing_or_timeout",
        dur_ms=barrier_ms,
        details={
            "stage": DialogStage.PHONE.value,
            "playback_stage": DialogStage.PHONE_CONFIRM.value,
            "playback_kind": "holding",
            "playback_id": playback_id,
            "media": media,
            "sound_id": media,
            "bounded": True,
        },
    )
    return True, moh_started


async def _play_prompt(
    client: AriClient,
    settings: Settings,
    app_name: str,
    session: CallSession,
    stage: DialogStage,
    system_sounds: dict[str, bool],
    moh_started: bool,
    latency_context: dict[str, Any] | None = None,
) -> tuple[bool, bool]:
    if stage == DialogStage.PHONE_CONFIRM:
        return await _play_phone_confirmation_prompt(client, settings, app_name, session, moh_started, latency_context)

    prompt_text = next_prompt(stage, session.dialog.profile)
    media = _static_retry_prompt_media(stage, prompt_text, system_sounds)
    if prompt_text != PROMPTS.get(stage) and media is None:
        return await _play_dynamic_prompt(
            client,
            settings,
            app_name,
            session,
            stage,
            prompt_text,
            moh_started,
            latency_context,
        )

    if media is None:
        media = _prompt_media_for_stage(stage, system_sounds)
    started = time.perf_counter()
    moh_started = await _maybe_stop_moh(client, session, moh_started)
    _log_latency_playback_started(
        session,
        latency_context,
        playback_stage=stage,
        media=media,
        sound_id=media,
        prompt_text=prompt_text,
        dynamic=False,
    )
    result = await client.play_safe(session.channel_id, media)

    if result["ok"]:
        if _requires_prompt_playback_barrier(stage):
            playback_id = _playback_id_from_result(result)
            if not await _wait_for_prompt_playback_barrier(
                client,
                app_name,
                session,
                stage,
                media,
                playback_id,
                prompt_text,
                dynamic=False,
            ):
                return False, moh_started
        dur_ms = int((time.perf_counter() - started) * 1000)
        session.log_event(
            action="play_prompt",
            status="ok",
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details={"stage": stage.value, "prompt_text": prompt_text, "dynamic": False},
        )
        return True, moh_started

    dur_ms = int((time.perf_counter() - started) * 1000)
    session.log_event(
        action="play_prompt",
        status="fail",
        reason=result.get("reason"),
        http_status=result.get("http_status"),
        media=media,
        sound_id=media,
        dur_ms=dur_ms,
        details=result.get("details"),
    )
    if result.get("reason") == "channel_gone":
        session.transition(CallState.DONE, action="channel_gone", status="ok")
        return False, moh_started

    moh_started = await _maybe_start_moh(client, session, moh_started, action="moh_start_after_prompt_fail")
    _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
    # Continue dialog even after prompt failure/fallback attempt to avoid immediate silent drop.
    return True, moh_started


def _append_turn(artifact_dir: Path, payload: dict[str, Any]) -> None:
    turns_path = artifact_dir / "turns.jsonl"
    with turns_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _save_profile(artifact_dir: Path, profile: dict[str, Any]) -> None:
    save_json(artifact_dir / "profile.json", profile)


def _is_successful_phone_capture(
    previous_stage: DialogStage,
    next_stage: DialogStage,
    profile: dict[str, Any],
) -> bool:
    return (
        previous_stage == DialogStage.PHONE_CONFIRM
        and next_stage == DialogStage.DONE
        and bool(profile.get("phone_digits"))
        and profile.get("phone_confirmed") is True
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


async def _download_transcription_artifact(
    client: AriClient,
    session: CallSession,
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
    dest_path: Path,
    *,
    early_stop_completion: bool = False,
) -> TranscriptionArtifact:
    if dest_path.exists():
        dest_path.unlink()
        session.log_event(
            action="discard_stale_audio_artifact",
            status="ok",
            details={
                "stage": stage.value,
                "turn_idx": turn_idx,
                "record_name": record_name,
                "audio_path": str(dest_path.as_posix()),
            },
        )

    download_start = time.perf_counter()
    retry_count = _early_stop_download_retry_count() if early_stop_completion else 0
    attempt = 0
    while True:
        try:
            await client.download_recording(record_name, dest_path.as_posix())
            break
        except Exception as exc:
            if not early_stop_completion or attempt >= retry_count:
                if early_stop_completion:
                    session.log_event(
                        action="recording_download_unavailable_after_early_stop",
                        status="handled",
                        reason=repr(exc),
                        details={
                            "stage": stage.value,
                            "turn_idx": turn_idx,
                            "record_name": record_name,
                            "attempt": attempt + 1,
                            "retry_count": retry_count,
                        },
                    )
                raise
            attempt += 1
            delay_ms = _early_stop_download_retry_base_ms() * attempt
            session.log_event(
                action="recording_download_retry",
                status="retry",
                reason=repr(exc),
                details={
                    "stage": stage.value,
                    "turn_idx": turn_idx,
                    "record_name": record_name,
                    "attempt": attempt,
                    "retry_count": retry_count,
                    "delay_ms": delay_ms,
                },
            )
            await asyncio.sleep(delay_ms / 1000)
    if attempt:
        session.log_event(
            action="recording_download_ready_after_retry",
            status="ok",
            dur_ms=int((time.perf_counter() - download_start) * 1000),
            details={
                "stage": stage.value,
                "turn_idx": turn_idx,
                "record_name": record_name,
                "attempt": attempt + 1,
                "retry_count": retry_count,
            },
        )
    if not dest_path.exists():
        raise FileNotFoundError(f"recording download did not create {dest_path}")
    size_bytes = dest_path.stat().st_size
    if size_bytes <= 0:
        raise ValueError(f"recording download is empty: {dest_path}")

    artifact = TranscriptionArtifact(
        call_id=session.call_id,
        channel_id=session.channel_id,
        stage=stage,
        turn_idx=turn_idx,
        record_name=record_name,
        path=dest_path,
        size_bytes=size_bytes,
        sha256=_file_sha256(dest_path),
    )
    session.log_event(
        action="download_recording",
        status="ok",
        dur_ms=int((time.perf_counter() - download_start) * 1000),
        details=artifact.details(),
    )
    return artifact


def _transcribe_audio_artifact(_settings: Settings, artifact: TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
    """Transcribe the artifact without fabricating speech when no STT backend is configured."""
    backend = os.getenv("TELEPHONY_STT_BACKEND", "").strip().lower()
    details = artifact.details()
    details["stt_backend"] = backend or "none"

    if backend in {"", "none", "disabled"}:
        details["reason"] = "stt_backend_not_configured"
        return "", details

    if backend == "fixture":
        fixture_env = f"TELEPHONY_STT_FIXTURE_{artifact.stage.value}"
        details["fixture_env"] = fixture_env
        return os.getenv(fixture_env, "").strip(), details

    if backend in {"openai", "whisper", "whisper_api"}:
        model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1").strip() or "whisper-1"
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        if artifact.stage == DialogStage.NAME:
            language = NAME_STT_LANGUAGE
            prompt = NAME_STT_PROMPT
        elif artifact.stage == DialogStage.CITY:
            language = CITY_STT_LANGUAGE
            prompt = CITY_STT_PROMPT
        else:
            language = None
            prompt = None
        try:
            audio_bytes = artifact.path.read_bytes()
            client = WhisperAPIClient(api_key=_settings.openai_api_key, model=model, base_url=base_url)
            text = client.transcribe(
                audio_bytes,
                filename=artifact.path.name,
                language=language,
                prompt=prompt,
            )
        except Exception as exc:
            details["reason"] = "stt_transcribe_failed"
            details["error"] = repr(exc)
            return "", details
        details["stt_model"] = model
        if language:
            details["stt_language"] = language
        if prompt:
            details["stt_prompt"] = prompt
        return text, details

    details["reason"] = "unsupported_stt_backend"
    return "", details


def _streaming_stt_enabled() -> bool:
    return os.getenv("STT_STREAMING_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _streaming_stt_fallback_enabled() -> bool:
    return os.getenv("STT_STREAMING_FALLBACK_TO_BATCH", "true").strip().lower() in {"1", "true", "yes", "on"}


def _streaming_stt_config(settings: Settings) -> RealtimeTranscriptionConfig:
    default_base_url = "wss://api.openai.com/v1/realtime"
    return RealtimeTranscriptionConfig(
        api_key=settings.openai_api_key,
        transcription_model=(
            os.getenv("STT_STREAMING_MODEL", "gpt-realtime-whisper").strip() or "gpt-realtime-whisper"
        ),
        session_model=os.getenv("STT_STREAMING_SESSION_MODEL", "gpt-realtime").strip() or "gpt-realtime",
        language=os.getenv("STT_STREAMING_LANGUAGE", "ru").strip() or "ru",
        sample_rate=_env_int("STT_STREAMING_SAMPLE_RATE", 24000),
        chunk_ms=_env_int("STT_STREAMING_CHUNK_MS", 200),
        base_url=os.getenv("STT_STREAMING_BASE_URL", default_base_url).strip() or default_base_url,
        timeout_seconds=float(os.getenv("STT_STREAMING_TIMEOUT_SECONDS", "30") or "30"),
        api_mode=os.getenv("STT_STREAMING_OPENAI_API_MODE", "ga").strip().lower() or "ga",
    )


async def _transcribe_audio_artifact_experimental(
    settings: Settings,
    session: CallSession,
    artifact: TranscriptionArtifact,
    live_result: LiveStreamingProofResult | None = None,
    *,
    recording_finished_at: float | None = None,
) -> tuple[str, dict[str, Any]]:
    """Use the feature-flagged streaming STT spike path or the existing batch path."""
    live_config = live_streaming_config()
    if live_result is not None:
        baseline_start = time.perf_counter()
        batch_text, batch_details = await asyncio.to_thread(_transcribe_audio_artifact, settings, artifact)
        batch_latency_ms = int((time.perf_counter() - baseline_start) * 1000)
        live_vs_batch_delta_ms = (
            live_result.recording_finish_to_final_ms - batch_latency_ms
            if live_result.recording_finish_to_final_ms is not None
            else None
        )
        live_details = {
            **batch_details,
            **live_result.details(),
            "stt_live_streaming_enabled": True,
            "stt_live_streaming_use_live_transcript": live_config.use_live_transcript,
            "stt_batch_baseline_latency_ms": batch_latency_ms,
            "stt_live_vs_batch_delta_ms": live_vs_batch_delta_ms,
        }
        session.log_event(
            action="stt_batch_baseline_latency_ms",
            status="ok",
            dur_ms=batch_latency_ms,
            details={**artifact.details(), "recording_finished_at": recording_finished_at},
        )
        session.log_event(
            action="stt_live_vs_batch_delta_ms",
            status="ok",
            dur_ms=live_vs_batch_delta_ms,
            details=live_details,
        )
        if live_config.use_live_transcript and live_result.text.strip():
            live_details["stt_backend"] = "live_streaming"
            return live_result.text, live_details
        live_details["stt_live_stream_fallback_to_batch"] = True
        session.log_event(
            action="stt_live_stream_fallback_to_batch",
            status="handled",
            reason="live_transcript_not_used_for_dialog",
            details=live_details,
        )
        return batch_text, live_details

    if not _streaming_stt_enabled():
        baseline_start = time.perf_counter()
        text, details = await asyncio.to_thread(_transcribe_audio_artifact, settings, artifact)
        details["stt_streaming_enabled"] = False
        details["stt_batch_baseline_latency_ms"] = int((time.perf_counter() - baseline_start) * 1000)
        return text, details

    provider = os.getenv("STT_STREAMING_PROVIDER", "openai_realtime_whisper").strip().lower()
    base_details = {
        **artifact.details(),
        "stt_streaming_enabled": True,
        "stt_stream_provider": provider,
    }
    if provider != "openai_realtime_whisper":
        session.log_event(
            action="stt_stream_error",
            status="handled",
            reason="unsupported_streaming_provider",
            details=base_details,
        )
        if not _streaming_stt_fallback_enabled():
            return "", {**base_details, "reason": "unsupported_streaming_provider"}
        return await _fallback_to_batch_stt(settings, session, artifact, base_details, "unsupported_streaming_provider")

    def log_stream_metric(action: str, details: dict[str, Any]) -> None:
        status = "ok"
        if action == "stt_stream_audio_chunk_sent":
            status = "sent"
        session.log_event(action=action, status=status, details={**base_details, **details})

    try:
        config = _streaming_stt_config(settings)
        adapter = RealtimeWhisperAdapter(config)
        result = await adapter.transcribe_wav_file(artifact.path, on_metric=log_stream_metric)
    except Exception as exc:
        error_details = {**base_details, "reason": "stt_stream_error", "error": repr(exc)}
        session.log_event(action="stt_stream_error", status="handled", reason="stt_stream_error", details=error_details)
        if not _streaming_stt_fallback_enabled():
            return "", error_details
        return await _fallback_to_batch_stt(settings, session, artifact, error_details, "stt_stream_error")

    details = {
        **base_details,
        **result.details(),
        "stt_backend": "streaming",
        "stt_model": result.model,
        "stt_language": result.language,
    }
    return result.text, details


async def _fallback_to_batch_stt(
    settings: Settings,
    session: CallSession,
    artifact: TranscriptionArtifact,
    details: dict[str, Any],
    reason: str,
) -> tuple[str, dict[str, Any]]:
    session.log_event(action="stt_stream_fallback_to_batch", status="handled", reason=reason, details=details)
    baseline_start = time.perf_counter()
    text, batch_details = await asyncio.to_thread(_transcribe_audio_artifact, settings, artifact)
    batch_latency_ms = int((time.perf_counter() - baseline_start) * 1000)
    return text, {
        **batch_details,
        "stt_streaming_enabled": True,
        "stt_stream_fallback_to_batch": True,
        "stt_stream_error_reason": reason,
        "stt_batch_baseline_latency_ms": batch_latency_ms,
    }


async def _start_live_streaming_probe(
    settings: Settings,
    client: AriClient,
    app_name: str,
    session: CallSession,
    *,
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
    record_started_at: float,
    recording_finished_at: Callable[[], float | None],
) -> LiveStreamingProofHandle | None:
    config = live_streaming_config()
    base_details = {
        "stage": stage.value,
        "turn_idx": turn_idx,
        "record_name": record_name,
        "stt_live_streaming_enabled": config.enabled,
        "stt_live_streaming_provider": config.provider,
        "stt_live_streaming_model": config.model,
        "stt_live_streaming_stage_allowlist": sorted(config.stage_allowlist),
        "live_media_topology": config.topology,
    }
    if is_live_external_media_channel(session.channel_id):
        session.log_event(
            action="stt_live_stream_probe_failed",
            status="skipped",
            reason="external_media_channel_excluded",
            details=base_details,
        )
        return None
    if not config.enabled:
        return None
    if not live_streaming_stage_allowed(stage, config):
        reason = "stage_not_allowlisted"
        if stage == DialogStage.PHONE_CONFIRM:
            reason = "phone_confirm_not_in_default_live_allowlist"
        session.log_event(
            action="stt_live_stream_probe_failed",
            status="skipped",
            reason=reason,
            details=base_details,
        )
        return None

    def log_metric(action: str, details: dict[str, Any], status: str, reason: str | None) -> None:
        session.log_event(action=action, status=status, reason=reason, details={**base_details, **details})

    try:
        return await start_live_streaming_proof(
            settings=settings,
            client=client,
            app_name=app_name,
            call_id=session.call_id,
            channel_id=session.channel_id,
            stage=stage,
            turn_idx=turn_idx,
            record_name=record_name,
            record_started_at=record_started_at,
            recording_finished_at=recording_finished_at,
            log_metric=log_metric,
            config=config,
        )
    except Exception as exc:
        reason = exc.reason if isinstance(exc, LiveStreamingProofError) else "stt_live_stream_error"
        session.log_event(
            action="stt_live_stream_probe_failed",
            status="handled",
            reason=reason,
            details={**base_details, "error": repr(exc)},
        )
        session.log_event(
            action="stt_live_stream_error",
            status="handled",
            reason=reason,
            details={**base_details, "error": repr(exc)},
        )
        session.log_event(
            action="stt_live_stream_fallback_to_batch",
            status="ok",
            reason="live_streaming_setup_failed" if reason != "openai_api_key_missing_or_invalid" else reason,
            details={**base_details, "error": repr(exc)},
        )
        return None


async def _finish_live_streaming_probe_task(
    handle: LiveStreamingProofHandle | None,
    session: CallSession,
    *,
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
) -> LiveStreamingProofResult | None:
    if handle is None:
        return None
    task = handle.task
    try:
        return await task
    except asyncio.CancelledError:
        return None
    except Exception as exc:
        session.log_event(
            action="stt_live_stream_fallback_to_batch",
            status="handled",
            reason="stt_live_stream_error",
            details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name, "error": repr(exc)},
        )
        return None


async def _cancel_live_streaming_probe_task(handle: LiveStreamingProofHandle | None) -> None:
    if handle is None or handle.task.done():
        return
    task = handle.task
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def handle_call(
    client: AriClient,
    settings: Settings,
    app_name: str,
    session: CallSession,
    moh_started: bool = False,
) -> None:
    call_id = session.call_id
    channel_id = session.channel_id
    if is_live_external_media_channel(channel_id):
        session.log_event(
            action="stt_live_external_media_channel_ignored",
            status="skipped",
            reason="external_media_channel_excluded",
            details={"channel_id": channel_id},
        )
        print("STASIS_EXTERNAL_MEDIA_IGNORED", channel_id)
        return
    play_test = os.getenv("PLAY_TEST", "0") == "1"
    record_max_duration_seconds = _env_int("RECORD_MAX_DURATION_SECONDS", 6)
    record_max_silence_seconds = _env_int("RECORD_MAX_SILENCE_SECONDS", 2)
    record_beep = os.getenv("RECORD_BEEP", "0").strip().lower() in {"1", "true", "yes", "on"}

    try:
        session.transition(CallState.ASKING, action="call_flow_started", status="ok")
        system_sounds = _system_sounds_snapshot()

        if play_test:
            play_test_media = "sound:demo-congrats"
            print("PLAY_TEST_START", call_id, play_test_media)
            play_result = await client.play_safe(channel_id, play_test_media)
            if play_result["ok"]:
                print("PLAY_TEST_OK", call_id, play_test_media)
                session.log_event(action="play_test", status="ok", media=play_test_media)
            else:
                print("PLAY_TEST_FAIL", call_id, play_result.get("reason"))
                session.log_event(
                    action="play_test",
                    status="fail",
                    reason=play_result.get("reason"),
                    http_status=play_result.get("http_status"),
                    media=play_test_media,
                    details=play_result.get("details"),
                )
        else:
            print("PLAY_TEST_DISABLED", call_id)
            session.log_event(action="play_test_disabled", status="ok")

        artifact_dir = session.artifact_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)

        if settings.demo_mode == "synth":
            session.transition(CallState.RECORDING, action="record_start", status="start")
            record_name = f"{call_id}_utt1"
            record_start = time.perf_counter()
            record_result = await client.record_safe(
                channel_id,
                record_name,
                max_duration_seconds=record_max_duration_seconds,
                max_silence_seconds=record_max_silence_seconds,
                beep=record_beep,
            )
            if not record_result["ok"]:
                session.transition(
                    CallState.FAILED,
                    action="record_start",
                    status="fail",
                    reason=record_result.get("reason"),
                    http_status=record_result.get("http_status"),
                    details=record_result.get("details"),
                )
                return

            event = await client.wait_for_recording_finished(app_name, record_name, timeout=30)
            dur_ms = int((time.perf_counter() - record_start) * 1000)
            if event.get("type") != "RecordingFinished":
                reason = event.get("type") or "recording_event_missing"
                session.transition(CallState.FAILED, action="record_wait", status="fail", reason=reason, dur_ms=dur_ms)
                return
            session.log_event(action="record_done", status="ok", dur_ms=dur_ms)

            input_path = artifact_dir / "input.wav"
            await client.download_recording(record_name, input_path.as_posix())
            session.log_event(action="download_recording", status="ok")
            transcript_for_pipeline = ""
            profile_for_pipeline: dict[str, Any] = {}
        else:
            dialogue_lines: list[str] = []
            max_turns = 8
            pending_latency_context: dict[str, Any] | None = None
            while not should_stop_dialog(session.dialog.stage, session.dialog.turns_done, max_turns):
                turn_idx = session.dialog.turns_done + 1
                stage = session.dialog.stage
                stage_enter_perf = time.perf_counter()
                stage_enter_ts = _now_iso()
                session.log_event(
                    action="latency_stage_enter",
                    status="start",
                    details={
                        "stage": stage.value,
                        "turn_idx": turn_idx,
                        "stage_enter_ts": stage_enter_ts,
                    },
                )
                should_continue, moh_started = await _play_prompt(
                    client,
                    settings,
                    app_name,
                    session,
                    stage,
                    system_sounds,
                    moh_started,
                    pending_latency_context,
                )
                pending_latency_context = None
                if not should_continue:
                    return
                moh_started = await _maybe_stop_moh(client, session, moh_started)

                record_profile = _record_profile_for_stage(stage)
                early_stop_policy = _recording_early_stop_policy_for_stage(stage, session.dialog.profile)
                if stage == DialogStage.CITY and early_stop_policy.reason == "city_retry_conservative_talk_detect":
                    session.log_event(
                        action="city_retry_conservative_talk_detect_used",
                        status="ok",
                        details={
                            "stage": stage.value,
                            "turn_idx": turn_idx,
                            "policy": early_stop_policy.details(),
                            "reason": session.dialog.profile.get("city_retry_reliable_mode_reason"),
                        },
                    )
                talk_detect_enabled = await _maybe_enable_talk_detect(
                    client,
                    session,
                    stage,
                    turn_idx,
                    early_stop_policy,
                )
                record_name = f"{call_id}_{stage.value.lower()}_utt{turn_idx}"
                event_subscription = await _open_recording_event_subscription(
                    client,
                    app_name,
                    session,
                    stage=stage,
                    turn_idx=turn_idx,
                    record_name=record_name,
                    policy=early_stop_policy,
                    talk_detect_enabled=talk_detect_enabled,
                )
                record_start = time.perf_counter()
                record_end_perf: float | None = None
                live_stream_task = await _start_live_streaming_probe(
                    settings,
                    client,
                    app_name,
                    session,
                    stage=stage,
                    turn_idx=turn_idx,
                    record_name=record_name,
                    record_started_at=record_start,
                    recording_finished_at=lambda: record_end_perf,
                )
                session.transition(
                    CallState.RECORDING,
                    action="record_start",
                    status="start",
                    details={
                        "stage": stage.value,
                        "turn_idx": turn_idx,
                        **record_profile.details(),
                    },
                )
                record_result = await client.record_safe(
                    channel_id,
                    record_name,
                    max_duration_seconds=record_profile.max_duration_seconds,
                    max_silence_seconds=record_profile.max_silence_seconds,
                    beep=record_beep,
                )
                if not record_result["ok"]:
                    await _cancel_live_streaming_probe_task(live_stream_task)
                    if event_subscription is not None:
                        event_subscription.close()
                    if record_result.get("reason") == "channel_gone":
                        session.transition(CallState.DONE, action="channel_gone", status="ok")
                        return
                    session.transition(
                        CallState.FAILED,
                        action="record_start",
                        status="fail",
                        reason=record_result.get("reason"),
                        http_status=record_result.get("http_status"),
                        details=record_result.get("details"),
                    )
                    return

                try:
                    event = await _wait_for_recording_with_optional_early_stop(
                        client,
                        app_name,
                        session,
                        record_name=record_name,
                        stage=stage,
                        turn_idx=turn_idx,
                        timeout=record_profile.wait_timeout_seconds,
                        policy=early_stop_policy,
                        talk_detect_enabled=talk_detect_enabled,
                        record_start=record_start,
                        event_subscription=event_subscription,
                    )
                except TimeoutError:
                    event = {"type": "timeout"}
                except asyncio.TimeoutError:
                    event = {"type": "timeout"}
                record_end_perf = time.perf_counter()
                dur_ms = int((record_end_perf - record_start) * 1000)
                recording_completion_source = event.get("recording_completion_source")
                if event.get("type") == "RecordingFinished" and not recording_completion_source:
                    recording_completion_source = "normal_record_done"
                transcript_text = ""
                transcript_details: dict[str, Any]
                stt_ms = 0
                if event.get("type") != "RecordingFinished":
                    await _cancel_live_streaming_probe_task(live_stream_task)
                    reason = event.get("type") or "recording_event_missing"
                    session.log_event(
                        action="record_wait",
                        status="handled",
                        reason=reason,
                        dur_ms=dur_ms,
                        details={
                            "stage": stage.value,
                            "turn_idx": turn_idx,
                            "record_name": record_name,
                            "normal_stage_outcome": True,
                            **record_profile.details(),
                        },
                    )
                    if (
                        stage == DialogStage.CITY
                        and reason == "timeout"
                        and session.dialog.profile.get("city_retry_reliable_mode")
                    ):
                        session.log_event(
                            action="city_retry_record_timeout",
                            status="handled",
                            reason=reason,
                            dur_ms=dur_ms,
                            details={
                                "stage": stage.value,
                                "turn_idx": turn_idx,
                                "record_name": record_name,
                                "retry_reason": session.dialog.profile.get("city_retry_reliable_mode_reason"),
                                **record_profile.details(),
                            },
                        )
                    transcript_details = {
                        "stage": stage.value,
                        "turn_idx": turn_idx,
                        "record_name": record_name,
                        "reason": reason,
                        "normal_stage_outcome": True,
                    }
                else:
                    session.log_event(
                        action="record_done",
                        status="ok",
                        dur_ms=dur_ms,
                        details={
                            "stage": stage.value,
                            "turn_idx": turn_idx,
                            "record_name": record_name,
                            "recording_completion_source": recording_completion_source,
                            "recording_early_stop_used": event.get("recording_early_stop_used") is True,
                            **record_profile.details(),
                        },
                    )
                    session.log_event(
                        action="recording_completion_source",
                        status="ok",
                        reason=recording_completion_source,
                        dur_ms=dur_ms,
                        details={
                            "stage": stage.value,
                            "turn_idx": turn_idx,
                            "record_name": record_name,
                            "recording_early_stop_used": event.get("recording_early_stop_used") is True,
                        },
                    )

                    turn_audio = artifact_dir / f"turn_{turn_idx}.wav"
                    try:
                        artifact = await _download_transcription_artifact(
                            client,
                            session,
                            stage,
                            turn_idx,
                            record_name,
                            turn_audio,
                            early_stop_completion=event.get("recording_completion_source") == "talk_detect_early_stop",
                        )
                    except Exception as exc:
                        await _cancel_live_streaming_probe_task(live_stream_task)
                        session.log_event(
                            action="download_recording",
                            status="handled",
                            reason=repr(exc),
                            details={
                                "stage": stage.value,
                                "turn_idx": turn_idx,
                                "record_name": record_name,
                                "normal_stage_outcome": True,
                            },
                        )
                        transcript_details = {
                            "stage": stage.value,
                            "turn_idx": turn_idx,
                            "record_name": record_name,
                            "reason": "recording_download_unavailable",
                            "normal_stage_outcome": True,
                        }
                    else:
                        stt_start = time.perf_counter()
                        city_min_audio_bytes = _city_early_stop_min_audio_bytes()
                        if (
                            stage == DialogStage.CITY
                            and event.get("recording_early_stop_used") is True
                            and artifact.size_bytes < city_min_audio_bytes
                        ):
                            await _cancel_live_streaming_probe_task(live_stream_task)
                            transcript_text = ""
                            transcript_details = {
                                **artifact.details(),
                                "reason": "early_stopped_audio_too_tiny",
                                "min_audio_bytes": city_min_audio_bytes,
                                "normal_stage_outcome": True,
                            }
                            session.dialog.profile["city_retry_reliable_mode"] = True
                            session.dialog.profile["city_retry_reliable_mode_reason"] = "early_stopped_audio_too_tiny"
                            session.log_event(
                                action="city_retry_conservative_talk_detect_selected",
                                status="ok",
                                reason="early_stopped_audio_too_tiny",
                                details={
                                    **transcript_details,
                                    "current_stage": stage.value,
                                    "next_stage": DialogStage.CITY.value,
                                },
                            )
                            session.log_event(
                                action="recording_early_stop_audio_sanity",
                                status="handled",
                                reason="early_stopped_audio_too_tiny",
                                details=transcript_details,
                            )
                        else:
                            live_result = await _finish_live_streaming_probe_task(
                                live_stream_task,
                                session,
                                stage=stage,
                                turn_idx=turn_idx,
                                record_name=record_name,
                            )
                            transcript_text, transcript_details = await _transcribe_audio_artifact_experimental(
                                settings,
                                session,
                                artifact,
                                live_result,
                                recording_finished_at=record_end_perf,
                            )
                            stt_ms = int((time.perf_counter() - stt_start) * 1000)
                            phone_confirm_min_audio_bytes = _phone_confirm_early_stop_min_audio_bytes()
                            if (
                                stage == DialogStage.PHONE_CONFIRM
                                and event.get("recording_early_stop_used") is True
                                and artifact.size_bytes < phone_confirm_min_audio_bytes
                                and not transcript_text.strip()
                            ):
                                transcript_details = {
                                    **transcript_details,
                                    "reason": "phone_confirm_early_stopped_audio_too_tiny",
                                    "min_audio_bytes": phone_confirm_min_audio_bytes,
                                    "normal_stage_outcome": True,
                                }
                                session.log_event(
                                    action="phone_confirm_early_stop_audio_sanity",
                                    status="handled",
                                    reason="phone_confirm_early_stopped_audio_too_tiny",
                                    details=transcript_details,
                                )
                transcript_status = "ok" if transcript_text else "unavailable"
                stage_latency_context = {
                    "stage": stage.value,
                    "turn_idx": turn_idx,
                    "stage_enter_ts": stage_enter_ts,
                    "stage_enter_perf": stage_enter_perf,
                    "client_speech_end_perf": record_end_perf,
                }
                session.log_event(
                    action="user_transcribed",
                    status=transcript_status,
                    reason=None if transcript_text else transcript_details.get("reason", "empty_transcript"),
                    dur_ms=stt_ms,
                    details={**transcript_details, "text": transcript_text},
                )
                _log_latency_segment(
                    session,
                    "latency_asr_done",
                    stage_latency_context,
                    status=transcript_status,
                    reason=None if transcript_text else transcript_details.get("reason", "empty_transcript"),
                    dur_ms=stt_ms,
                    details={
                        "record_ms": dur_ms,
                        "record_event_type": event.get("type"),
                        "text_present": bool(transcript_text),
                    },
                )
                prompt_text = next_prompt(stage, session.dialog.profile)
                _append_turn(artifact_dir, build_turn_record(stage, prompt_text, transcript_text).to_dict())

                decision_start = time.perf_counter()
                new_stage, new_profile = apply_turn(stage, session.dialog.profile, transcript_text)
                decision_ms = int((time.perf_counter() - decision_start) * 1000)
                stage_latency_context["next_stage"] = new_stage.value
                stage_latency_context["outcome"] = "ok"
                if stage == DialogStage.CITY and "city_validation_accepted" in new_profile:
                    city_validation_details = {
                        "raw_transcript": new_profile.get("city_validation_raw", transcript_text),
                        "normalized_transcript": new_profile.get("city_validation_normalized"),
                        "rejection_reason": new_profile.get("city_validation_reason"),
                        "lexicon_matched": bool(new_profile.get("city_validation_lexicon_matched")),
                        "alias_matched": bool(new_profile.get("city_validation_alias_matched")),
                        "accepted": bool(new_profile.get("city_validation_accepted")),
                        "canonical_city": new_profile.get("city_validation_canonical"),
                        "location_detail": new_profile.get("location_detail"),
                        "current_stage": stage.value,
                        "next_stage": new_stage.value,
                    }
                    session.log_event(
                        action="city_transcript_validation",
                        status="ok" if city_validation_details["accepted"] else "rejected",
                        reason=str(new_profile.get("city_validation_reason") or "invalid_city_transcript"),
                        details=city_validation_details,
                    )
                    if not city_validation_details["accepted"]:
                        session.log_event(
                            action="city_transcript_rejected",
                            status="handled",
                            reason=str(new_profile.get("city_validation_reason") or "invalid_city_transcript"),
                            details=city_validation_details,
                        )
                        session.log_event(
                            action="invalid_city_transcript",
                            status="handled",
                            reason=str(new_profile.get("city_validation_reason") or "invalid_city_transcript"),
                            details=city_validation_details,
                        )
                session.log_event(
                    action="dialog_decision",
                    status="ok",
                    dur_ms=decision_ms,
                    details={
                        "from_stage": stage.value,
                        "to_stage": new_stage.value,
                        "turn_idx": turn_idx,
                        "profile_fields": sorted(new_profile.keys()),
                        "department": new_profile.get("department"),
                        "department_intent": new_profile.get("department_intent"),
                        "early_transfer_requested": bool(new_profile.get("early_transfer_requested")),
                        "missing_required_fields": required_fields_missing(new_profile),
                        "clarification_needed": bool(new_profile.get("department_clarification_needed")),
                        "clarification_result": new_profile.get("department_clarification_result"),
                        "retry_count": new_profile.get("last_retry_count"),
                        "retry_limit": new_profile.get("last_retry_limit"),
                        "retry_reason": new_profile.get("last_retry_reason"),
                        "safe_finish_reason": new_profile.get("safe_finish_reason"),
                        "default_resolution": new_profile.get("department_defaulted"),
                    },
                )
                _log_latency_segment(
                    session,
                    "latency_decision_done",
                    stage_latency_context,
                    dur_ms=decision_ms,
                    details={
                        "from_stage": stage.value,
                        "to_stage": new_stage.value,
                        "missing_required_fields": required_fields_missing(new_profile),
                        "safe_finish_reason": new_profile.get("safe_finish_reason"),
                    },
                )
                session.dialog.stage = new_stage
                session.dialog.profile = new_profile
                session.dialog.turns_done += 1
                session.dialog.transcripts.append(transcript_text)
                _save_profile(artifact_dir, session.dialog.profile)
                _log_latency_segment(
                    session,
                    "latency_stage_done",
                    stage_latency_context,
                    dur_ms=int((time.perf_counter() - stage_enter_perf) * 1000),
                    details={
                        "from_stage": stage.value,
                        "to_stage": new_stage.value,
                        "outcome": "dialog_continue",
                    },
                )
                dialogue_lines.append(f"Секретарь: {prompt_text}")
                dialogue_lines.append(f"Клиент: {transcript_text}")

                if _is_successful_phone_capture(stage, new_stage, session.dialog.profile):
                    transferred, moh_started = await _play_transfer_and_continue(
                        client,
                        session,
                        system_sounds,
                        moh_started,
                        app_name=app_name,
                        storage_dir=settings.storage_dir,
                    )
                    if transferred:
                        return
                    _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
                    await client.hangup_safe(channel_id)
                    return
                if (
                    stage == DialogStage.PHONE
                    and new_stage == DialogStage.PHONE_CONFIRM
                    and not _phone_confirm_fast_path_available(session.dialog.profile, system_sounds)
                ):
                    holding_played, moh_started = await _play_phone_confirm_holding_prompt(
                        client,
                        app_name,
                        session,
                        system_sounds,
                        moh_started,
                        stage_latency_context,
                    )
                    stage_latency_context["holding_played"] = holding_played
                pending_latency_context = stage_latency_context

            transcript_for_pipeline = "\n".join(dialogue_lines)
            profile_for_pipeline = dict(session.dialog.profile)
            global_turn_limit_exhausted = (
                session.dialog.turns_done >= max_turns
                and session.dialog.stage not in {DialogStage.PHONE, DialogStage.PHONE_CONFIRM}
            )
            if session.dialog.stage == DialogStage.SAFE_FINISH or global_turn_limit_exhausted:
                reason = str(session.dialog.profile.get("safe_finish_reason") or "dialog_retry_limit")
                session.transition(
                    CallState.DONE,
                    action="safe_finish",
                    status="ok",
                    reason=reason,
                    details={
                        "stage": session.dialog.stage.value,
                        "turns_done": session.dialog.turns_done,
                        "safe_finish_reason": reason,
                        "missing_required_fields": required_fields_missing(session.dialog.profile),
                        "retry_count": session.dialog.profile.get("last_retry_count"),
                        "retry_limit": session.dialog.profile.get("last_retry_limit"),
                    },
                )
                _persist_callback_record(
                    session,
                    settings.storage_dir,
                    outcome_type="safe_finish",
                    outcome_reason=reason,
                )
                played_safe_finish, moh_started = await _play_safe_finish_phrase(
                    client,
                    settings,
                    app_name,
                    session,
                    system_sounds,
                    moh_started,
                    reason,
                )
                if not played_safe_finish:
                    _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
                await client.hangup_safe(channel_id)
                return
            if session.dialog.stage == DialogStage.DONE:
                transferred, moh_started = await _play_transfer_and_continue(
                    client,
                    session,
                    system_sounds,
                    moh_started,
                    app_name=app_name,
                    storage_dir=settings.storage_dir,
                )
                if transferred:
                    return
                _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
                await client.hangup_safe(channel_id)
                return
            if session.dialog.stage in {DialogStage.PHONE, DialogStage.PHONE_CONFIRM}:
                session.transition(
                    CallState.FAILED,
                    action="phone_unconfirmed_no_generic_pipeline",
                    status="fail",
                    reason="phone_not_confirmed",
                    details={
                        "stage": session.dialog.stage.value,
                        "turns_done": session.dialog.turns_done,
                    },
                )
                _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
                await client.hangup_safe(channel_id)
                return

        session.transition(CallState.THINKING, action="pipeline_start", status="start")
        moh_started = await _maybe_start_moh(client, session, moh_started, action="moh_start_thinking")

        pipeline_start = time.perf_counter()
        if settings.demo_mode == "synth":
            result = run_pipeline(
                "real",
                settings,
                audio_path_override=input_path,
                call_id_override=session.call_id,
                artifact_dir_override=session.artifact_dir,
                events_path_override=session.events_path,
                channel_id=session.channel_id,
            )
        else:
            result = run_pipeline_from_transcript(
                "real",
                settings,
                transcript_text=transcript_for_pipeline,
                profile_override=profile_for_pipeline,
                call_id_override=session.call_id,
                artifact_dir_override=session.artifact_dir,
                events_path_override=session.events_path,
                channel_id=session.channel_id,
            )
        session.log_event(action="pipeline_done", status="ok", dur_ms=int((time.perf_counter() - pipeline_start) * 1000))

        response_tts_path = result["paths"].get("response_for_tts")
        if not response_tts_path:
            session.transition(CallState.FAILED, action="tts_text", status="fail", reason="response_for_tts_missing")
            return

        tts_text = Path(response_tts_path).read_text(encoding="utf-8")
        tts = SileroTTS()
        tts_start = time.perf_counter()
        reply_wav = tts.synthesize(tts_text)
        reply_path = artifact_dir / "reply.wav"
        save_bytes(reply_path, reply_wav)
        session.log_event(action="tts_done", status="ok", dur_ms=int((time.perf_counter() - tts_start) * 1000))

        remote_rel_path = f"{settings.asterisk_sounds_subdir}/{call_id}/reply.wav"
        publish_start = time.perf_counter()
        publish_timeout_sec = _publish_total_timeout_sec()
        publish_cmd_timeout_sec = _env_int("PUBLISH_CMD_TIMEOUT_SEC", 15)
        try:
            publish_result = await asyncio.wait_for(
                asyncio.to_thread(
                    publish_wav_to_asterisk,
                    reply_path,
                    remote_rel_path,
                    settings,
                    cmd_timeout_sec=publish_cmd_timeout_sec,
                ),
                timeout=publish_timeout_sec,
            )
        except asyncio.TimeoutError:
            session.log_event(
                action="publish",
                status="fail",
                reason="publish_timeout",
                dur_ms=int((time.perf_counter() - publish_start) * 1000),
                details={
                    "remote_rel_path": remote_rel_path,
                    "publish_timeout_sec": publish_timeout_sec,
                    "publish_cmd_timeout_sec": publish_cmd_timeout_sec,
                    "docker_container": bool(settings.asterisk_docker_container),
                },
            )
            fallback_details = {
                "remote_rel_path": remote_rel_path,
                "publish_timeout_sec": publish_timeout_sec,
                "publish_cmd_timeout_sec": publish_cmd_timeout_sec,
                "docker_container": bool(settings.asterisk_docker_container),
            }
            _played, moh_started = await _play_publish_failure_fallback(
                client,
                session,
                system_sounds,
                moh_started,
                reason="publish_timeout",
                publish_details=fallback_details,
            )
            session.transition(
                CallState.FAILED,
                action="publish_timeout_fallback_no_immediate_hangup",
                status="ok",
            )
            return

        publish_ms = int((time.perf_counter() - publish_start) * 1000)
        if not publish_result.get("ok"):
            reason = _publish_result_reason(publish_result)
            session.log_event(action="publish", status="fail", reason=reason, dur_ms=publish_ms, details=publish_result)
            _played, moh_started = await _play_publish_failure_fallback(
                client,
                session,
                system_sounds,
                moh_started,
                reason=reason,
                publish_details=publish_result,
            )
            await client.hangup_safe(channel_id)
            session.transition(CallState.FAILED, action="hangup_after_publish_fail", status="ok")
            return

        media_id = str(publish_result.get("sound_id"))
        session.log_event(
            action="publish",
            status="ok",
            sound_id=media_id,
            remote_path=str(publish_result.get("remote_path") or ""),
            dur_ms=publish_ms,
            details=publish_result.get("details"),
        )

        moh_started = await _maybe_stop_moh(client, session, moh_started)
        session.transition(CallState.RESPONDING, action="playback_start", status="start", media=media_id)

        play_result = await client.play_safe(channel_id, media_id)
        if not play_result["ok"]:
            session.log_event(
                action="playback",
                status="fail",
                reason=play_result.get("reason"),
                http_status=play_result.get("http_status"),
                media=media_id,
                sound_id=media_id,
                details=play_result.get("details"),
            )
            _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
            await client.hangup_safe(channel_id)
            session.transition(
                CallState.FAILED,
                action="playback_failed",
                status="fail",
                reason=play_result.get("reason"),
                http_status=play_result.get("http_status"),
                media=media_id,
                sound_id=media_id,
                details=play_result.get("details"),
            )
            return

        session.log_event(action="playback", status="ok", media=media_id, sound_id=media_id)
        await asyncio.sleep(1)
        await client.hangup_safe(channel_id)
        session.transition(CallState.DONE, action="hangup", status="ok")
    except Exception as exc:
        session.transition(CallState.FAILED, action="call_flow_exception", status="fail", reason=repr(exc))
        raise
    finally:
        await _maybe_stop_moh(client, session, moh_started)


async def main() -> None:
    settings = Settings.from_env()
    if os.getenv("WARMUP", "0") == "1":
        try:
            warmup_embeddings()
            print("WARMUP_EMBEDDINGS_OK")
        except Exception as exc:
            print("WARMUP_EMBEDDINGS_FAIL", repr(exc))

    base_url = os.getenv("ARI_URL", "http://localhost:8088/ari")
    username = os.getenv("ARI_USER", "")
    password = os.getenv("ARI_PASSWORD", "")
    app_name = os.getenv("ARI_APP_NAME", "")
    if not app_name:
        print("ARI_APP_NAME is required")
        return

    _start_system_sounds_task(settings)

    client = AriClient(base_url=base_url, username=username, password=password)
    sessions: dict[str, CallSession] = {}
    call_tasks: dict[str, asyncio.Task[None]] = {}

    print("ARI_LISTENING", base_url, app_name)
    try:
        async for event in client.ws_events(app_name=app_name, subscribe_all=True):
            event_type = event.get("type")
            channel = event.get("channel", {})
            channel_id = channel.get("id")

            if event_type == "StasisStart" and channel_id:
                if _is_live_external_media_stasis_channel(channel):
                    _log_external_media_channel_ignored(settings, channel)
                    continue
                call_id = channel_id
                artifact_dir = settings.storage_dir / "artifacts" / call_id
                session = CallSession(call_id=call_id, channel_id=channel_id, artifact_dir=artifact_dir)
                sessions[channel_id] = session
                print("STASIS_START", channel_id)

                answer_result = await client.answer_safe(channel_id)
                if not answer_result["ok"]:
                    session.transition(
                        CallState.FAILED,
                        action="answer",
                        status="fail",
                        reason=answer_result.get("reason"),
                        http_status=answer_result.get("http_status"),
                        details=answer_result.get("details"),
                    )
                    continue
                session.transition(CallState.ANSWERED, action="answer", status="ok")

                moh_started = await _maybe_start_moh(client, session, False, action="moh_start_after_answer")

                async def _run_call(sess: CallSession, started: bool) -> None:
                    try:
                        await handle_call(client, settings, app_name, sess, moh_started=started)
                    except Exception as exc:
                        print("CALL_FLOW_ERROR", sess.channel_id, repr(exc))

                task = asyncio.create_task(_run_call(session, moh_started), name=f"call-{channel_id}")
                call_tasks[channel_id] = task
                task.add_done_callback(lambda _t, ch=channel_id: call_tasks.pop(ch, None))

            elif event_type in {"StasisEnd", "ChannelDestroyed"} and channel_id:
                session = sessions.pop(channel_id, None)
                if session is not None and session.state not in {CallState.DONE, CallState.FAILED}:
                    session.transition(CallState.DONE, action=event_type, status="ok")
                print("STASIS_END", channel_id, event_type)
    except Exception as exc:
        print("ARI_APP_ERROR", repr(exc))
    finally:
        if call_tasks:
            await asyncio.gather(*call_tasks.values(), return_exceptions=True)
        if _system_sounds_task is not None:
            await asyncio.gather(_system_sounds_task, return_exceptions=True)


def _is_live_external_media_stasis_channel(channel: dict[str, Any]) -> bool:
    return is_live_external_media_channel(
        str(channel.get("id") or ""),
        str(channel.get("name") or ""),
    )


def _log_external_media_channel_ignored(settings: Settings, channel: dict[str, Any]) -> None:
    channel_id = str(channel.get("id") or "")
    channel_name = str(channel.get("name") or "")
    artifact_dir = settings.storage_dir / "artifacts" / (channel_id or "live-proof-ext-unknown")
    session = CallSession(call_id=channel_id, channel_id=channel_id, artifact_dir=artifact_dir)
    session.log_event(
        action="stt_live_external_media_channel_ignored",
        status="skipped",
        reason="external_media_channel_excluded",
        details={
            "channel_id": channel_id,
            "channel_name": channel_name,
        },
    )
    print("STASIS_EXTERNAL_MEDIA_IGNORED", channel_id, channel_name)


def _reset_fallback_cache_for_tests() -> None:
    global _system_sounds_done, _system_sounds_lock, _system_sounds_task
    _system_sounds_done = False
    _system_sounds_lock = None
    _system_sounds_task = None
    for sound_id in _system_sound_status:
        _system_sound_status[sound_id] = False


if __name__ == "__main__":
    asyncio.run(main())
