from datetime import datetime
from app.config import Config
from app.utils.helpers import safe_url
from app.utils.constants import WATCHED_TEAMS
from app.utils.aliases import FlexDict

def build_goal_flex(h_name: str, a_name: str, hs: int, as_: int,
                    h_logo: str, a_logo: str, scorer: str = "", minute: str = "") -> FlexDict:
    scorer_line = []
    if scorer:
        scorer_line = [{"type": "text", "text": f"⚽ {scorer} {minute}'",
                        "size": "sm", "align": "center", "color": "#1a1a1a", "margin": "sm"}]
    return {
        "type": "bubble",
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "⚽ GOAL!!!", "weight": "bold",
                 "color": "#e11d48", "size": "xl", "align": "center"},
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

    return {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#3D195B",
            "contents": [
                {"type": "text", "text": "PREMIER LEAGUE", "weight": "bold", "color": "#ffffff", "size": "sm"},
                {"type": "text", "text": "Full Standings",  "weight": "bold", "color": "#ffffff", "size": "xl"},
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

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#38003c",
            "contents": [{"type": "text", "text": "📅 EPL FIXTURES",
                          "color": "#ffffff", "weight": "bold", "size": "md", "align": "center"}]
        },
        "body": {"type": "box", "layout": "vertical", "contents": rows},
    }
