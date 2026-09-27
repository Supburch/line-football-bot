"""Test bootstrap: load test env vars before any ``app.*`` module is imported.

``app.config.Config`` reads required secrets (``LINE_CHANNEL_ACCESS_TOKEN``,
``LINE_CHANNEL_SECRET``, ``FOOTBALL_API_KEY``) at import time, so the test
session must provide them up front. SUPABASE is pointed at a localhost
placeholder so tests never touch the real database.
"""
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.test", override=True)
