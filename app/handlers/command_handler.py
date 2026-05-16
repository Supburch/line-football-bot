from typing import Any
from app.services.football_service import svc
from app.flex.flex_builders import build_standings_flex, build_upcoming_flex
from app.utils.constants import EPL_CODE

HELP_TEXT = (
    "⚽ สวัสดี! FootballBot ยินดีให้บริการ\n\n"
    "📌 คำสั่งที่ใช้ได้:\n"
    "─────────────────────\n"
    "⚽ บอตเว้ย ผลบอล\n"
    "🔴 บอตเว้ย สด\n"
    "🏆 บอตเว้ย ตาราง\n"
    "📅 บอตเว้ย โปรแกรม\n\n"
    "🔔 แจ้งเตือนประตูอัตโนมัติทีมโปรด"
)

def build_live_scores() -> str:
    data = svc.fetch(f"competitions/{EPL_CODE}/matches?status=LIVE", ttl=30)
    if not isinstance(data, dict): return "📭 ขณะนี้ไม่มีการแข่งขัน"
    matches = data.get("matches", [])
    if not matches: return "📭 ขณะนี้ไม่มีการแข่งขัน"

    lines = ["🔴 EPL LIVE SCORES", "─" * 20]
    for m in matches:
        home   = m["homeTeam"]["name"]
        away   = m["awayTeam"]["name"]
        hs     = m.get("score", {}).get("fullTime", {}).get("home") or m.get("score", {}).get("halfTime", {}).get("home") or 0
        as_    = m.get("score", {}).get("fullTime", {}).get("away") or m.get("score", {}).get("halfTime", {}).get("away") or 0
        minute = m.get("minute", m.get("status", "LIVE"))
        lines.append(f"▶️ {home} {hs} - {as_} {away} ({minute}')")
    return "\n".join(lines)

def build_recent_results() -> str:
    data = svc.fetch(f"competitions/{EPL_CODE}/matches?status=FINISHED", ttl=120)
    if not isinstance(data, dict): return "📭 ไม่มีผลการแข่งขันล่าสุด"
    matches = data.get("matches", [])
    if not matches: return "📭 ไม่มีผลการแข่งขันล่าสุด"

    lines = ["⚽ ผลบอล EPL ล่าสุด", "─" * 20]
    # เอา 10 นัดล่าสุด (อยู่ท้ายสุดของ array) และเรียงให้ล่าสุดอยู่บนสุด
    recent_matches = reversed(matches[-10:])
    for m in recent_matches:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        hs   = m.get("score", {}).get("fullTime", {}).get("home", "?")
        as_  = m.get("score", {}).get("fullTime", {}).get("away", "?")
        lines.append(f"✅ {home} {hs} - {as_} {away}")
    return "\n".join(lines)

def build_standings() -> Any:
    data = svc.fetch(f"competitions/{EPL_CODE}/standings", ttl=14400)
    if not isinstance(data, dict): return "📭 ยังไม่มีข้อมูลตารางคะแนน"
    standings_groups = data.get("standings", [])
    if not standings_groups: return "📭 ยังไม่มีข้อมูลตารางคะแนน"
    return build_standings_flex(standings_groups)

def build_upcoming() -> Any:
    data = svc.fetch(f"competitions/{EPL_CODE}/matches?status=SCHEDULED", ttl=300)
    if not isinstance(data, dict): return "📭 ตอนนี้ไม่มีโปรแกรมการแข่งขัน"
    matches = data.get("matches", [])
    if not matches: return "📭 ตอนนี้ไม่มีโปรแกรมการแข่งขัน"
    return build_upcoming_flex(matches)

COMMAND_MAP = [
    (("สด", "live"), build_live_scores),
    (("ตาราง", "table", "standing"), build_standings),
    (("ผล", "ผลบอล", "result"), build_recent_results),
    (("โปรแกรม", "fixture", "นัดถัดไป"), build_upcoming),
]

def handle_command(cmd_text: str) -> Any:
    cmd = cmd_text.strip().lower()
    for keys, func in COMMAND_MAP:
        if any(k in cmd for k in keys):
            return func()
    return HELP_TEXT
