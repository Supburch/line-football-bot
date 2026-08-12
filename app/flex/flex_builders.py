from datetime import datetime
from app.config import Config
from app.utils.helpers import safe_url, format_minute, is_exact_team_match
from app.utils.constants import WATCHED_TEAMS, WATCHED_COUNTRIES, EPL_LOGO, WC_LOGO, WC_CODE, UCL_LOGO, UCL_CODE, ACTIVE_COMPETITION, COUNTDOWN_COVER, STAGE_TRANSLATION
from app.utils.aliases import FlexDict
from app.utils.free_tv_schedule import is_free_tv_match
from app.services.line_service import get_remaining_quota_text

def build_goal_flex(h_name: str, a_name: str, hs: int, as_: int,
                    h_logo: str, a_logo: str, scorer: str = "", minute: object = None,
                    comp_code: str = "PL") -> FlexDict:
    # Theme configuration
    if comp_code == WC_CODE:
        header_bg = "#7F0F25"          # Premium Crimson Red for World Cup
        header_text = "🏆 FIFA WORLD CUP"
        header_text_color = "#D4AF37"  # Gold text
        badge_logo = WC_LOGO
        goal_color = "#D4AF37"
    elif comp_code == UCL_CODE:
        header_bg = "#0B1E36"          # UCL Midnight Blue
        header_text = "⭐ UEFA CHAMPIONS LEAGUE"
        header_text_color = "#D4AF37"  # Gold text
        badge_logo = UCL_LOGO
        goal_color = "#3A86FF"         # UCL Electric Blue
    else:
        header_bg = "#38003c"          # EPL Purple
        header_text = "⚽ PREMIER LEAGUE"
        header_text_color = "#FFFFFF"
        badge_logo = EPL_LOGO
        goal_color = "#e11d48"

    scorer_line = []
    if scorer:
        min_text = format_minute(minute)
        display_time = f" {min_text}" if min_text else ""
        scorer_line = [{"type": "text", "text": f"⚽ {scorer}{display_time}",
                        "size": "sm", "align": "center", "color": "#1a1a1a", "margin": "sm"}]
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "horizontal", "backgroundColor": header_bg,
            "paddingAll": "md", "alignItems": "center",
            "contents": [
                {"type": "image", "url": safe_url(badge_logo), "size": "xxs", "flex": 0},
                {"type": "text", "text": header_text, "weight": "bold",
                 "color": header_text_color, "size": "sm", "margin": "md", "flex": 1}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "⚽ GOAL!!!", "weight": "bold",
                 "color": goal_color, "size": "xl", "align": "center"},
                {
                    "type": "box", "layout": "horizontal", "margin": "lg", "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(h_logo, h_name), "size": "sm", "flex": 2},
                        {"type": "text", "text": str(hs), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "text", "text": "-", "size": "xxl", "weight": "bold", "align": "center", "flex": 0},
                        {"type": "text", "text": str(as_), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "image", "url": safe_url(a_logo, a_name), "size": "sm", "flex": 2},
                    ]
                },
                {"type": "text", "text": f"{h_name}  vs  {a_name}",
                 "margin": "md", "align": "center", "color": "#666666", "size": "sm"},
                *scorer_line,
            ]
        }
    }

