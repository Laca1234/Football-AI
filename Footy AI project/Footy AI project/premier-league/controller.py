# controller.py — Flask API routes

from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
import os
import json
import urllib.request

from model import load_all_data, train_model, ALL_SEASONS
from service import predict_match, simulate_season

app = Flask(__name__)
CORS(app)

# ─── Bootstrap ───────────────────────────────────────────────────────────────
print("\n  Booting Premier League Predictor...")
_data                                              = load_all_data()
_rf, _target_enc, _label_enc, _team_hist, _feat_cols = train_model(_data)

CURRENT_SEASON = sorted(_data["season"].unique())[-1]

ALL_TEAMS = sorted([
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Leeds",
    "Burnley", "Liverpool", "Manchester City", "Manchester United",
    "Newcastle", "Nottingham Forest", "Sunderland", "Tottenham",
    "West Ham", "Wolves",
])

# Teams promoted to PL this season — shown in the season sim sidebar
PROMOTED_TEAMS = ["Leeds", "Burnley", "Sunderland"]

TEAM_BADGES = {
    "Arsenal":            "https://www.thesportsdb.com/images/media/team/badge/uyhbfe1612467038.png",
    "Aston Villa":        "https://www.thesportsdb.com/images/media/team/badge/jykrpv1717309891.png",
    "Bournemouth":        "https://www.thesportsdb.com/images/media/team/badge/y08nak1534071116.png",
    "Brentford":          "https://www.thesportsdb.com/images/media/team/badge/grv1aw1546453779.png",
    "Brighton":           "https://www.thesportsdb.com/images/media/team/badge/ywypts1448810904.png",
    "Chelsea":            "https://www.thesportsdb.com/images/media/team/badge/yvwvtu1448813215.png",
    "Crystal Palace":     "https://www.thesportsdb.com/images/media/team/badge/ia6i3m1656014992.png",
    "Everton":            "https://www.thesportsdb.com/images/media/team/badge/eqayrf1523184794.png",
    "Fulham":             "https://www.thesportsdb.com/images/media/team/badge/xwwvyt1448811086.png",
    #"Ipswich":            "https://www.thesportsdb.com/images/media/team/badge/mdj1ey1634670785.png",
    #"Leicester":          "https://www.thesportsdb.com/images/media/team/badge/xtxwtu1448813356.png",
    "Liverpool":          "https://www.thesportsdb.com/images/media/team/badge/kfaher1737969724.png",
    "Manchester City":    "https://www.thesportsdb.com/images/media/team/badge/vwpvry1467462651.png",
    "Manchester United":  "https://www.thesportsdb.com/images/media/team/badge/xzqdr11517660252.png",
    "Newcastle":          "https://www.thesportsdb.com/images/media/team/badge/lhwuiz1621593302.png",
    "Nottingham Forest":  "https://www.thesportsdb.com/images/media/team/badge/bk4qjs1546440351.png",
    #"Southampton":        "https://www.thesportsdb.com/images/media/team/badge/ggqtd01621593274.png",
    "Tottenham":          "https://www.thesportsdb.com/images/media/team/badge/dfyfhl1604094109.png",
    "West Ham":           "https://www.thesportsdb.com/images/media/team/badge/yutyxs1467459956.png",
    "Wolves":             "https://www.thesportsdb.com/images/media/team/badge/u9qr031621593327.png",
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
        "Manchester United":       "Manchester United",
        "Manchester City":         "Manchester City",
        "Nottingham Forest":       "Nottingham Forest",
        "Wolverhampton Wanderers": "Wolves",
        "Tottenham Hotspur":       "Tottenham",
        "Newcastle United":        "Newcastle",
        "West Ham United":         "West Ham",
        "Brighton and Hove Albion":"Brighton",
        "Sunderland AFC":          "Sunderland",
        "Leeds United":            "Leeds",
        "Burnley FC":              "Burnley",
    }
    return mapping.get(api_name, api_name)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/teams")
def get_teams():
    teams = [{"name": t, "badge": TEAM_BADGES.get(t, "")} for t in ALL_TEAMS]
    return jsonify({"teams": teams, "season": CURRENT_SEASON})


@app.route("/api/predict", methods=["POST"])
def predict():
    body    = request.get_json(force=True)
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
                              _team_hist, CURRENT_SEASON, noise=True)
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
    """
    Fetch next 2 gameweeks of PL fixtures from TheSportsDB.
    Returns upcoming (unplayed) matches grouped by date.
    """
    base   = "https://www.thesportsdb.com/api/v1/json/123"
    data   = _api_get(f"{base}/eventsnextleague.php?id=4328")
    events = (data or {}).get("events") or []

    results = []
    seen_dates = set()

    for e in events:
        home = _normalise_team(e.get("strHomeTeam", ""))
        away = _normalise_team(e.get("strAwayTeam", ""))
        date = e.get("dateEvent", "")
        time = e.get("strTime", "")

        # Only include teams we know about
        if home not in ALL_TEAMS or away not in ALL_TEAMS:
            continue
        if e.get("intHomeScore") is not None:
            continue  # already played

        seen_dates.add(date)
        if len(seen_dates) > 2:
            break

        results.append({
            "home":       home,
            "away":       away,
            "home_badge": TEAM_BADGES.get(home, ""),
            "away_badge": TEAM_BADGES.get(away, ""),
            "date":       date,
            "time":       time,
        })

    # Group by date
    grouped = {}
    for r in results:
        grouped.setdefault(r["date"], []).append(r)

    return jsonify({"gameweeks": [
        {"date": d, "matches": grouped[d]}
        for d in sorted(grouped.keys())
    ]})


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False, port=5000)