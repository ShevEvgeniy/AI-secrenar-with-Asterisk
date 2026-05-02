"""Tests for multi-turn dialog flow helpers."""

from __future__ import annotations

from ai_secretary.telephony.call_session import DialogStage
from ai_secretary.telephony.dialog import (
    PHONE_RETRY_PROMPTS,
    apply_turn,
    next_prompt,
    phone_confirm_prompt_text,
    phone_digits_to_spoken_ru,
    should_stop_dialog,
)


def test_dialog_state_transitions_typical_inputs() -> None:
    profile: dict[str, str] = {}
    state = DialogStage.ISSUE

    state, profile = apply_turn(state, profile, "Need cylinders")
    assert state == DialogStage.NAME
    assert profile["issue"] == "Need cylinders"

    state, profile = apply_turn(state, profile, "Ivan Petrov")
    assert state == DialogStage.CITY
    assert profile["name"] == "Ivan Petrov"

    state, profile = apply_turn(state, profile, "from Moscow")
    assert state == DialogStage.PHONE
    assert profile["city"] == "from Moscow"

    state, profile = apply_turn(state, profile, "My phone is 9 903 678 46 53")
    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_digits"] == "99036784653"
    assert profile["phone_confirmed"] is False

    state, profile = apply_turn(state, profile, "да")
    assert state == DialogStage.DONE
    assert profile["phone_digits"] == "99036784653"
    assert profile["phone_confirmed"] is True


def test_dialog_max_turns_stops_loop() -> None:
    profile: dict[str, str] = {}
    state = DialogStage.ISSUE
    turns_done = 0
    max_turns = 4

    while not should_stop_dialog(state, turns_done, max_turns):
        transcript = "Need order help" if state == DialogStage.ISSUE else ""
        state, profile = apply_turn(state, profile, transcript)
        turns_done += 1

    assert turns_done == max_turns
    assert state != DialogStage.DONE


def test_empty_issue_transcript_does_not_complete_dialog() -> None:
    state, profile = apply_turn(DialogStage.ISSUE, {}, "")

    assert state == DialogStage.ISSUE
    assert profile == {}


def test_dialog_done_prompt_exact_transfer_phrase() -> None:
    assert next_prompt(DialogStage.DONE, {}) == "хорошо я соединяю вас с отделом продаж."


def test_phone_stage_accepts_dotted_mobile_transcription() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920.032.0355")

    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_digits"] == "9200320355"
    assert profile["phone_formatted"] == "+7 920 032-03-55"


def test_city_reasks_when_not_confident() -> None:
    state, profile = apply_turn(DialogStage.CITY, {}, "12345")

    assert state == DialogStage.CITY
    assert profile == {}

    state, profile = apply_turn(DialogStage.CITY, {}, "Мос")

    assert state == DialogStage.CITY
    assert profile == {}


def test_name_reasks_on_obvious_stt_junk() -> None:
    state, profile = apply_turn(DialogStage.NAME, {}, "you")

    assert state == DialogStage.NAME
    assert profile == {}

    state, profile = apply_turn(DialogStage.NAME, {}, "Ivan Petrov")

    assert state == DialogStage.CITY
    assert profile["name"] == "Ivan Petrov"


def test_phone_confirmation_rejects_and_redictates() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920.032.0355")
    assert state == DialogStage.PHONE_CONFIRM

    state, profile = apply_turn(state, profile, "нет")
    assert state == DialogStage.PHONE
    assert profile["phone_confirmed"] is False

    state, profile = apply_turn(state, profile, "903 678 46 53")
    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_digits"] == "9036784653"

    state, profile = apply_turn(state, profile, "верно")
    assert state == DialogStage.DONE
    assert profile["phone_confirmed"] is True


def test_phone_reasks_until_complete_digit_floor() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920 032")

    assert state == DialogStage.PHONE
    assert profile["phone_retry_reason"] == "incomplete"
    assert next_prompt(state, profile) == PHONE_RETRY_PROMPTS["incomplete"][0]

    state, profile = apply_turn(DialogStage.PHONE, {}, "920 032 03 55")

    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_digits"] == "9200320355"
    assert "phone_retry_prompt" not in profile


def test_phone_retry_prompts_vary_by_reason_without_immediate_repeat() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "не расслышал")

    assert state == DialogStage.PHONE
    assert profile["phone_retry_reason"] == "unclear"
    assert next_prompt(state, profile) == PHONE_RETRY_PROMPTS["unclear"][0]

    state, profile = apply_turn(state, profile, "снова без цифр")

    assert state == DialogStage.PHONE
    assert profile["phone_retry_reason"] == "unclear"
    assert next_prompt(state, profile) == PHONE_RETRY_PROMPTS["unclear"][1]


def test_negative_phone_confirmation_uses_rejected_retry_prompt() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920.032.0355")
    assert state == DialogStage.PHONE_CONFIRM

    state, profile = apply_turn(state, profile, "нет")

    assert state == DialogStage.PHONE
    assert profile["phone_retry_reason"] == "rejected"
    assert next_prompt(state, profile) == PHONE_RETRY_PROMPTS["rejected"][0]


def test_phone_confirmation_meta_repair_returns_to_phone_capture() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920.032.0355")
    assert state == DialogStage.PHONE_CONFIRM

    state, profile = apply_turn(state, profile, "вы ничего не произнесли")

    assert state == DialogStage.PHONE
    assert profile["phone_retry_reason"] == "meta_repair"
    assert next_prompt(state, profile) == PHONE_RETRY_PROMPTS["meta_repair"][0]


def test_phone_confirm_prompt_uses_tts_safe_spoken_digits() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920.032.0355")

    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_formatted"] == "+7 920 032-03-55"
    assert profile["phone_spoken"] == "девять, два, ноль, ноль, три, два, ноль, три, пять, пять"
    assert phone_digits_to_spoken_ru("79200320355") == (
        "семь, девять, два, ноль, ноль, три, два, ноль, три, пять, пять"
    )
    assert phone_confirm_prompt_text(profile) == (
        "Правильно ли я записала ваш номер: девять, два, ноль, ноль, три, два, ноль, три, пять, пять?"
    )
    assert next_prompt(state, profile) == phone_confirm_prompt_text(profile)
