"""Morning-greeting logic for the "มอนิ่ง" wake word.

Two constraints drive the behaviour:

1. **One greeting per day** — the bot replies at most once per BKK calendar day,
   keyed on the current date (so it naturally resets at midnight). Repeated
   "มอนิ่ง" messages on the same day are silently ignored.
2. **Use all 7 before repeating** — the 7 sentences are chosen at random without
   repeats; only once every sentence has been sent does the pool reset and start
   a fresh random cycle. The "used" set is persisted in Supabase so it survives
   Render free-tier sleeps/restarts.
"""

import random
from datetime import datetime

from app.config import Config
from app.utils.constants import MONING_GREETINGS
from app.repositories import supabase_client as sc

_DAY_KEY_PREFIX = "moning_greeting_"


def _today_key() -> str:
    return f"{_DAY_KEY_PREFIX}{datetime.now(Config.TZ).strftime('%Y-%m-%d')}"


def pick_moning_greeting() -> "tuple[int, str] | None":
    """Return ``(index, text)`` for the next greeting, or ``None`` if already sent today."""
    if sc.get_sent_event(_today_key()):
        return None

    count = len(MONING_GREETINGS)
    used = sc.get_moning_used_indices()
    available = [i for i in range(count) if i not in used]
    if not available:
        # Every sentence was used this cycle — reset and start a fresh rotation.
        sc.clear_moning_used()
        available = list(range(count))

    idx = random.choice(available)
    return idx, MONING_GREETINGS[idx]


def commit_moning_greeting(idx: int) -> None:
    """Persist that today's greeting (at ``idx``) has been sent successfully."""
    sc.mark_sent_event(_today_key())
    sc.mark_moning_used(idx)
