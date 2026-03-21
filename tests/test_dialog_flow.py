"""Tests for multi-turn dialog flow helpers."""

from __future__ import annotations

from ai_secretary.telephony.call_session import DialogStage
from ai_secretary.telephony.dialog import apply_turn, should_stop_dialog


def test_dialog_state_transitions_typical_inputs() -> None:
    profile: dict[str, str] = {}
    state = DialogStage.ISSUE

    state, profile = apply_turn(state, profile, "Хочу уточнить условия поставки оборудования.")
    assert state == DialogStage.NAME
    assert profile["issue"].startswith("Хочу уточнить")

    state, profile = apply_turn(state, profile, "Меня зовут Иван Петров")
    assert state == DialogStage.CITY
    assert profile["name"] == "Иван Петров"

    state, profile = apply_turn(state, profile, "Я из Казани")
    assert state == DialogStage.PHONE
    assert profile["city"] == "Казани"

    state, profile = apply_turn(state, profile, "Мой телефон 9 903 678 46 53")
    assert state == DialogStage.DONE
    assert profile["phone_digits"] == "79036784653"


def test_dialog_max_turns_stops_loop() -> None:
    profile: dict[str, str] = {}
    state = DialogStage.ISSUE
    turns_done = 0
    max_turns = 4

    while not should_stop_dialog(state, turns_done, max_turns):
        if state == DialogStage.ISSUE:
            transcript = "Нужна помощь с заказом."
        else:
            transcript = ""
        state, profile = apply_turn(state, profile, transcript)
        turns_done += 1

    assert turns_done == max_turns
    assert state != DialogStage.DONE