def build_var_flex(h_name: str, a_name: str, hs: int, as_: int, h_logo: str, a_logo: str, scorer: str = "",
                   minute: object = None, comp_code: str = "PL") -> FlexDict:
    min_text = format_minute(minute)
    if scorer and min_text:
        sub_text = f"Goal by {scorer} disallowed after review ({min_text})"
    elif scorer:
        sub_text = f"Goal by {scorer} disallowed after review"
    else:
        sub_text = "Goal disallowed after review"
    
    # Theme configuration
    if comp_code == WC_CODE:
        header_bg = "#7F0F25"
        header_text = "🏆 FIFA WORLD CUP"
        header_text_color = "#D4AF37"
        badge_logo = WC_LOGO
        var_color = "#ef4444"
    elif comp_code == UCL_CODE:
        header_bg = "#0B1E36"
        header_text = "⭐ UEFA CHAMPIONS LEAGUE"
        header_text_color = "#D4AF37"
        badge_logo = UCL_LOGO
        var_color = "#ef4444"
    else:
        header_bg = "#38003c"
        header_text = "⚽ PREMIER LEAGUE"
        header_text_color = "#FFFFFF"
        badge_logo = EPL_LOGO
        var_color = "#ef4444"

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "horizontal", "backgroundColor": header_bg,
            "paddingAll": "md", "alignItems": "center",
            "contents": [
                {"type": "image", "url": safe_url(badge_logo), "size": "xxs", "flex": 0},
                {"type": "text", "text": header_text, "weight": "bold",
                 "color": header_text_color, "size": "sm", "margin": "md", "flex": 1}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "❌ VAR: NO GOAL!", "weight": "bold",
                 "color": var_color, "size": "xl", "align": "center"},
                {"type": "text", "text": sub_text, "size": "xs", "align": "center", "color": "#888888", "margin": "sm"},
                {
                    "type": "box", "layout": "horizontal", "margin": "lg", "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(h_logo, h_name), "size": "sm", "flex": 2},
                        {"type": "text", "text": str(hs), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "text", "text": "-", "size": "xxl", "weight": "bold", "align": "center", "flex": 0},
                        {"type": "text", "text": str(as_), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "image", "url": safe_url(a_logo, a_name), "size": "sm", "flex": 2},
                    ]
                },
                {"type": "text", "text": f"{h_name}  vs  {a_name}",
                 "margin": "md", "align": "center", "color": "#666666", "size": "sm"}
            ]
        }
    }

def build_penalty_shootout_flex(h_name: str, a_name: str, hs: int, as_: int,
                                pen_hs: int, pen_as: int, h_logo: str, a_logo: str,
                                scorer_text: str = "", comp_code: str = "PL") -> FlexDict:
    if comp_code == WC_CODE:
        header_bg = "#7F0F25"
        header_text = "🏆 FIFA WORLD CUP"
        header_text_color = "#D4AF37"
        badge_logo = WC_LOGO
        shootout_color = "#D4AF37"
    elif comp_code == UCL_CODE:
        header_bg = "#0B1E36"
        header_text = "⭐ UEFA CHAMPIONS LEAGUE"
        header_text_color = "#D4AF37"
        badge_logo = UCL_LOGO
        shootout_color = "#3A86FF"
    else:
        header_bg = "#38003c"
        header_text = "⚽ PREMIER LEAGUE"
        header_text_color = "#FFFFFF"
        badge_logo = EPL_LOGO
        shootout_color = "#e11d48"

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "horizontal", "backgroundColor": header_bg,
            "paddingAll": "md", "alignItems": "center",
            "contents": [
                {"type": "image", "url": safe_url(badge_logo), "size": "xxs", "flex": 0},
                {"type": "text", "text": header_text, "weight": "bold",
                 "color": header_text_color, "size": "sm", "margin": "md", "flex": 1}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🎯 PENALTY SHOOTOUT", "weight": "bold",
                 "color": shootout_color, "size": "lg", "align": "center"},
                {
                    "type": "box", "layout": "horizontal", "margin": "lg", "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(h_logo, h_name), "size": "sm", "flex": 2},
                        {
                            "type": "box", "layout": "vertical", "flex": 3, "alignItems": "center",
                            "contents": [
                                {"type": "text", "text": f"{hs} - {as_}", "size": "xl", "weight": "bold", "align": "center"},
                                {"type": "text", "text": f"PSO: {pen_hs} - {pen_as}", "size": "sm", "weight": "bold", "color": "#888888", "margin": "xs"}
                            ]
                        },
                        {"type": "image", "url": safe_url(a_logo, a_name), "size": "sm", "flex": 2},
                    ]
                },
                {"type": "text", "text": f"{h_name}  vs  {a_name}",
                 "margin": "md", "align": "center", "color": "#666666", "size": "sm"},
                {"type": "text", "text": scorer_text, "size": "sm", "align": "center", "weight": "bold", "color": "#1a1a1a", "margin": "md"}
            ]
        }
    }

