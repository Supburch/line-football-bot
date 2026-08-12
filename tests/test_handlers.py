import pytest
from app.handlers.command_handler import handle_command
from app.utils.constants import BOT_PREFIX

def test_handle_command_invalid():
    res = handle_command("randomtext")
    assert "สวัสดี" in res
    assert "แจ้งเตือนประตูอัตโนมัติ" in res

