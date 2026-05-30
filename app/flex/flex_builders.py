from datetime import datetime
from app.config import Config
from app.utils.helpers import safe_url
from app.utils.constants import WATCHED_TEAMS, EPL_LOGO, WC_LOGO, WC_CODE, ACTIVE_COMPETITION
from app.utils.aliases import FlexDict

def build_goal_flex(h_name: str, a_name: str, hs: int, as_: int,
                    h_logo: str, a_logo: str, scorer: str = "", minute: str = "",
                    comp_code: str = "PL") -> FlexDict:
    # Theme configuration
    if comp_code == WC_CODE:
        header_bg = "#7F0F25"          # Premium Crimson Red for World Cup
        header_text = "🏆 FIFA WORLD CUP"
        header_text_color = "#D4AF37"  # Gold text
        badge_logo = WC_LOGO
        goal_color = "#D4AF37"
    else:
        header_bg = "#38003c"          # EPL Purple
        header_text = "⚽ PREMIER LEAGUE"
        header_text_color = "#FFFFFF"
        badge_logo = EPL_LOGO
        goal_color = "#e11d48"

    scorer_line = []
    if scorer:
        scorer_line = [{"type": "text", "text": f"⚽ {scorer} {minute}'",
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
                        {"type": "image", "url": safe_url(h_logo), "size": "sm", "flex": 2},
                        {"type": "text", "text": str(hs), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "text", "text": "-", "size": "xxl", "weight": "bold", "align": "center", "flex": 0},
                        {"type": "text", "text": str(as_), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "image", "url": safe_url(a_logo), "size": "sm", "flex": 2},
                    ]
                },
                {"type": "text", "text": f"{h_name}  vs  {a_name}",
                 "margin": "md", "align": "center", "color": "#666666", "size": "sm"},
                *scorer_line,
            ]
        }
    }

def build_var_flex(h_name: str, a_name: str, hs: int, as_: int, h_logo: str, a_logo: str, scorer: str = "",
                   comp_code: str = "PL") -> FlexDict:
    sub_text = f"Goal by {scorer} disallowed after review" if scorer else "Goal disallowed after review"
    
    # Theme configuration
    if comp_code == WC_CODE:
        header_bg = "#7F0F25"
        header_text = "🏆 FIFA WORLD CUP"
        header_text_color = "#D4AF37"
        badge_logo = WC_LOGO
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
                        {"type": "image", "url": safe_url(h_logo), "size": "sm", "flex": 2},
                        {"type": "text", "text": str(hs), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "text", "text": "-", "size": "xxl", "weight": "bold", "align": "center", "flex": 0},
                        {"type": "text", "text": str(as_), "size": "xxl", "weight": "bold", "align": "center", "flex": 1},
                        {"type": "image", "url": safe_url(a_logo), "size": "sm", "flex": 2},
                    ]
                },
                {"type": "text", "text": f"{h_name}  vs  {a_name}",
                 "margin": "md", "align": "center", "color": "#666666", "size": "sm"}
            ]
        }
    }

def build_standings_flex(standings_groups) -> FlexDict:
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
        is_fav   = any(f.lower() in name.lower() for f in WATCHED_TEAMS)
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
                        {"type": "image", "url": safe_url(logo), "size": "xxs", "flex": 0},
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
    header_color = "#7F0F25" if is_wc else "#3D195B"
    header_title = "FIFA WORLD CUP" if is_wc else "PREMIER LEAGUE"

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
            "contents": [{"type": "text", "text": f"Updated: {datetime.now(Config.TZ).strftime('%H:%M')}",
                           "size": "xxs", "align": "center", "color": "#aaaaaa"}]
        }
    }

def build_upcoming_flex(matches) -> FlexDict:
    rows = []
    for m in matches[:10]:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        utc_str = m.get("utcDate", "")
        try:
            dt_utc  = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            dt_bkk  = dt_utc.astimezone(Config.TZ)
            bkk_time = dt_bkk.strftime("%d/%m %H:%M น.")
        except Exception:
            bkk_time = utc_str

        h_logo = m["homeTeam"].get("crest", "")
        a_logo = m["awayTeam"].get("crest", "")

        rows.append({
            "type": "box", "layout": "vertical", "margin": "md",
            "contents": [
                {"type": "text", "text": f"🕐 {bkk_time}", "size": "xs", "color": "#888888"},
                {
                    "type": "box", "layout": "horizontal", "margin": "sm", "alignItems": "center",
                    "contents": [
                        {"type": "image", "url": safe_url(h_logo), "size": "xxs", "flex": 0},
                        {"type": "text", "text": home, "size": "sm", "flex": 3, "margin": "sm"},
                        {"type": "text", "text": "vs", "size": "sm", "flex": 1, "align": "center", "color": "#888888"},
                        {"type": "text", "text": away, "size": "sm", "flex": 3, "align": "end", "margin": "sm"},
                        {"type": "image", "url": safe_url(a_logo), "size": "xxs", "flex": 0},
                    ]
                },
                {"type": "separator", "margin": "md"},
            ]
        })

    is_wc = ACTIVE_COMPETITION == WC_CODE
    header_color = "#7F0F25" if is_wc else "#38003c"
    header_title = "🏆 WORLD CUP FIXTURES" if is_wc else "📅 EPL FIXTURES"

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [{"type": "text", "text": header_title,
                          "color": "#ffffff", "weight": "bold", "size": "md", "align": "center"}]
        },
        "body": {"type": "box", "layout": "vertical", "contents": rows},
    } rows},
    }
