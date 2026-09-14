from unittest.mock import patch

from app.handlers.command_handler import build_upcoming, handle_command
from app.utils.teams import TEAM_ALIASES, get_team_name, resolve_team


def test_handle_command_invalid():
    res = handle_command("randomtext")
    assert "สวัสดี" in res
    assert "แจ้งเตือนอัตโนมัติ" in res


def test_only_four_favorite_teams():
    assert set(TEAM_ALIASES) == {"arsenal", "liverpool", "newcastle", "tottenham"}


def test_resolve_team_thai_nicknames():
    assert resolve_team("โปรแกรม ไก่") == "tottenham"
    assert resolve_team("โปรแกรม ไก่เดือยทอง") == "tottenham"
    assert resolve_team("โปรแกรม สเปอร์ส") == "tottenham"
    assert resolve_team("โปรแกรม หงส์") == "liverpool"
    assert resolve_team("โปรแกรม หงส์แดง") == "liverpool"
    assert resolve_team("โปรแกรม ปืน") == "arsenal"
    assert resolve_team("โปรแกรม ปืนใหญ่") == "arsenal"
    assert resolve_team("โปรแกรม สาลิกา") == "newcastle"
    assert resolve_team("โปรแกรม สาลิกาดง") == "newcastle"
    assert resolve_team("โปรแกรม นิวฯ") == "newcastle"
    assert resolve_team("โปรแกรม นิว") == "newcastle"


def test_resolve_team_english_and_none():
    assert resolve_team("fixture spurs") == "tottenham"
    assert resolve_team("fixture liverpool") == "liverpool"
    assert resolve_team("fixture arsenal") == "arsenal"
    assert resolve_team("fixture Newcastle United") == "newcastle"
    # Only the 4 favorite teams are supported — anything else resolves to None.
    assert resolve_team("โปรแกรม แมนยู") is None
    assert resolve_team("fixture wolves") is None
    assert resolve_team("โปรแกรม") is None
    assert resolve_team("โปรแกรม นัดถัดไป") is None


def test_get_team_name():
    assert get_team_name("tottenham") == "สเปอร์ส"
    assert get_team_name("liverpool") == "ลิเวอร์พูล"
    assert get_team_name("newcastle") == "นิวคาสเซิล"
    assert get_team_name("arsenal") == "อาร์เซน่อล"
    assert get_team_name("unknown") == "Unknown"


def _sample_matches():
    return {
        "matches": [
            {
                "homeTeam": {"name": "Tottenham Hotspur FC", "crest": ""},
                "awayTeam": {"name": "Everton FC", "crest": ""},
                "utcDate": "2026-09-19T15:00:00Z",
                "stage": "REGULAR_SEASON",
            },
            {
                "homeTeam": {"name": "Newcastle United FC", "crest": ""},
                "awayTeam": {"name": "Arsenal FC", "crest": ""},
                "utcDate": "2026-09-20T15:00:00Z",
                "stage": "REGULAR_SEASON",
            },
            {
                "homeTeam": {"name": "Liverpool FC", "crest": ""},
                "awayTeam": {"name": "Chelsea FC", "crest": ""},
                "utcDate": "2026-09-21T15:00:00Z",
                "stage": "REGULAR_SEASON",
            },
        ]
    }


@patch("app.flex.flex_builders.get_remaining_quota_text", return_value="")
@patch("app.handlers.command_handler.svc.fetch")
def test_build_upcoming_team_filter(fetch_mock, _quota_mock):
    fetch_mock.return_value = _sample_matches()

    res = build_upcoming(team_filter="liverpool")
    assert isinstance(res, dict)
    # One match filtered -> exactly one match box in the body.
    assert len(res["body"]["contents"]) == 1
    assert "ลิเวอร์พูล" in res["header"]["contents"][0]["text"]


@patch("app.flex.flex_builders.get_remaining_quota_text", return_value="")
@patch("app.handlers.command_handler.svc.fetch")
def test_build_upcoming_team_filter_no_match(fetch_mock, _quota_mock):
    fetch_mock.return_value = {
        "matches": [
            {
                "homeTeam": {"name": "Newcastle United FC", "crest": ""},
                "awayTeam": {"name": "Arsenal FC", "crest": ""},
                "utcDate": "2026-09-20T15:00:00Z",
                "stage": "REGULAR_SEASON",
            }
        ]
    }

    # Tottenham is a favorite team but has no fixture in this sample.
    res = build_upcoming(team_filter="tottenham")
    assert isinstance(res, str)
    assert "ไม่มีโปรแกรม" in res
    assert "สเปอร์ส" in res


@patch("app.flex.flex_builders.get_remaining_quota_text", return_value="")
@patch("app.handlers.command_handler.svc.fetch")
def test_handle_command_team_fixture(fetch_mock, _quota_mock):
    fetch_mock.return_value = _sample_matches()

    # "ไก่" is the Spurs nickname -> shows Spurs fixtures (5 next matches).
    res = handle_command("โปรแกรม ไก่")
    assert isinstance(res, dict)
    assert "สเปอร์ส" in res["header"]["contents"][0]["text"]