def build_red_card_flex(h_name: str, a_name: str, hs: int, as_: int, h_logo: str, a_logo: str,
                        player: str = "", team: str = "", minute: object = None,
                        card_type: str = "RED_CARD", comp_code: str = "PL") -> FlexDict:
    """Build a flex message for red card notifications."""
    # Theme configuration
    if comp_code == WC_CODE:
        header_bg = "#7F0F25"
        header_text = "🏆 FIFA WORLD CUP"
        header_text_color = "#D4AF37"
        badge_logo = WC_LOGO
    elif comp_code == UCL_CODE:
        header_bg = "#0B1E36"
        header_text = "⭐ UEFA CHAMPIONS LEAGUE"
        header_text_color = "#D4AF37"
        badge_logo = UCL_LOGO
    else:
        header_bg = "#38003c"
        header_text = "⚽ PREMIER LEAGUE"
        header_text_color = "#FFFFFF"
        badge_logo = EPL_LOGO

    # Card label
    if card_type == "YELLOW_RED_CARD":
        card_emoji = "🟨🟥"
        card_label = "ใบเหลือง-แดง!"
    else:
        card_emoji = "🟥"
        card_label = "ใบแดง!"

    min_text = format_minute(minute)
    detail_parts = []
    if player:
        detail_parts.append(player)
    if team:
        detail_parts.append(f"({team})")
    if min_text:
        detail_parts.append(f"นาทีที่ {min_text}")
    detail_text = "  ".join(detail_parts) if detail_parts else "ผู้เล่นโดนใบแดง"

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "horizontal", "backgroundColor": header_bg,
            "paddingAll": "md", "alignItems": "center",
            "contents": [
                {"type": "image", "url": safe_url(badge_logo), "size": "xxs", "flex": 0},
                {"type": "text", "text": header_text, "weight": "bold",
                 "color": header_text_color, "size": "sm", "margin": "md", "flex": 1}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"{card_emoji} {card_label}", "weight": "bold",
                 "color": "#DC2626", "size": "xl", "align": "center"},
                {"type": "text", "text": detail_text,
                 "size": "sm", "align": "center", "color": "#444444", "margin": "sm", "wrap": True},
                {
                    "type": "box", "layout": "horizontal", "margin": "lg", "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(h_logo, h_name), "size": "sm", "flex": 2},
                        {"type": "text", "text": str(hs), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "text", "text": "-", "size": "xxl", "weight": "bold", "align": "center", "flex": 0},
                        {"type": "text", "text": str(as_), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "image", "url": safe_url(a_logo, a_name), "size": "sm", "flex": 2},
                    ]
                },
                {"type": "text", "text": f"{h_name}  vs  {a_name}",
                 "margin": "md", "align": "center", "color": "#666666", "size": "sm"}
            ]
        }
    }

def make_group_box(group_data) -> dict:
    group_name = group_data.get("group", "Unknown Group").replace("GROUP_", "GROUP ")
    table = group_data.get("table", [])
    
    rows = [
        # Group Header
        {
            "type": "box", "layout": "vertical", "margin": "md", "contents": [
                {"type": "text", "text": group_name, "weight": "bold", "color": "#D4AF37", "size": "md", "margin": "sm"},
                {"type": "separator", "margin": "sm", "color": "#D4AF37"}
            ]
        },
        # Headers
        {
            "type": "box", "layout": "horizontal", "margin": "sm",
            "contents": [
                {"type": "text", "text": "#",    "weight": "bold", "size": "xs", "flex": 1, "align": "center"},
                {"type": "text", "text": "Team", "weight": "bold", "size": "xs", "flex": 4},
                {"type": "text", "text": "P",    "weight": "bold", "size": "xs", "align": "center", "flex": 1},
                {"type": "text", "text": "GD",   "weight": "bold", "size": "xs", "align": "center", "flex": 1},
                {"type": "text", "text": "Pts",  "weight": "bold", "size": "xs", "align": "end", "flex": 2, "margin": "sm"},
            ]
        },
        {"type": "separator", "margin": "xs"},
    ]
    
    for t in table:
        pos    = t.get("position", "-")
        name   = t.get("team", {}).get("name", "Unknown")
        played = t.get("playedGames", 0)
        gd     = t.get("goalDifference", 0)
        pts    = t.get("points", 0)
        logo   = t.get("team", {}).get("crest", "")
        
        gd_text  = f"+{gd}" if gd > 0 else str(gd)
        is_fav   = is_exact_team_match(name, WATCHED_COUNTRIES)
        bg_color = "#F0F9FF" if is_fav else "#FFFFFF"
        
        rows.append({
            "type": "box", "layout": "horizontal", "margin": "xs",
            "alignItems": "center", "backgroundColor": bg_color,
            "cornerRadius": "sm", "paddingAll": "xs",
            "contents": [
                {"type": "text", "text": str(pos), "size": "xs", "flex": 1, "align": "center", "color": "#888888"},
                {
                    "type": "box", "layout": "horizontal", "flex": 4, "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(logo, name), "size": "xxs", "flex": 0},
                        {"type": "text", "text": name, "size": "xs", "margin": "sm", "flex": 1,
                         "weight": "bold" if is_fav else "regular", "wrap": True},
                    ]
                },
                {"type": "text", "text": str(played), "size": "xs", "align": "center", "flex": 1},
                {"type": "text", "text": gd_text,     "size": "xs", "align": "center", "flex": 1, "color": "#666666"},
                {"type": "text", "text": str(pts),    "size": "xs", "align": "end", "weight": "bold", "flex": 2, "margin": "sm"},
            ]
        })
        
    return {"type": "box", "layout": "vertical", "contents": rows}

