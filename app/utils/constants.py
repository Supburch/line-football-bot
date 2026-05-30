# Core Constants
EPL_CODE = "PL"
WC_CODE = "WC"
ACTIVE_COMPETITION = WC_CODE   # Pivot all resources (EPL / World Cup) dynamically
BOT_PREFIX = "บอตเว้ย"
WAKE_WORDS = ["บอตเว้ย"]
DEFAULT_LOGO = "https://via.placeholder.com/100/CCCCCC/FFFFFF?text=?"

# World Cup Countdown Settings
WORLD_CUP_START = "2026-06-11" # วันที่ 11 มิถุนายน 2026 (เริ่มอย่างเป็นทางการตามตาราง FIFA 2026)
COUNTDOWN_COVER = "https://lh3.googleusercontent.com/d/1dmUN48peARmkGPud7dVyBAYKKYbNbFIQ"

# Premium Competition Logos
EPL_LOGO = "https://i.imgur.com/vH1N3mF.png"  # Premium EPL logo link or fallback
WC_LOGO = "https://i.imgur.com/K5fB39L.png"   # Premium World Cup gold logo link or fallback

WATCHED_TEAMS = [
    "Tottenham Hotspur",
    "Arsenal",
    "Liverpool",
    "Newcastle",
]

WATCHED_COUNTRIES = [
    "England",
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
