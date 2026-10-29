from datetime import datetime
from app.config import Config

# Core Constants
EPL_CODE = "PL"
WC_CODE = "WC"
UCL_CODE = "CL"


class DynamicCompetition:
    def __str__(self) -> str:
        bkk_now = datetime.now(Config.TZ)
        # 1. Before UCL Final (06:00 AM BKK on May 31, 2026) -> UCL (CL)
        ucl_cutoff = Config.TZ.localize(datetime(2026, 5, 31, 6, 0, 0))
        # 2. During World Cup (May 31, 2026 to July 20, 2026) -> World Cup (WC)
        wc_cutoff = Config.TZ.localize(datetime(2026, 7, 20, 0, 0, 0))

        if bkk_now < ucl_cutoff:
            return UCL_CODE
        elif bkk_now < wc_cutoff:
            return WC_CODE
        else:
            return EPL_CODE  # Revert to EPL (PL) automatically after WC ends!

    def __eq__(self, other: object) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def lower(self) -> str:
        return str(self).lower()

    def upper(self) -> str:
        return str(self).upper()


ACTIVE_COMPETITION = DynamicCompetition()

# --- Live monitor competition scope ---
# The live goal / red-card / VAR / penalty monitor watches a FIXED set of
# competitions instead of the single dynamic ACTIVE_COMPETITION, so an event
# involving a watched club is never missed just because it happened outside the
# "primary" competition (e.g. a Liverpool UCL red card during the EPL season,
# or an EPL red card while ACTIVE_COMPETITION points at the UCL).
#
# Both codes are free-tier (TIER_ONE) on football-data.org. The FA Cup (FAC),
# EFL Cup (FLC), Europa League (EL) and UEFA Conference League (API code "UCL")
# require paid plans, so a free API key would get 403 for them and they are
# intentionally omitted here.
LIVE_COMPETITIONS = [EPL_CODE, UCL_CODE]  # ["PL", "CL"]

# Comma-separated form accepted by the /v4/matches endpoint.
LIVE_COMPETITIONS_CSV = ",".join(LIVE_COMPETITIONS)

# --- Temporary WC 26 flag ---
# ตั้งเป็น True เพื่อปิดการแจ้งสกอร์สดช่วง WC 26 ชั่วคราว
# เปลี่ยนเป็น False เมื่อต้องการเปิดคืน
# *** AUTO-GUARD: จะปิดการส่งสกอร์สดเฉพาะตอนที่ competition ปัจจุบันเป็น WC เท่านั้น ***
LIVE_SCORE_WC_DISABLED = True


def is_live_score_enabled() -> bool:
    """Returns True if live score broadcasting is enabled for the current competition."""
    if LIVE_SCORE_WC_DISABLED and ACTIVE_COMPETITION == WC_CODE:
        return False
    return True


BOT_PREFIX = "บอตเว้ย"
WAKE_WORDS = ["บอตเว้ย", "บอตโว๊ย", "บอตโว้ย"]

# Delayed wake words: when a user types "-- ได้รม --", "-- เห็ด --" or
# "-- มอนิ่ง --", the bot silently picks a random display command and delivers
# it after DELAYED_RESPONSE_MINUTES.
DELAYED_WAKE_WORDS = ["ได้รม", "เห็ด", "มอนิ่ง"]
DELAYED_RESPONSE_MINUTES = 4

DEFAULT_LOGO = "https://via.placeholder.com/100/CCCCCC/FFFFFF?text=?"

# World Cup Countdown Settings
WORLD_CUP_START = "2026-06-11"  # วันที่ 11 มิถุนายน 2026 (เริ่มอย่างเป็นทางการตามตาราง FIFA 2026)
COUNTDOWN_COVER = "https://lh3.googleusercontent.com/d/1dmUN48peARmkGPud7dVyBAYKKYbNbFIQ"

# Premium Competition Logos (API-Sports public CDN; imgur links were dead)
EPL_LOGO = "https://media.api-sports.io/football/leagues/39.png"  # Premier League
WC_LOGO = "https://media.api-sports.io/football/leagues/1.png"  # FIFA World Cup
UCL_LOGO = "https://media.api-sports.io/football/leagues/2.png"  # UEFA Champions League

WATCHED_TEAMS = [
    "Tottenham Hotspur",
    "Arsenal",
    "Liverpool",
    "Newcastle",
]

WATCHED_COUNTRIES = [
    "England",
    "Germany",
    "Scotland",
    "Brazil",
]

# Translation map for football tournament stages
STAGE_TRANSLATION = {
    "GROUP_STAGE": "รอบแบ่งกลุ่ม",
    "LAST_32": "รอบ 32 ทีมสุดท้าย",
    "ROUND_OF_32": "รอบ 32 ทีมสุดท้าย",
    "LAST_16": "รอบ 16 ทีมสุดท้าย",
    "ROUND_OF_16": "รอบ 16 ทีมสุดท้าย",
    "QUARTER_FINALS": "รอบ 8 ทีมสุดท้าย",
    "SEMI_FINALS": "รอบรองชนะเลิศ",
    "THIRD_PLACE": "รอบชิงอันดับ 3",
    "FINAL": "รอบชิงชนะเลิศ",
}

# Terminal states for a football match
TERMINAL_MATCH_STATUSES = {"FINISHED", "CANCELLED", "POSTPONED"}

# Match statuses that should trigger memory cleanup in the goal monitor
CLEANUP_MATCH_STATUSES = {"FINISHED", "CANCELLED", "POSTPONED", "SUSPENDED", "ABANDONED", "AWARDED"}