def build_standings_flex(standings_groups) -> FlexDict:
    is_group_based = any(s.get("group") is not None for s in standings_groups)
    
    if is_group_based:
        total_standings = [s for s in standings_groups if s.get("type") == "TOTAL"]
        total_standings.sort(key=lambda s: s.get("group", ""))
        
        bubbles = []
        for i in range(0, len(total_standings), 2):
            pair = total_standings[i:i+2]
            
            pair_names = []
            contents = []
            for s in pair:
                group_clean = s.get("group", "").replace("GROUP_", "Group ")
                pair_names.append(group_clean)
                contents.append(make_group_box(s))
                
            header_title = "🏆 WORLD CUP - " + " & ".join(pair_names)
            
            bubbles.append({
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical", "backgroundColor": "#7F0F25",
                    "contents": [
                        {"type": "text", "text": header_title, "weight": "bold", "color": "#D4AF37", "size": "sm"},
                    ]
                },
                "body": {
                    "type": "box", "layout": "vertical", "paddingAll": "md",
                    "contents": contents
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": f"Updated: {datetime.now(Config.TZ).strftime('%H:%M')}",
                         "size": "xxs", "align": "center", "color": "#aaaaaa"},
                        {"type": "text", "text": get_remaining_quota_text(),
                         "size": "xxs", "align": "center", "color": "#aaaaaa", "margin": "xs"}
                    ]
                }
            })
            
        return {
            "type": "carousel",
            "contents": bubbles
        }

    total = next((s for s in standings_groups if s.get("type") == "TOTAL"), standings_groups[0])
    table = total.get("table", [])

    rows = [
        {
            "type": "box", "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "#",    "weight": "bold", "size": "xs", "flex": 1, "align": "center"},
                {"type": "text", "text": "Team", "weight": "bold", "size": "xs", "flex": 4},
                {"type": "text", "text": "P",    "weight": "bold", "size": "xs", "align": "center", "flex": 1},
                {"type": "text", "text": "GD",   "weight": "bold", "size": "xs", "align": "center", "flex": 1},
                {"type": "text", "text": "Pts",  "weight": "bold", "size": "xs", "align": "end", "flex": 2, "margin": "md"},
            ]
        },
        {"type": "separator", "margin": "sm"},
    ]

    for t in table:
        pos    = t.get("position", "-")
        name   = t.get("team", {}).get("name", "Unknown")
        played = t.get("playedGames", 0)
        gd     = t.get("goalDifference", 0)
        pts    = t.get("points", 0)
        logo   = t.get("team", {}).get("crest", "")

        gd_text  = f"+{gd}" if gd > 0 else str(gd)
        is_fav   = is_exact_team_match(name, WATCHED_TEAMS)
        bg_color = "#F0F9FF" if is_fav else "#FFFFFF"

        rows.append({
            "type": "box", "layout": "horizontal", "margin": "xs",
            "alignItems": "center", "backgroundColor": bg_color,
            "cornerRadius": "sm", "paddingAll": "xs",
            "contents": [
                {"type": "text", "text": str(pos), "size": "xs", "flex": 1, "align": "center", "color": "#888888"},
                {
                    "type": "box", "layout": "horizontal", "flex": 4, "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(logo, name), "size": "xxs", "flex": 0},
                        {"type": "text", "text": name, "size": "xs", "margin": "sm", "flex": 1,
                         "weight": "bold" if is_fav else "regular", "wrap": True},
                    ]
                },
                {"type": "text", "text": str(played), "size": "xs", "align": "center", "flex": 1},
                {"type": "text", "text": gd_text,     "size": "xs", "align": "center", "flex": 1, "color": "#666666"},
                {"type": "text", "text": str(pts),    "size": "xs", "align": "end", "weight": "bold", "flex": 2, "margin": "md"},
            ]
        })

    is_wc = ACTIVE_COMPETITION == WC_CODE
    is_ucl = ACTIVE_COMPETITION == UCL_CODE
    if is_wc:
        header_color = "#7F0F25"
        header_title = "FIFA WORLD CUP"
    elif is_ucl:
        header_color = "#0B1E36"
        header_title = "UEFA CHAMPIONS LEAGUE"
    else:
        header_color = "#3D195B"
        header_title = "PREMIER LEAGUE"

    return {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [
                {"type": "text", "text": header_title, "weight": "bold", "color": "#ffffff", "size": "sm"},
                {"type": "text", "text": "Standings",  "weight": "bold", "color": "#ffffff", "size": "xl"},
            ]
        },
        "body": {"type": "box", "layout": "vertical", "paddingAll": "md", "contents": rows},
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"Updated: {datetime.now(Config.TZ).strftime('%H:%M')}",
                 "size": "xxs", "align": "center", "color": "#aaaaaa"},
                {"type": "text", "text": get_remaining_quota_text(),
                 "size": "xxs", "align": "center", "color": "#aaaaaa", "margin": "xs"}
            ]
        }
    }

