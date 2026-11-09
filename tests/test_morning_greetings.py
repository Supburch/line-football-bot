"""Tests for the "มอนิ่ง" morning-greeting wake word logic."""

from app.utils.constants import MONING_GREETINGS, MONING_WAKE_WORDS
from app.repositories import supabase_client as sc
from app.services import morning_greeting as mg


def _install_fake_sc(monkeypatch):
    """Point the Supabase helpers at in-memory state for deterministic tests."""
    state = {"sent_today": False, "used": set()}

    def get_sent_event(key):
        return state["sent_today"] if key.startswith("moning_greeting_") else False

    def mark_sent_event(key):
        if key.startswith("moning_greeting_"):
            state["sent_today"] = True

    monkeypatch.setattr(sc, "get_sent_event", get_sent_event)
    monkeypatch.setattr(sc, "mark_sent_event", mark_sent_event)
    monkeypatch.setattr(sc, "get_moning_used_indices", lambda: set(state["used"]))
    monkeypatch.setattr(sc, "mark_moning_used", lambda idx: state["used"].add(idx))
    monkeypatch.setattr(sc, "clear_moning_used", lambda: state["used"].clear())
    return state


def test_moning_wake_word_constant():
    assert "มอนิ่ง" in MONING_WAKE_WORDS


def test_moning_greetings_has_seven_unique_sentences():
    assert len(MONING_GREETINGS) == 7
    assert len(set(MONING_GREETINGS)) == 7


def test_pick_returns_valid_greeting(monkeypatch):
    _install_fake_sc(monkeypatch)
    idx, text = mg.pick_moning_greeting()
    assert 0 <= idx < 7
    assert text == MONING_GREETINGS[idx]


def test_pick_returns_none_when_already_sent_today(monkeypatch):
    state = _install_fake_sc(monkeypatch)
    idx, _ = mg.pick_moning_greeting()
    mg.commit_moning_greeting(idx)
    assert state["sent_today"] is True
    # Second call the same day is ignored.
    assert mg.pick_moning_greeting() is None


def test_rotation_uses_all_seven_before_repeat(monkeypatch):
    state = _install_fake_sc(monkeypatch)
    seen = set()
    # Simulate 7 days, one greeting each day.
    for _ in range(7):
        idx, _ = mg.pick_moning_greeting()
        assert idx not in seen
        seen.add(idx)
        mg.commit_moning_greeting(idx)
        state["sent_today"] = False  # reset for the next day
    assert seen == set(range(7))
    assert len(state["used"]) == 7

    # On the 8th day the pool resets for a fresh random cycle.
    idx, _ = mg.pick_moning_greeting()
    assert 0 <= idx < 7
    assert state["used"] == set()
