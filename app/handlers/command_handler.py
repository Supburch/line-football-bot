from typing import Any
from datetime import datetime
from app.config import Config
from app.services.football_service import svc
from app.flex.flex_builders import build_standings_flex, build_upcoming_flex, build_scorers_flex
from app.utils.constants import ACTIVE_COMPETITION, WC_CODE, UCL_CODE
from app.utils.helpers import format_minute, first_not_none

def build_help_text() -> str:
    if ACTIVE_COMPETITION == WC_CODE:
        comp_name = "(ช่วงฟุตบอลโลก)"
        notification_info = "ทีมชาติอังกฤษ"
    elif ACTIVE_COMPETITION == UCL_CODE:
        comp_name = "(ช่วงยูฟ่าแชมเปียนส์ลีก)"
        notification_info = "ทีมรักของคุณ (Spurs, Arsenal, Liverpool, Newcastle)"
    else:
        comp_name = "(ช่วงพรีเมียร์ลีก)"
        notification_info = "ทีมที่คุณชื่นชอบ"

    return (
        f"⚽ สวัสดี! FootballBot ยินดีให้บริการ\n\n"
        f"📌 คำสั่งที่ใช้ได้: {comp_name}\n"
        f"─────────────────────\n"
        f"⚽ บอตเว้ย ผลบอล\n"
        f"🔴 บอตเว้ย สด\n"
        f"🏆 บอตเว้ย ตาราง\n"
        f"📅 บอตเว้ย โปรแกรม\n"
        f"🥾 บอตเว้ย ดาวซัลโว\n\n"
        f"🔔 บริการแจ้งเตือนประตูอัตโนมัติ{notification_info}"
    )

def build_live_scores() -> str:
    data = svc.fetch(f"competitions/{ACTIVE_COMPETITION}/matches?status=LIVE", ttl=30)
    if not isinstance(data, dict): return "📭 ขณะนี้ไม่มีการแข่งขัน"
    matches = data.get("matches", [])
    if not matches: return "📭 ขณะนี้ไม่มีการแข่งขัน"

    if ACTIVE_COMPETITION == WC_CODE:
        title = "🏆 WORLD CUP LIVE SCORES"
    elif ACTIVE_COMPETITION == UCL_CODE:
        title = "⭐ UCL LIVE SCORES"
    else:
        title = "🔴 EPL LIVE SCORES"
    lines = [title, "─" * 20]
    for m in matches:
        home   = m["homeTeam"]["name"]
        away   = m["awayTeam"]["name"]
        hs     = first_not_none(m.get("score", {}).get("fullTime", {}).get("home"), m.get("score", {}).get("halfTime", {}).get("home"), 0)
        as_    = first_not_none(m.get("score", {}).get("fullTime", {}).get("away"), m.get("score", {}).get("halfTime", {}).get("away"), 0)
        minute = m.get("minute")
        if minute is not None:
            label = format_minute(minute)
        else:
            label = m.get("status", "LIVE")
        lines.append(f"▶️ {home} {hs} - {as_} {away} ({label})")
    return "\n".join(lines)

def build_recent_results() -> str:
    data = svc.fetch(f"competitions/{ACTIVE_COMPETITION}/matches?status=FINISHED", ttl=120)
    if not isinstance(data, dict): return "📭 ไม่มีผลการแข่งขันล่าสุด"
    matches = data.get("matches", [])
    if not matches: return "📭 ไม่มีผลการแข่งขันล่าสุด"

    if ACTIVE_COMPETITION == WC_CODE:
        title = "⚽ ผลบอล WORLD CUP ล่าสุด"
    elif ACTIVE_COMPETITION == UCL_CODE:
        title = "⚽ ผลบอล UCL ล่าสุด"
    else:
        title = "⚽ ผลบอล EPL ล่าสุด"
    lines = [title, "─" * 20]
    # เอา 10 นัดล่าสุด (อยู่ท้ายสุดของ array) และเรียงให้ล่าสุดอยู่บนสุด
    recent_matches = reversed(matches[-10:])
    for m in recent_matches:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        score = m.get("score", {})
        hs   = first_not_none(score.get("fullTime", {}).get("home"), score.get("halfTime", {}).get("home"), "?")
        as_  = first_not_none(score.get("fullTime", {}).get("away"), score.get("halfTime", {}).get("away"), "?")
        lines.append(f"✅ {home} {hs} - {as_} {away}")
    return "\n".join(lines)

def build_standings() -> Any:
    data = svc.fetch(f"competitions/{ACTIVE_COMPETITION}/standings", ttl=14400)
    if not isinstance(data, dict): return "📭 ยังไม่มีข้อมูลตารางคะแนน"
    standings_groups = data.get("standings", [])
    if not standings_groups: return "📭 ยังไม่มีข้อมูลตารางคะแนน"
    return build_standings_flex(standings_groups)

def build_upcoming() -> Any:
    data = svc.fetch(f"competitions/{ACTIVE_COMPETITION}/matches?status=SCHEDULED", ttl=300)
    if not isinstance(data, dict): return "📭 ตอนนี้ไม่มีโปรแกรมการแข่งขัน"
    matches = data.get("matches", [])
    if not matches: return "📭 ตอนนี้ไม่มีโปรแกรมการแข่งขัน"
    matches.sort(key=lambda m: m.get("utcDate", ""))
    return build_upcoming_flex(matches)

def build_scorers() -> Any:
    data = svc.fetch(f"competitions/{ACTIVE_COMPETITION}/scorers", ttl=14400)
    if not isinstance(data, dict): return "📭 ยังไม่มีข้อมูลดาวซัลโว"
    scorers = data.get("scorers", [])
    if not scorers: return "📭 ยังไม่มีข้อมูลดาวซัลโว"
    return build_scorers_flex(scorers)

COMMAND_MAP = [
    (("สด", "live"), build_live_scores),
    (("ตาราง", "table", "standing"), build_standings),
    (("ผล", "ผลบอล", "result"), build_recent_results),
    (("โปรแกรม", "fixture", "นัดถัดไป"), build_upcoming),
    (("ดาวซัลโว", "scorer", "scorers", "รองเท้าทองคำ"), build_scorers),
]

def handle_command(cmd_text: str) -> Any:
    cmd = cmd_text.strip().lower()
    for keys, func in COMMAND_MAP:
        if any(k in cmd for k in keys):
            return func()
    return build_help_text()
