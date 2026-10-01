"""Coverage for the delayed-command persistence error paths.

These tests lock in the fix that keeps ``/cron/delayed`` returning 200 even when
Supabase (or the ``delayed_commands`` table) is unavailable, so cron-job.org
never auto-disables the job after consecutive non-2xx responses.
"""

from unittest.mock import patch

from flask import Flask

from app.repositories import supabase_client as sc
from app.routes import register_routes


def _boom(*args, **kwargs):
    raise RuntimeError("simulated Supabase failure")


# --- repository helpers -------------------------------------------------------


def test_get_due_delayed_commands_returns_empty_on_error():
    with patch.object(sc, "execute_with_retry", side_effect=_boom):
        assert sc.db_get_due_delayed_commands() == []


def test_get_due_delayed_commands_returns_empty_when_not_configured():
    with patch.object(sc, "supabase", None):
        assert sc.db_get_due_delayed_commands() == []


def test_insert_delayed_command_swallows_error():
    with patch.object(sc, "execute_with_retry", side_effect=_boom):
        sc.db_insert_delayed_command("id1", "target1", "ตาราง", "2026-01-01T00:00:00")


def test_reopen_delayed_command_swallows_error():
    with patch.object(sc, "execute_with_retry", side_effect=_boom):
        sc.db_reopen_delayed_command("id1")


def test_claim_delayed_command_returns_true_on_error():
    with patch.object(sc, "execute_with_retry", side_effect=_boom):
        # Best-effort delivery without dedup when Supabase is down.
        assert sc.db_claim_delayed_command("id1") is True


def test_claim_delayed_command_returns_true_when_not_configured():
    with patch.object(sc, "supabase", None):
        assert sc.db_claim_delayed_command("id1") is True


# --- route --------------------------------------------------------------------


def test_cron_delayed_returns_200_even_when_processing_raises():
    from app.handlers import message_handler as mh

    app = Flask(__name__)
    register_routes(app)
    client = app.test_client()

    with patch.object(mh, "process_due_delayed_commands", side_effect=_boom):
        resp = client.get("/cron/delayed")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "delivered": 0}