def build_upcoming_flex(matches) -> FlexDict:
    rows = []
    has_free = False
    for m in matches[:10]:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        utc_str = m.get("utcDate", "")
        try:
            dt_utc  = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            dt_bkk  = dt_utc.astimezone(Config.TZ)
            bkk_time = dt_bkk.strftime("%d/%m %H:%M น.")
            match_date = dt_bkk.date()
        except Exception:
            bkk_time = utc_str
            match_date = None

        h_logo = m["homeTeam"].get("crest", "")
        a_logo = m["awayTeam"].get("crest", "")

        stage_raw = m.get("stage", "")
        stage_th = STAGE_TRANSLATION.get(stage_raw, "")
        stage_text = f" ({stage_th})" if stage_th else ""

        # Check if this match is free-to-watch
        is_free = match_date and is_free_tv_match(home, away, match_date)
        if is_free:
            has_free = True

        # Time label with free TV badge
        time_label = f"🆓 {bkk_time}{stage_text}  📺 ช่อง29" if is_free else f"🕐 {bkk_time}{stage_text}"
        time_color = "#16a34a" if is_free else "#888888"
        row_bg = "#F0FFF4" if is_free else "#FFFFFF"

        rows.append({
            "type": "box", "layout": "vertical", "margin": "md",
            "backgroundColor": row_bg, "cornerRadius": "md", "paddingAll": "sm",
            "contents": [
                {"type": "text", "text": time_label, "size": "xs", "color": time_color, "weight": "bold" if is_free else "regular"},
                {
                    "type": "box", "layout": "horizontal", "margin": "sm", "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(h_logo, home), "size": "xxs", "flex": 0},
                        {"type": "text", "text": home, "size": "sm", "flex": 3, "margin": "sm"},
                        {"type": "text", "text": "vs", "size": "sm", "flex": 1, "align": "center", "color": "#888888"},
                        {"type": "text", "text": away, "size": "sm", "flex": 3, "align": "end", "margin": "sm"},
                        {"type": "image", "url": safe_url(a_logo, away), "size": "xxs", "flex": 0},
                    ]
                },
                {"type": "separator", "margin": "md"},
            ]
        })

    is_wc = ACTIVE_COMPETITION == WC_CODE
    is_ucl = ACTIVE_COMPETITION == UCL_CODE
    if is_wc:
        header_color = "#7F0F25"
        header_title = "🏆 WORLD CUP FIXTURES"
    elif is_ucl:
        header_color = "#0B1E36"
        header_title = "⭐ UCL FIXTURES"
    else:
        header_color = "#38003c"
        header_title = "📅 EPL FIXTURES"

    # Footer with free TV legend if any matches are free
    footer_contents = []
    if has_free:
        footer_contents.append({"type": "text", "text": "🆓 = ดูฟรี ช่อง 29 Monomax Sports", "size": "xs", "align": "center", "color": "#16a34a", "weight": "bold"})
    footer_contents.append({"type": "text", "text": f"Updated: {datetime.now(Config.TZ).strftime('%H:%M')}",
                             "size": "xxs", "align": "center", "color": "#aaaaaa"})
    footer_contents.append({"type": "text", "text": get_remaining_quota_text(),
                             "size": "xxs", "align": "center", "color": "#aaaaaa", "margin": "xs"})

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [{"type": "text", "text": header_title,
                          "color": "#ffffff", "weight": "bold", "size": "md", "align": "center"}]
        },
        "body": {"type": "box", "layout": "vertical", "contents": rows},
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": footer_contents
        },
    }

