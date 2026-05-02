"""Tests for multi-turn dialog flow helpers."""

from __future__ import annotations

from ai_secretary.telephony.call_session import DialogStage
from ai_secretary.telephony.dialog import (
    CLARIFICATION_PROMPT,
    EARLY_TRANSFER_PROMPTS,
    INTENT_CLARIFY_MAX_RETRIES,
    ISSUE_MAX_RETRIES,
    NAME_MAX_RETRIES,
    NAME_RETRY_PROMPTS,
    PHONE_CONFIRM_MAX_RETRIES,
    PHONE_RETRY_PROMPTS,
    REQUIRED_STAGE_MAX_RETRIES,
    apply_turn,
    normalize_name_candidate,
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


def test_max_turns_do_not_stop_phone_confirmation_policy() -> None:
    assert should_stop_dialog(DialogStage.NAME, 8, 8) is True
    assert should_stop_dialog(DialogStage.PHONE, 8, 8) is False
    assert should_stop_dialog(DialogStage.PHONE_CONFIRM, 8, 8) is False


def test_empty_issue_transcript_does_not_complete_dialog() -> None:
    state, profile = apply_turn(DialogStage.ISSUE, {}, "")

    assert state == DialogStage.ISSUE
    assert profile["issue_retry_count"] == 1
    assert profile["last_retry_reason"] == "empty_transcript"


def test_unclear_issue_intent_asks_bounded_clarification() -> None:
    state, profile = apply_turn(DialogStage.ISSUE, {}, "I need help")

    assert state == DialogStage.INTENT_CLARIFY
    assert next_prompt(state, profile) == CLARIFICATION_PROMPT
    assert profile["department_clarification_needed"] is True

    state, profile = apply_turn(state, profile, "delivery")

    assert state == DialogStage.NAME
    assert profile["department"] == "delivery"
    assert profile["department_clarified"] is True
    assert profile["department_clarification_result"] == "delivery"


def test_tied_issue_intent_asks_bounded_clarification() -> None:
    state, profile = apply_turn(DialogStage.ISSUE, {}, "Need invoice and delivery")

    assert state == DialogStage.INTENT_CLARIFY
    assert profile["department_intent"] == "unclear"
    assert profile["department_clarification_needed"] is True


def test_early_transfer_at_issue_preserves_department_and_collects_name() -> None:
    state, profile = apply_turn(DialogStage.ISSUE, {}, "соедините с бухгалтерией")

    assert state == DialogStage.NAME
    assert profile["department"] == "accounting"
    assert profile["early_transfer_requested"] is True
    assert profile["early_transfer_missing_fields"] == ["name", "city", "phone"]
    assert next_prompt(state, profile) == EARLY_TRANSFER_PROMPTS[DialogStage.ISSUE]


def test_early_transfer_at_slot_stages_keeps_collecting_missing_slot() -> None:
    state, profile = apply_turn(DialogStage.NAME, {"issue": "Need cylinders"}, "соедините с отделом продаж")

    assert state == DialogStage.NAME
    assert profile["department"] == "sales"
    assert profile["early_transfer_missing_fields"] == ["name", "city", "phone"]
    assert next_prompt(state, profile) == EARLY_TRANSFER_PROMPTS[DialogStage.NAME]

    state, profile = apply_turn(DialogStage.CITY, {"issue": "Need cylinders", "name": "Ivan"}, "мне нужен отдел доставки")

    assert state == DialogStage.CITY
    assert profile["department"] == "delivery"
    assert profile["early_transfer_missing_fields"] == ["city", "phone"]
    assert next_prompt(state, profile) == EARLY_TRANSFER_PROMPTS[DialogStage.CITY]

    state, profile = apply_turn(
        DialogStage.PHONE,
        {"issue": "Need cylinders", "name": "Ivan", "city": "Moscow"},
        "соедините с бухгалтерией",
    )

    assert state == DialogStage.PHONE
    assert profile["department"] == "accounting"
    assert profile["early_transfer_missing_fields"] == ["phone"]
    assert next_prompt(state, profile) == EARLY_TRANSFER_PROMPTS[DialogStage.PHONE]


def test_dialog_done_prompt_exact_transfer_phrase() -> None:
    assert next_prompt(DialogStage.DONE, {}) == "хорошо я соединяю вас с отделом продаж."


def test_phone_stage_accepts_dotted_mobile_transcription() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920.032.0355")

    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_digits"] == "9200320355"
    assert profile["phone_formatted"] == "+7 920 032-03-55"


def test_name_prompt_asks_for_just_name() -> None:
    assert next_prompt(DialogStage.NAME, {}) == "Назовите, пожалуйста, ваше имя."


def test_russian_name_lexicon_normalizes_common_forms() -> None:
    cases = {
        "саня": "Александр",
        "меня зовут дима": "Дмитрий",
        "это серёжа петрович": "Сергей Петрович",
        "ну света ивановна спасибо": "Светлана Ивановна",
        "мое имя оля": "Ольга",
    }
    for transcript, expected in cases.items():
        assert normalize_name_candidate(transcript) == expected


def test_name_stage_stores_normalized_russian_name() -> None:
    state, profile = apply_turn(DialogStage.NAME, {}, "это саня иваныч")

    assert state == DialogStage.CITY
    assert profile["name"] == "Александр Иванович"


def test_phone_stage_accepts_comma_grouped_digit_dictation() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920, 0.32, 0.3, 0.55")

    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_digits"] == "9200320355"
    assert profile["phone_formatted"] == "+7 920 032-03-55"


def test_city_reasks_when_not_confident() -> None:
    state, profile = apply_turn(DialogStage.CITY, {}, "12345")

    assert state == DialogStage.CITY
    assert profile["city_retry_count"] == 1
    assert profile["last_retry_reason"] == "unclear_transcript"

    state, profile = apply_turn(DialogStage.CITY, {}, "Мос")

    assert state == DialogStage.CITY
    assert profile["city_retry_count"] == 1


def test_name_reasks_on_obvious_stt_junk() -> None:
    state, profile = apply_turn(DialogStage.NAME, {}, "you")

    assert state == DialogStage.NAME
    assert profile["name_retry_reason"] == "junk"

    state, profile = apply_turn(DialogStage.NAME, {}, "Ivan Petrov")

    assert state == DialogStage.CITY
    assert profile["name"] == "Ivan Petrov"


def test_name_rejects_short_english_filler() -> None:
    for transcript in ("Yep.", "ok", "Hi"):
        state, profile = apply_turn(DialogStage.NAME, {}, transcript)

        assert state == DialogStage.NAME
        assert profile["name_retry_reason"] == "junk"


def test_name_accepts_short_valid_russian_names() -> None:
    for transcript, expected in (("Ян", "Ян"), ("Лев", "Лев"), ("Оля", "Ольга")):
        state, profile = apply_turn(DialogStage.NAME, {}, transcript)

        assert state == DialogStage.CITY
        assert profile["name"] == expected


def test_name_retry_prompts_vary_by_reason_without_immediate_repeat() -> None:
    state, profile = apply_turn(DialogStage.NAME, {}, "")

    assert state == DialogStage.NAME
    assert profile["name_retry_reason"] == "unclear"
    assert next_prompt(state, profile) == NAME_RETRY_PROMPTS["unclear"][0]

    state, profile = apply_turn(state, profile, "")

    assert state == DialogStage.NAME
    assert profile["name_retry_reason"] == "unclear"
    assert next_prompt(state, profile) == NAME_RETRY_PROMPTS["unclear"][1]


def test_name_meta_repair_uses_reasoned_retry_prompt() -> None:
    state, profile = apply_turn(DialogStage.NAME, {}, "я уже сказал")

    assert state == DialogStage.NAME
    assert profile["name_retry_reason"] == "meta_repair"
    assert next_prompt(state, profile) == NAME_RETRY_PROMPTS["meta_repair"][0]


def test_name_retry_limit_advances_with_unavailable_marker() -> None:
    state = DialogStage.NAME
    profile: dict[str, object] = {}

    for _ in range(NAME_MAX_RETRIES):
        state, profile = apply_turn(state, profile, "you")

    assert state == DialogStage.SAFE_FINISH
    assert profile["safe_finish_reason"] == "name_retry_limit"
    assert "name_retry_prompt" not in profile


def test_issue_empty_retries_then_moves_to_clarification() -> None:
    state = DialogStage.ISSUE
    profile: dict[str, object] = {}

    for attempt in range(ISSUE_MAX_RETRIES):
        state, profile = apply_turn(state, profile, "")
        if attempt + 1 < ISSUE_MAX_RETRIES:
            assert state == DialogStage.ISSUE

    assert state == DialogStage.INTENT_CLARIFY
    assert profile["last_retry_count"] == ISSUE_MAX_RETRIES
    assert profile["last_retry_limit"] == ISSUE_MAX_RETRIES


def test_intent_clarify_empty_retries_then_defaults_department() -> None:
    state = DialogStage.INTENT_CLARIFY
    profile: dict[str, object] = {
        "department_clarification_needed": True,
        "department_clarification_resume_stage": DialogStage.NAME.value,
    }

    for attempt in range(INTENT_CLARIFY_MAX_RETRIES):
        state, profile = apply_turn(state, profile, "")
        if attempt + 1 < INTENT_CLARIFY_MAX_RETRIES:
            assert state == DialogStage.INTENT_CLARIFY

    assert state == DialogStage.NAME
    assert profile["department"] == "sales"
    assert profile["department_defaulted"] is True
    assert profile["department_clarification_reason"] == "default_after_intent_clarify_retries"


def test_required_stage_retries_safe_finish_without_transfer() -> None:
    state = DialogStage.CITY
    profile: dict[str, object] = {"issue": "Need cylinders", "name": "Ivan"}

    for attempt in range(REQUIRED_STAGE_MAX_RETRIES):
        state, profile = apply_turn(state, profile, "")
        if attempt + 1 < REQUIRED_STAGE_MAX_RETRIES:
            assert state == DialogStage.CITY

    assert state == DialogStage.SAFE_FINISH
    assert profile["safe_finish_reason"] == "city_retry_limit"
    assert profile["safe_finish_missing_fields"] == ["city", "phone"]


def test_phone_confirm_retries_return_to_phone_before_safe_finish() -> None:
    state = DialogStage.PHONE_CONFIRM
    profile: dict[str, object] = {"phone_digits": "9200320355", "phone_confirmed": False}

    for attempt in range(PHONE_CONFIRM_MAX_RETRIES):
        state, profile = apply_turn(state, profile, "")
        if attempt + 1 < PHONE_CONFIRM_MAX_RETRIES:
            assert state == DialogStage.PHONE_CONFIRM

    assert state == DialogStage.PHONE
    assert profile["phone_retry_reason"] == "unclear"
    assert profile["last_retry_count"] == PHONE_CONFIRM_MAX_RETRIES


def test_entering_phone_confirm_resets_confirm_retry_budget() -> None:
    state = DialogStage.PHONE
    profile: dict[str, object] = {
        "phone_confirm_retry_count": PHONE_CONFIRM_MAX_RETRIES,
        "phone_retry_count": REQUIRED_STAGE_MAX_RETRIES - 1,
    }

    state, profile = apply_turn(state, profile, "920.032.0355")

    assert state == DialogStage.PHONE_CONFIRM
    assert "phone_confirm_retry_count" not in profile
    assert "phone_retry_count" not in profile

    state, profile = apply_turn(state, profile, "")

    assert state == DialogStage.PHONE_CONFIRM
    assert profile["phone_confirm_retry_count"] == 1
    assert profile["last_retry_limit"] == PHONE_CONFIRM_MAX_RETRIES


def test_repeated_phone_confirm_failure_cycles_end_in_safe_finish() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "920.032.0355")
    assert state == DialogStage.PHONE_CONFIRM

    for _ in range(PHONE_CONFIRM_MAX_RETRIES):
        state, profile = apply_turn(state, profile, "")

    assert state == DialogStage.PHONE
    assert profile["phone_confirm_failure_count"] == 1

    state, profile = apply_turn(state, profile, "920.032.0355")
    assert state == DialogStage.PHONE_CONFIRM

    for _ in range(PHONE_CONFIRM_MAX_RETRIES):
        state, profile = apply_turn(state, profile, "")

    assert state == DialogStage.SAFE_FINISH
    assert profile["safe_finish_reason"] == "phone_retry_limit"
    assert profile["phone_confirm_failure_count"] == 2


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


def test_phone_stage_meta_repair_uses_reasoned_retry_prompt() -> None:
    state, profile = apply_turn(DialogStage.PHONE, {}, "я уже продиктовал номер для связи")

    assert state == DialogStage.PHONE
    assert profile["phone_retry_reason"] == "meta_repair"
    assert next_prompt(state, profile) == PHONE_RETRY_PROMPTS["meta_repair"][0]


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
