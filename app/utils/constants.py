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

# --- Temporary WC 26 flag ---
# ตั้งเป็น True เพื่อปิดการแจ้งสกอร์สดช่วง WC 26 ชั่วคราว
# เปลี่ยนเป็น False เมื่อต้องการเปิดคืน
LIVE_SCORE_WC_DISABLED = True

BOT_PREFIX = "บอตเว้ย"
WAKE_WORDS = ["บอตเว้ย"]
DEFAULT_LOGO = "https://via.placeholder.com/100/CCCCCC/FFFFFF?text=?"

# World Cup Countdown Settings
WORLD_CUP_START = "2026-06-11" # วันที่ 11 มิถุนายน 2026 (เริ่มอย่างเป็นทางการตามตาราง FIFA 2026)
COUNTDOWN_COVER = "https://lh3.googleusercontent.com/d/1dmUN48peARmkGPud7dVyBAYKKYbNbFIQ"

# Premium Competition Logos
EPL_LOGO = "https://i.imgur.com/vH1N3mF.png"  # Premium EPL logo link or fallback
WC_LOGO = "https://i.imgur.com/K5fB39L.png"   # Premium World Cup gold logo link or fallback
UCL_LOGO = "https://i.imgur.com/83p5HnL.png"  # Premium UCL logo link or fallback

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
    "FINAL": "รอบชิงชนะเลิศ"
}

# Terminal states for a football match
TERMINAL_MATCH_STATUSES = {
    "FINISHED",
    "CANCELLED",
    "POSTPONED"
}

# Match statuses that should trigger memory cleanup in the goal monitor
CLEANUP_MATCH_STATUSES = {
    "FINISHED",
    "CANCELLED",
    "POSTPONED",
    "SUSPENDED",
    "ABANDONED",
    "AWARDED"
}