def build_scorers_flex(scorers) -> FlexDict:
    rows = [
        # Table Header
        {
            "type": "box", "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "#",      "weight": "bold", "size": "xs", "flex": 1, "align": "center"},
                {"type": "text", "text": "Player", "weight": "bold", "size": "xs", "flex": 4},
                {"type": "text", "text": "Team",   "weight": "bold", "size": "xs", "flex": 3},
                {"type": "text", "text": "Goals",  "weight": "bold", "size": "xs", "align": "end", "flex": 2},
            ]
        },
        {"type": "separator", "margin": "sm"},
    ]
    
    for idx, s in enumerate(scorers[:10], start=1):
        player_name = s.get("player", {}).get("name", "Unknown")
        team_name = s.get("team", {}).get("name", "Unknown")
        team_logo = s.get("team", {}).get("crest", "")
        goals = s.get("goals", 0)
        
        rows.append({
            "type": "box", "layout": "horizontal", "margin": "md",
            "alignItems": "center",
            "contents": [
                {"type": "text", "text": str(idx), "size": "xs", "flex": 1, "align": "center", "color": "#888888"},
                {"type": "text", "text": player_name, "size": "xs", "flex": 4, "weight": "bold", "wrap": True},
                {
                    "type": "box", "layout": "horizontal", "flex": 3, "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(team_logo, team_name), "size": "xxs", "flex": 0},
                        {"type": "text", "text": team_name, "size": "xs", "margin": "sm", "flex": 1, "wrap": True}
                    ]
                },
                {"type": "text", "text": str(goals), "size": "sm", "align": "end", "weight": "bold", "flex": 2, "color": "#D4AF37" if ACTIVE_COMPETITION in (WC_CODE, UCL_CODE) else "#e11d48"}
            ]
        })
        rows.append({"type": "separator", "margin": "sm"})
        
    is_wc = ACTIVE_COMPETITION == WC_CODE
    is_ucl = ACTIVE_COMPETITION == UCL_CODE
    if is_wc:
        header_color = "#7F0F25"
        header_title = "🏆 WORLD CUP TOP SCORERS"
    elif is_ucl:
        header_color = "#0B1E36"
        header_title = "⭐ UCL TOP SCORERS"
    else:
        header_color = "#38003c"
        header_title = "⚽ EPL TOP SCORERS"
    
    return {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [
                {"type": "text", "text": header_title, "weight": "bold", "color": "#D4AF37" if is_wc else "#ffffff", "size": "sm"},
                {"type": "text", "text": "Top Scorers Leaderboard", "weight": "bold", "color": "#ffffff", "size": "xl"},
            ]
        },
        "body": {"type": "box", "layout": "vertical", "paddingAll": "md", "contents": rows},
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"Updated: {datetime.now(Config.TZ).strftime('%H:%M')}",
                 "size": "xxs", "align": "center", "color": "#aaaaaa"},
                {"type": "text", "text": get_remaining_quota_text(),
                 "size": "xxs", "align": "center", "color": "#aaaaaa", "margin": "xs"}
            ]
        }
    }

def build_countdown_flex(days_left: int) -> FlexDict:
    return {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "position": "relative",
            "contents": [
                # Background Cover Image (1:1 Square edge-to-edge)
                {
                    "type": "image",
                    "url": safe_url(COUNTDOWN_COVER),
                    "size": "full",
                    "aspectMode": "cover",
                    "aspectRatio": "1:1"
                },
                # Dynamic Overlay: Large Black Number inside the gold card's blank left area
                {
                    "type": "box",
                    "layout": "vertical",
                    "position": "absolute",
                    "offsetBottom": "17px",
                    "offsetStart": "25%",
                    "offsetEnd": "35%",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{days_left}",
                            "size": "3xl",
                            "color": "#000000",
                            "weight": "bold",
                            "align": "center"
                        }
                    ]
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#7F0F25",
            "paddingAll": "md",
            "contents": [
                {
                    "type": "text",
                    "text": f"🏆 อีก {days_left} วัน สู่ FIFA WORLD CUP 2026!",
                    "color": "#D4AF37",
                    "align": "center",
                    "weight": "bold",
                    "size": "sm"
                }
            ]
        }
    }
