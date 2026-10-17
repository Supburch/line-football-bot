"""Regression tests for the live-event monitor (red card / goal / VAR)."""

from unittest.mock import patch

from app.jobs import monitor_goals
from app.services.line_service import BroadcastResult
from app.services.match_state_manager import MatchStateManager


def _watched_match(bookings=None, goals=None, home=0, away=0):
    return {
        "id": 4242,
        "utcDate": "",
        "status": "IN_PLAY",
        "competition": {"code": "PL"},
        "homeTeam": {"name": "Liverpool", "crest": "https://example.com/liv.png"},
        "awayTeam": {"name": "Chelsea", "crest": "https://example.com/che.png"},
        "score": {
            "winner": None,
            "duration": "REGULAR",
            "fullTime": {"home": home, "away": away},
            "halfTime": {"home": 0, "away": 0},
            "regularTime": None,
            "extraTime": None,
            "penalties": None,
        },
        "goals": goals or [],
        "bookings": bookings or [],
    }


_RED_CARD = {
    "card": "RED",
    "player": {"name": "V. Dijk"},
    "team": {"name": "Liverpool"},
    "minute": 60,
}

_YELLOW_CARD = {
    "card": "YELLOW",
    "player": {"name": "V. Dijk"},
    "team": {"name": "Liverpool"},
    "minute": 60,
}

_PENALTY_GOAL = {
    "minute": "30",
    "type": "PENALTY",
    "team": {"name": "Liverpool"},
    "scorer": {"name": "Mohamed Salah"},
    "score": {"home": 1, "away": 0},
}


def _run_monitor(matches, *, already_sent):
    sent_events = []

    with patch.object(monitor_goals, "state_manager", MatchStateManager()), patch.object(
        monitor_goals, "is_live_score_enabled", return_value=True
    ), patch.object(monitor_goals, "get_sent_event", return_value=already_sent), patch.object(
        monitor_goals, "get_match_score", return_value=None
    ), patch.object(
        monitor_goals, "commit_match_state", return_value=None
    ), patch.object(
        monitor_goals, "broadcast", return_value=BroadcastResult.SUCCESS
    ), patch.object(
        monitor_goals, "mark_sent_event", side_effect=sent_events.append
    ):
        for match in matches:
            monitor_goals._monitor_goals_inner(live_matches=[match])

    return sent_events


def test_standalone_red_card_is_broadcast_even_without_score_change():
    """A red card with no goal/VAR in the same poll must still be notified."""
    sent = _run_monitor([_watched_match(bookings=[_RED_CARD])], already_sent=False)
    assert sent == ["4242-RED_CARD-V._Dijk-60"]


def test_red_card_already_notified_is_not_rebroadcast():
    """An already-sent red card must not be broadcast again."""
    sent = _run_monitor([_watched_match(bookings=[_RED_CARD])], already_sent=True)
    assert sent == []


def test_yellow_card_is_not_broadcast():
    """A plain yellow card must not be notified."""
    sent = _run_monitor([_watched_match(bookings=[_YELLOW_CARD])], already_sent=False)
    assert sent == []


def test_penalty_goal_is_broadcast():
    """A penalty goal (type == PENALTY) must be notified, unlike regular goals."""
    first = _watched_match()
    second = _watched_match(goals=[_PENALTY_GOAL], home=1, away=0)
    sent = _run_monitor([first, second], already_sent=False)
    assert sent == ["4242-PENALTY-Mohamed_Salah-30"]


def test_regular_goal_is_not_broadcast():
    """A normal (non-penalty) goal must remain silent."""
    regular_goal = {
        "minute": "30",
        "type": "REGULAR",
        "team": {"name": "Liverpool"},
        "scorer": {"name": "Mohamed Salah"},
        "score": {"home": 1, "away": 0},
    }
    first = _watched_match()
    second = _watched_match(goals=[regular_goal], home=1, away=0)
    sent = _run_monitor([first, second], already_sent=False)
    assert sent == []


_NON_FAVORITE_RED_CARD = {
    "card": "RED",
    "player": {"name": "J. Pickford"},
    "team": {"name": "Everton"},
    "minute": 60,
}

_PENALTY_GOAL_EVERTON = {
    "minute": "30",
    "type": "PENALTY",
    "team": {"name": "Everton"},
    "scorer": {"name": "D. Calvert-Lewin"},
    "score": {"home": 1, "away": 0},
}


def _non_watched_match(bookings=None, goals=None, home=0, away=0):
    """A live match where neither side is one of the favorite teams."""
    return {
        "id": 4242,
        "utcDate": "",
        "status": "IN_PLAY",
        "competition": {"code": "PL"},
        "homeTeam": {"name": "Everton", "crest": ""},
        "awayTeam": {"name": "Chelsea", "crest": ""},
        "score": {
            "winner": None,
            "duration": "REGULAR",
            "fullTime": {"home": home, "away": away},
            "halfTime": {"home": 0, "away": 0},
            "regularTime": None,
            "extraTime": None,
            "penalties": None,
        },
        "goals": goals or [],
        "bookings": bookings or [],
    }


def test_non_favorite_red_card_is_broadcast():
    """Red cards are notified for every live match, not only favorite teams."""
    sent = _run_monitor([_non_watched_match(bookings=[_NON_FAVORITE_RED_CARD])], already_sent=False)
    assert sent == ["4242-RED_CARD-J._Pickford-60"]


def test_non_favorite_penalty_goal_is_broadcast():
    """Penalty goals are notified for every live match, not only favorite teams."""
    first = _non_watched_match()
    second = _non_watched_match(goals=[_PENALTY_GOAL_EVERTON], home=1, away=0)
    sent = _run_monitor([first, second], already_sent=False)
    assert sent == ["4242-PENALTY-D._Calvert-Lewin-30"]


def test_monitor_fetches_epl_and_ucl_competitions():
    """The live poll must fetch UCL alongside the EPL, not a single league.

    Regression guard for the missed Liverpool UCL red card: the monitor used to
    fetch only ACTIVE_COMPETITION (PL during the EPL season), so a red card in a
    Champions League match was never seen.
    """
    with patch.object(monitor_goals, "state_manager", MatchStateManager()), patch.object(
        monitor_goals, "is_live_score_enabled", return_value=True
    ), patch.object(monitor_goals, "svc") as mock_svc:
        mock_svc.fetch.return_value = {"matches": []}
        monitor_goals._monitor_goals_inner()
        endpoint = mock_svc.fetch.call_args[0][0]
        codes = endpoint.split("competitions=", 1)[1].split("&", 1)[0]
        assert set(codes.split(",")) == {"PL", "CL"}
