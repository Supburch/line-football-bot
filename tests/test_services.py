import pytest
from unittest.mock import patch, MagicMock
from app.services.football_service import FootballService

def test_football_service_init():
    svc = FootballService("fake_key")
    assert svc.api_key == "fake_key"
    assert "https://api.football-data.org/v4/" == svc.BASE_URL
