# controller.py — Flask API routes

from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
import os
import json
import urllib.request

from model import load_all_data, train_model, ALL_SEASONS
from service import predict_match, simulate_season
from logger import log_event

app = Flask(__name__)
CORS(app)

# ─── Bootstrap ───────────────────────────────────────────────────────────────
print("\n  Booting Premier League Predictor...")
_data                                         = load_all_data()
_rf, _target_enc, _label_enc, _team_hist, _feat_cols = train_model(_data)

CURRENT_SEASON = "2026-2027"

ALL_TEAMS = sorted([
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Coventry", "Crystal Palace", "Everton", "Fulham",
    "Hull", "Ipswich", "Liverpool", "Manchester City", "Manchester United",
    "Newcastle", "Nottingham Forest", "Tottenham", "Leeds", "Sunderland",
])

# Teams promoted to PL this season — shown in the season sim sidebar
PROMOTED_TEAMS = ["Coventry", "Ipswich", "Hull"]

TEAM_BADGES = {
    "Arsenal":            "https://www.thesportsdb.com/images/media/team/badge/uyhbfe1612467038.png",
    "Aston Villa":        "https://www.thesportsdb.com/images/media/team/badge/jykrpv1717309891.png",
    "Bournemouth":        "https://www.thesportsdb.com/images/media/team/badge/y08nak1534071116.png",
    "Brentford":          "https://www.thesportsdb.com/images/media/team/badge/grv1aw1546453779.png",
    "Brighton":           "https://www.thesportsdb.com/images/media/team/badge/ywypts1448810904.png",
    "Chelsea":            "https://www.thesportsdb.com/images/media/team/badge/yvwvtu1448813215.png",
    "Coventry":           "https://www.thesportsdb.com/images/media/team/badge/KHpmY4tIwqiutl8Cfl0MAw_500x500.png",
    "Crystal Palace":     "https://www.thesportsdb.com/images/media/team/badge/ia6i3m1656014992.png",
    "Everton":            "https://www.thesportsdb.com/images/media/team/badge/eqayrf1523184794.png",
    "Fulham":             "https://www.thesportsdb.com/images/media/team/badge/xwwvyt1448811086.png",
    "Hull":               "https://www.thesportsdb.com/images/media/team/badge/riiyZbb1JHuFQgZ3831jUQ_500x500.png",
    "Ipswich":            "https://www.thesportsdb.com/images/media/team/badge/mdj1ey1634670785.png",
    "Liverpool":          "https://www.thesportsdb.com/images/media/team/badge/kfaher1737969724.png",
    "Manchester City":    "https://www.thesportsdb.com/images/media/team/badge/vwpvry1467462651.png",
    "Manchester United":  "https://www.thesportsdb.com/images/media/team/badge/xzqdr11517660252.png",
    "Newcastle":          "https://www.thesportsdb.com/images/media/team/badge/lhwuiz1621593302.png",
    "Nottingham Forest":  "https://www.thesportsdb.com/images/media/team/badge/bk4qjs1546440351.png",
    "Tottenham":          "https://www.thesportsdb.com/images/media/team/badge/dfyfhl1604094109.png",
    "West Ham":           "https://www.thesportsdb.com/images/media/team/badge/yutyxs1467459956.png",
    "Wolves":             "https://www.thesportsdb.com/images/media/team/badge/u9qr031621593327.png",
    "Sunderland":         "https://www.thesportsdb.com/images/media/team/badge/le5k8j1634670785.png",
}

print(f"  Ready. Season: {CURRENT_SEASON} | Teams: {len(ALL_TEAMS)}\n")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _api_get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _normalise_team(api_name):
    """Map API team names to our internal names."""
    mapping = {
        "Manchester United F.C.": "Manchester United",
        "Manchester City F.C.": "Manchester City",
        "Nottingham Forest F.C.": "Nottingham Forest",
        "Sunderland AFC": "Sunderland",
        "Tottenham Hotspur F.C.": "Tottenham",
        "Newcastle United F.C.": "Newcastle",
        "Leeds United": "Leeds",
        "Brighton & Hove Albion F.C.": "Brighton",
        "Coventry City Football Club": "Coventry",
        "Hull City A.F.C.": "Hull",
        "Ipswich Town F.C.": "Ipswich",
        "Arsenal F.C.": "Arsenal",
        "Aston Villa F.C.": "Aston Villa",
        "AFC Bournemouth": "Bournemouth",
        "Brentford F.C.": "Brentford",
        "Chelsea F.C.": "Chelsea",
        "Crystal Palace F.C.": "Crystal Palace",
        "Everton F.C.": "Everton",
        "Fulham F.C.": "Fulham",
        "Liverpool F.C.": "Liverpool",
    }
    return mapping.get(api_name, api_name)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/teams")
