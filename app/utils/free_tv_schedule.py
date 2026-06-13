# -*- coding: utf-8 -*-
"""
16 คู่ดูฟรี ที่ช่อง 29 Monomax Sports (FIFA World Cup 2026)
ข้อมูลจากตารางถ่ายทอดสดฟรี ช่อง 29 โมโนแม็กซ์ สปอร์ต
"""

from datetime import date

# Each entry: (date, time_str, home_th, away_th, home_en, away_en)
# home_en / away_en used for matching with API team names
FREE_TV_MATCHES = [
    # ---- Column 1 (Left) ----
    (date(2026, 6, 13), "08.00 น.", "อเมริกา", "ปารากวัย", "United States", "Paraguay"),
    (date(2026, 6, 14), "05.00 น.", "บราซิล", "โมร็อคโค", "Brazil", "Morocco"),
    (date(2026, 6, 15), "00.00 น.", "เยอรมัน", "คูราเซา", "Germany", "Curaçao"),
    (date(2026, 6, 15), "23.00 น.", "สเปน", "เคปเวิร์ด", "Spain", "Cape Verde"),
    (date(2026, 6, 17), "08.00 น.", "อาร์เจนตินา", "อัลจีเรีย", "Argentina", "Algeria"),
    (date(2026, 6, 18), "00.00 น.", "โปรตุเกส", "คองโก", "Portugal", "DR Congo"),
    (date(2026, 6, 19), "08.00 น.", "เม็กซิโก", "เกาหลีใต้", "Mexico", "Korea Republic"),
    (date(2026, 6, 20), "10.00 น.", "ตุรกี", "ปารากวัย", "Türkiye", "Paraguay"),
    # ---- Column 2 (Right) ----
    (date(2026, 6, 21), "11.00 น.", "ตูนีเซีย", "ญี่ปุ่น", "Tunisia", "Japan"),
    (date(2026, 6, 22), "08.00 น.", "นิวซีแลนด์", "อียิปต์", "New Zealand", "Egypt"),
    (date(2026, 6, 23), "07.00 น.", "นอร์เวย์", "เซเนกัล", "Norway", "Senegal"),
    (date(2026, 6, 24), "03.00 น.", "อังกฤษ", "กานา", "England", "Ghana"),
    (date(2026, 6, 25), "08.00 น.", "อาร์เจนตินา", "อัลจีเรีย", "Argentina", "Algeria"),
    (date(2026, 6, 26), "06.00 น.", "ตูนีเซีย", "ฮอลแลนด์", "Tunisia", "Netherlands"),
    (date(2026, 6, 27), "10.00 น.", "นิวซีแลนด์", "เบลเยียม", "New Zealand", "Belgium"),
]

# Matches on 25 มิ.ย. might be a duplicate or different round — kept as provided in schedule


def get_free_tv_matches_for_date(target_date: date) -> list:
    """Return all free-to-watch matches for the given date."""
    return [m for m in FREE_TV_MATCHES if m[0] == target_date]


def format_free_tv_section(target_date: date) -> str | None:
    """
    Format a prominent free TV section for the morning greeting.
    Returns None if there are no free matches today.
    """
    today_free = get_free_tv_matches_for_date(target_date)
    if not today_free:
        return None

    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "📺✨ คู่ดูฟรี! ช่อง 29 Monomax Sports ✨📺",
        "━━━━━━━━━━━━━━━━━━━━━",
    ]
    for _, time_str, home_th, away_th, _home_en, _away_en in today_free:
        lines.append(f"🆓 {time_str}  {home_th} 🆚 {away_th}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 ดูฟรีไม่ต้องสมัครสมาชิก!")
    lines.append("")

    return "\n".join(lines)


def is_free_tv_match(home_en: str, away_en: str, match_date: date) -> bool:
    """Check if a specific match (by English team names) is a free-to-watch match."""
    home_lower = home_en.strip().lower()
    away_lower = away_en.strip().lower()
    for m_date, _, _, _, m_home_en, m_away_en in FREE_TV_MATCHES:
        if m_date == match_date:
            if (m_home_en.lower() in home_lower or home_lower in m_home_en.lower()) and \
               (m_away_en.lower() in away_lower or away_lower in m_away_en.lower()):
                return True
    return False