def get_teams():
    log_event("API: /api/teams called")
    teams = [{"name": t, "badge": TEAM_BADGES.get(t, "")} for t in ALL_TEAMS]
    return jsonify({"teams": teams, "season": CURRENT_SEASON})


@app.route("/api/predict", methods=["POST"])
def predict():
    log_event("API: /api/predict called")
    body  = request.get_json(force=True)
    matches = body.get("matches", [])
    if not matches:
        return jsonify({"error": "No matches provided"}), 400

    results = []
    for m in matches:
        home = m.get("home", "").strip()
        away = m.get("away", "").strip()
        if not home or not away:
            results.append({"home": home, "away": away, "error": "Missing team"})
            continue
        if home == away:
            results.append({"home": home, "away": away, "error": "Teams must differ"})
            continue

        probs = predict_match(home, away, _rf, _target_enc, _label_enc,
                            _team_hist, CURRENT_SEASON)
        if probs is None:
            results.append({"home": home, "away": away, "error": "Unknown team(s)"})
            continue

        results.append({
            "home": home, "away": away,
            "home_badge": TEAM_BADGES.get(home, ""),
            "away_badge": TEAM_BADGES.get(away, ""),
            "probs": {
                "H": round(probs.get("H", 0), 4),
                "D": round(probs.get("D", 0), 4),
                "A": round(probs.get("A", 0), 4),
            },
        })

    return jsonify({"results": results})


@app.route("/api/simulate", methods=["POST"])
def simulate():
    log_event("API: /api/simulate called")
    standings = simulate_season(ALL_TEAMS, _rf, _target_enc, _label_enc,
                                _team_hist, CURRENT_SEASON)
    for row in standings:
        row["badge"] = TEAM_BADGES.get(row["team"], "")

    # ── Sidebar insights ──────────────────────────────────────────────────────
    top4      = [r for r in standings if r["pos"] <= 4]
    relegated = [r for r in standings if r["pos"] >= 18]
    promoted  = [r for r in standings if r["team"] in PROMOTED_TEAMS]
    top_scorer= sorted(standings, key=lambda r: r["gf"], reverse=True)[:5]
    best_gd   = sorted(standings, key=lambda r: r["gd"], reverse=True)[:5]

    insights = {
        "top4":       top4,
        "relegated":  relegated,
        "promoted":   promoted,
        "top_scorers": top_scorer,
        "best_gd":    best_gd,
    }

    return jsonify({"season": CURRENT_SEASON, "standings": standings, "insights": insights})


@app.route("/api/fixtures")
def fixtures():
    log_event("API: /api/fixtures called")
    """
    Fetch upcoming PL fixtures and group them strictly by round number,
    capturing all 10 matches per gameweek without dropping un-normalized names.
    """
    from model import _fetch_season_raw
    import re
    
    events = _fetch_season_raw(CURRENT_SEASON, verbose=False) or []
    rounds_dict = {}

    for e in events:
        hg = e.get("intHomeScore")
        ag = e.get("intAwayScore")
        if hg is not None and ag is not None:
            continue  # already played

        home = e.get("strHomeTeam", "")
        away = e.get("strAwayTeam", "")
        date = e.get("dateEvent", "")
        time = e.get("strTime", "")
        
        # Extract the real numeric round
        raw_round = str(e.get("intRound", "1"))
        match_round = re.search(r'\d+', raw_round)
        round_num = int(match_round.group()) if match_round else 1

        if not home or not away:
            continue

        if round_num not in rounds_dict:
            rounds_dict[round_num] = {
                "round": str(round_num),
                "round_num": str(round_num),
                "title": f"Gameweek {round_num}",
                "name": f"Gameweek {round_num}",
                "gameweek": str(round_num),
                "date": date,
                "matches": []
            }
        
        rounds_dict[round_num]["matches"].append({
            "home":       home,
            "away":       away,
            "home_badge": TEAM_BADGES.get(home, TEAM_BADGES.get(_normalise_team(home), "")),
            "away_badge": TEAM_BADGES.get(away, TEAM_BADGES.get(_normalise_team(away), "")),
            "date":       date,
            "time":       time,
            "round":      str(round_num),
        })

    # Sort rounds numerically and pick the next 2 upcoming rounds with matches
    sorted_rounds = sorted([r for r in rounds_dict.keys() if rounds_dict[r]["matches"]])
    next_two_rounds = sorted_rounds[:2]

    gameweeks_result = []
    for r in next_two_rounds:
        gw_data = rounds_dict[r]
        gw_data["matches"].sort(key=lambda x: (x["date"] if x["date"] else "9999-99-99", x["time"] if x["time"] else ""))
        
        dates = [m["date"] for m in gw_data["matches"] if m["date"]]
        if dates:
            gw_data["date"] = min(dates)
            
        gameweeks_result.append(gw_data)

    return jsonify({"gameweeks": gameweeks_result})

# ─── Run ────────────────────────────────________________________________──────

if __name__ == "__main__":
    app.run(debug=False, port=5000)