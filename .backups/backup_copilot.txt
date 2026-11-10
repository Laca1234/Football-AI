# Premier League Match Result Probability Predictor
# All data from TheSportsDB API (round-by-round) | local cache | linear recency weights

# ==========================
# 1. Imports & Warnings
# ==========================
import os
import json
import time
import warnings
import urllib.request
from itertools import permutations
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR  = os.path.join(SCRIPT_DIR, "_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


# ==========================
# 2. API Config
# ==========================
SPORTSDB_KEY = "123"        # free key — replace with premium if you upgrade
PL_LEAGUE_ID = "4328"
BASE_URL      = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_KEY}"
TOTAL_ROUNDS  = 38

# Seasons to fetch: 2000-2001 through 2025-2026
FIRST_YEAR    = 2012
CURRENT_YEAR  = 2026
ALL_SEASONS   = [f"{y}-{y+1}" for y in range(FIRST_YEAR, CURRENT_YEAR)]


# ==========================
# 3. Fetching & Caching
# ==========================
def _cache_path(season):
    return os.path.join(CACHE_DIR, f"season_{season.replace('-','_')}.json")


def _fetch_round(season, round_num):
    """
    Fetch one round from the API. Returns list of event dicts or [].
    No caching at round level — we cache at season level after all rounds
    are assembled, so a failed mid-season fetch can be retried cleanly.
    """
    url = (
        f"{BASE_URL}/eventsround.php"
        f"?id={PL_LEAGUE_ID}&r={round_num}&s={season}"
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode())
        return data.get("events") or []
    except Exception as e:
        print(f"    [API] Round {round_num} failed: {e}")
        return []


def _fetch_season_raw(season, verbose=True):
    """
    Fetches all 38 rounds for a season, assembles them, caches to disk.
    Returns list of all event dicts for that season.
    On subsequent runs loads straight from cache — no API call needed.
    """
    path = _cache_path(season)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)

    if verbose:
        print(f"  {season}: fetching 38 rounds", end="", flush=True)

    all_events = []
    for r in range(1, TOTAL_ROUNDS + 1):
        events = _fetch_round(season, r)
        all_events.extend(events)
        time.sleep(2.1)   # stay under 30 req/min free limit
        if verbose and r % 10 == 0:
            print(f".", end="", flush=True)

    # Cache the full season so we never fetch it again
    with open(path, "w") as f:
        json.dump(all_events, f)

    if verbose:
        print(f" → {len(all_events)} matches cached")

    return all_events


def _parse_events(events, season):
    """
    Convert raw event list to a tidy DataFrame.
    Columns: HomeTeam, AwayTeam, FTHG, FTAG, FTR, season, date
    Only includes completed matches (both scores present and non-null).
    """
    rows = []
    for e in events:
        hg = e.get("intHomeScore")
        ag = e.get("intAwayScore")
        if hg is None or ag is None:
            continue
        try:
            hg, ag = int(hg), int(ag)
        except (ValueError, TypeError):
            continue

        ftr = "H" if hg > ag else ("A" if ag > hg else "D")
        rows.append({
            "HomeTeam": e["strHomeTeam"],
            "AwayTeam": e["strAwayTeam"],
            "FTHG":     hg,
            "FTAG":     ag,
            "FTR":      ftr,
            "season":   season,
            "date":     e.get("dateEvent", ""),
        })
    return pd.DataFrame(rows)


# ==========================
# 4. Load All Seasons + Weights
# ==========================
def load_all_data(verbose=True):
    """
    Loads all seasons 2000-2001 to present.
    First run fetches from API round-by-round (~33 min, one-time only).
    Subsequent runs load from local cache instantly.

    Recency weights are linear:
      oldest season (2000-2001) → weight 1.0
      newest season             → weight 5.0
      everything between scales proportionally
    """
    total = len(ALL_SEASONS)
    dfs   = []
    needs_fetch = [s for s in ALL_SEASONS if not os.path.exists(_cache_path(s))]

    if needs_fetch and verbose:
        print(f"\n  First run: fetching {len(needs_fetch)} season(s) from API.")
        print(f"  This takes ~{len(needs_fetch) * 38 * 2 // 60 + 1} min and only happens once.")
        print(f"  {'─' * 50}")

    for i, season in enumerate(ALL_SEASONS):
        events = _fetch_season_raw(season, verbose=verbose)
        df     = _parse_events(events, season)
        if df.empty:
            continue

        # Linear weight: 1.0 for index 0 (oldest), 5.0 for last index
        weight     = 1.0 + 4.0 * (i / (total - 1))
        df["weight"] = round(weight, 4)
        dfs.append(df)

    if not dfs:
        raise RuntimeError("No data loaded — check your internet connection.")

    combined = pd.concat(dfs, ignore_index=True)

    if verbose:
        seasons_loaded = combined["season"].nunique()
        print(f"\n  Loaded {len(combined):,} matches across {seasons_loaded} seasons.")
        print(f"  Weight range: 1.0 (2000-2001) → 5.0 ({ALL_SEASONS[-1]})\n")

    return combined


# ==========================
# 5. Team Strength & Form Calculation
# ==========================
def calculate_team_strength(data, team):
    """
    Calculate overall team strength from all historical matches.
    Stabilizes predictions with long-term performance metrics.
    """
    home_matches = data[data["HomeTeam"] == team]
    away_matches = data[data["AwayTeam"] == team]
    
    all_matches = len(home_matches) + len(away_matches)
    if all_matches == 0:
        return {"win_rate": 0.333, "avg_gf": 1.0, "avg_ga": 1.0}
    
    home_wins = (home_matches["FTR"] == "H").sum()
    away_wins = (away_matches["FTR"] == "A").sum()
    total_wins = home_wins + away_wins
    
    all_gf = home_matches["FTHG"].sum() + away_matches["FTAG"].sum()
    all_ga = home_matches["FTAG"].sum() + away_matches["FTHG"].sum()
    
    return {
        "win_rate": total_wins / all_matches if all_matches > 0 else 0.333,
        "avg_gf": all_gf / all_matches if all_matches > 0 else 1.0,
        "avg_ga": all_ga / all_matches if all_matches > 0 else 1.0,
    }


def calculate_team_form(data, team, is_home):
    """
    Calculate team's last 5 form stats (recent performance + goals).
    """
    if is_home:
        team_matches = data[data["HomeTeam"] == team].tail(5)
        goals_for = team_matches["FTHG"].sum()
        goals_against = team_matches["FTAG"].sum()
        result_label = "H"
    else:
        team_matches = data[data["AwayTeam"] == team].tail(5)
        goals_for = team_matches["FTAG"].sum()
        goals_against = team_matches["FTHG"].sum()
        result_label = "A"
    
    wins = (team_matches["FTR"] == result_label).sum()
    draws = (team_matches["FTR"] == "D").sum()
    losses = len(team_matches) - wins - draws
    
    n_matches = len(team_matches)
    avg_gf = goals_for / n_matches if n_matches > 0 else 1.0
    avg_ga = goals_against / n_matches if n_matches > 0 else 1.0
    
    return {
        "recent_wins": wins,
        "recent_draws": draws,
        "recent_losses": losses,
        "recent_avg_gf": avg_gf,
        "recent_avg_ga": avg_ga,
    }


def get_features_for_match(data, home_team, away_team, label_encoders):
    """
    Extract team identity + form features for a match.
    Combines stable team strength with recent form volatility.
    """
    # Team identity encoding
    h_enc = label_encoders["HomeTeam"].transform([home_team])[0]
    a_enc = label_encoders["AwayTeam"].transform([away_team])[0]
    
    # Overall team strength
    home_strength = calculate_team_strength(data, home_team)
    away_strength = calculate_team_strength(data, away_team)
    
    # Recent form
    home_form = calculate_team_form(data, home_team, is_home=True)
    away_form = calculate_team_form(data, away_team, is_home=False)
    
    features = {
        "home_team_enc": h_enc,
        "away_team_enc": a_enc,
        "home_win_rate": home_strength["win_rate"],
        "home_avg_gf": home_strength["avg_gf"],
        "home_avg_ga": home_strength["avg_ga"],
        "away_win_rate": away_strength["win_rate"],
        "away_avg_gf": away_strength["avg_gf"],
        "away_avg_ga": away_strength["avg_ga"],
        "home_recent_wins": home_form["recent_wins"],
        "home_recent_draws": home_form["recent_draws"],
        "home_recent_losses": home_form["recent_losses"],
        "home_recent_avg_gf": home_form["recent_avg_gf"],
        "home_recent_avg_ga": home_form["recent_avg_ga"],
        "away_recent_wins": away_form["recent_wins"],
        "away_recent_draws": away_form["recent_draws"],
        "away_recent_losses": away_form["recent_losses"],
        "away_recent_avg_gf": away_form["recent_avg_gf"],
        "away_recent_avg_ga": away_form["recent_avg_ga"],
    }
    
    return features


# ==========================
# 5b. Train Model
# ==========================
def train_model(data, verbose=True):
    """
    Combines team identity + overall strength + recent form.
    Trains a weighted Random Forest on mixed stable/volatile features.
    Returns (rf, target_encoder, label_encoders, feature_cols).
    """
    if verbose:
        print(f"  Training model on {len(data):,} matches...")

    team_cols      = ["HomeTeam", "AwayTeam"]
    label_encoders = {}
    
    # Fit label encoders on original team names (don't modify data yet)
    for col in team_cols:
        le = LabelEncoder()
        le.fit(data[col].unique())
        label_encoders[col] = le

    df = data.copy()
    target_encoder = LabelEncoder()
    df["FTR_enc"]  = target_encoder.fit_transform(df["FTR"])

    feature_cols = [
        "home_team_enc", "away_team_enc",
        "home_win_rate", "home_avg_gf", "home_avg_ga",
        "away_win_rate", "away_avg_gf", "away_avg_ga",
        "home_recent_wins", "home_recent_draws", "home_recent_losses",
        "home_recent_avg_gf", "home_recent_avg_ga",
        "away_recent_wins", "away_recent_draws", "away_recent_losses",
        "away_recent_avg_gf", "away_recent_avg_ga",
    ]
    
    # Build feature matrix from team identity + strength + form (using original team names)
    feature_data = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        features = get_features_for_match(df, row["HomeTeam"], row["AwayTeam"], label_encoders)
        feature_data.append(features)
    
    X = pd.DataFrame(feature_data)
    y = df["FTR_enc"]

    # Repeat rows proportional to weight — recent seasons appear more in training
    repeat_counts = df["weight"].apply(lambda w: max(1, int(round(w)))).values
    weighted_X    = X.loc[X.index.repeat(repeat_counts)].reset_index(drop=True)
    weighted_y    = y.loc[y.index.repeat(repeat_counts)].reset_index(drop=True)

    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,              # Shallow trees prevent overfitting
        min_samples_split=20,      # Require more samples per split
        min_samples_leaf=10,       # Prevent extreme leaf predictions
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    rf.fit(weighted_X, weighted_y)

    if verbose:
        print(f"  Done. Trained on {len(feature_cols)} features (team ID + strength + form).\n")

    return rf, target_encoder, label_encoders, feature_cols


# ==========================
# 6. Prediction Helper
# ==========================
NOISE_STD = 0.02   # Reduced noise for more stable predictions


def predict_match(home, away, data, rf, target_encoder, label_encoders, feature_cols, noise=True):
    """
    Returns H/D/A probability dict based on team identity + strength + form,
    or None if team not found in data.
    """
    # Check if teams exist
    all_teams = set(data["HomeTeam"].unique()) | set(data["AwayTeam"].unique())
    if home not in all_teams:
        print(f"  Unknown team: '{home}'")
        return None
    if away not in all_teams:
        print(f"  Unknown team: '{away}'")
        return None

    # Build feature vector with team encoding + strength + form
    features = get_features_for_match(data, home, away, label_encoders)
    X_input = pd.DataFrame([features], columns=feature_cols)
    proba   = rf.predict_proba(X_input)[0]

    # Smooth toward uniform more aggressively — prevents extreme predictions
    proba = proba * 0.85 + 0.15 / 3

    if noise:
        proba += np.random.normal(0, NOISE_STD, size=len(proba))
        proba  = np.clip(proba, 0.01, None)

    proba /= proba.sum()
    return dict(zip(target_encoder.classes_, proba))


def print_match_result(home, away, probs):
    print(f"\n  {home} vs {away}")
    print(f"  {'─' * 36}")
    for outcome, label in [("H", f"{home} win"), ("D", "Draw"), ("A", f"{away} win")]:
        p       = probs.get(outcome, 0)
        bar_len = int(p * 30)
        bar     = "█" * bar_len + "░" * (30 - bar_len)
        print(f"  {label:<26} {bar}  {p:.1%}")


# ==========================
# 7. Season Simulation
# ==========================
def get_current_season_teams(data):
    """Returns the teams from the most recent season in the dataset."""
    latest = sorted(data["season"].unique())[-1]
    recent = data[data["season"] == latest]
    return sorted(set(recent["HomeTeam"].tolist() + recent["AwayTeam"].tolist()))


def simulate_season(data, rf, target_encoder, label_encoders, feature_cols):
    """
    Plays out one full season — every team vs every other once home, once away.
    Results are sampled from model probabilities + noise, so each run differs.
    Sorted by PL rules: Pts > GD > GF.
    """
    teams    = get_current_season_teams(data)
    fixtures = list(permutations(teams, 2))   # N*(N-1) = 380 for 20 teams

    print(f"\n  {len(teams)} teams | {len(fixtures)} fixtures")
    print(f"  {'─' * 40}")

    points = defaultdict(int)
    wins   = defaultdict(int)
    draws  = defaultdict(int)
    losses = defaultdict(int)
    gf     = defaultdict(int)
    ga     = defaultdict(int)

    for home, away in fixtures:
        probs = predict_match(
            home, away, data, rf, target_encoder, label_encoders, feature_cols, noise=True
        )
        if probs is None:
            continue

        # Get expected goals based on team form
        home_strength = calculate_team_strength(data, home)
        away_strength = calculate_team_strength(data, away)
        home_form = calculate_team_form(data, home, is_home=True)
        away_form = calculate_team_form(data, away, is_home=False)
        
        # Expected goals: blend strength with form
        home_xg = home_strength["avg_gf"] * 0.7 + home_form["recent_avg_gf"] * 0.3
        away_xg = away_strength["avg_gf"] * 0.7 + away_form["recent_avg_gf"] * 0.3
        
        # Generate realistic goal counts biased toward expected goals
        # Use Poisson-like distribution with some variance
        hg = np.random.poisson(home_xg)
        ag = np.random.poisson(away_xg)
        
        # Clip to reasonable range and adjust for outcome
        hg = min(hg, 5)
        ag = min(ag, 5)
        
        # Ensure outcome matches prediction (soft constraint)
        outcome = np.random.choice(
            ["H", "D", "A"], p=[probs["H"], probs["D"], probs["A"]]
        )
        
        # Adjust goals to roughly match predicted outcome (but keep naturalistic)
        if outcome == "H" and hg <= ag:
            # Home win but goals don't reflect it: boost home slightly
            hg = ag + np.random.randint(1, 2)
        elif outcome == "A" and ag <= hg:
            # Away win but goals don't reflect it: boost away slightly
            ag = hg + np.random.randint(1, 2)
        elif outcome == "D" and hg != ag:
            # Draw predicted but goals differ: make them equal
            if np.random.random() < 0.5:
                ag = hg
            else:
                hg = ag

        # Record results
        if hg > ag:
            points[home] += 3
            wins[home]   += 1
            losses[away] += 1
        elif ag > hg:
            points[away] += 3
            wins[away]   += 1
            losses[home] += 1
        else:
            points[home] += 1
            points[away] += 1
            draws[home]  += 1
            draws[away]  += 1

        gf[home] += hg;  ga[home] += ag
        gf[away] += ag;  ga[away] += hg

    standings = sorted(
        teams,
        key=lambda t: (points[t], gf[t] - ga[t], gf[t]),
        reverse=True,
    )

    rows = []
    for pos, team in enumerate(standings, 1):
        gd_val = gf[team] - ga[team]
        rows.append({
            "Pos":  pos,
            "Team": team,
            "Pts":  points[team],
            "W":    wins[team],
            "D":    draws[team],
            "L":    losses[team],
            "GF":   gf[team],
            "GA":   ga[team],
            "GD":   f"{gd_val:+d}",
        })

    return pd.DataFrame(rows).set_index("Pos")


# ==========================
# 8. CLI
# ==========================
def get_team_input(prompt_text, data):
    known = sorted(set(data["HomeTeam"].unique()) | set(data["AwayTeam"].unique()))
    while True:
        name        = input(prompt_text).strip()
        if name in known:
            return name
        suggestions = [t for t in known if name.lower() in t.lower()]
        if suggestions:
            print(f"  Not found. Did you mean: {', '.join(suggestions[:6])}?")
        else:
            print(f"  Not found. Examples: {', '.join(known[:8])}...")
        print()


def run_cli(data, rf, target_encoder, label_encoders, feature_cols):
    print("=" * 50)
    print("  PREMIER LEAGUE RESULT PREDICTOR")
    print("=" * 50)

    while True:
        print("\n  Choose a mode:")
        print("  [1] Single match prediction")
        print("  [2] Multi-match predictions")
        print("  [3] Season simulation")
        print("  [q] Quit")
        print()

        choice = input("  Enter choice: ").strip().lower()

        # ── Single match ──────────────────────────────────
        if choice == "1":
            home  = get_team_input("\n  Home team: ", data)
            away  = get_team_input("  Away team: ", data)
            probs = predict_match(home, away, data, rf, target_encoder, label_encoders, feature_cols)
            if probs:
                print_match_result(home, away, probs)

        # ── Multi-match ───────────────────────────────────
        elif choice == "2":
            matches = []
            print("\n  Enter matches one by one. Type 'done' when finished.\n")
            while True:
                home_input = input("  Home team (or 'done'): ").strip()
                if home_input.lower() == "done":
                    break
                known = sorted(set(data["HomeTeam"].unique()) | set(data["AwayTeam"].unique()))
                home  = home_input if home_input in known \
                        else get_team_input("  Home team: ", data)
                away  = get_team_input("  Away team: ", data)
                matches.append((home, away))

            if matches:
                print(f"\n  {'─' * 40}")
                print(f"  PREDICTIONS FOR {len(matches)} MATCH(ES)")
                print(f"  {'─' * 40}")
                for home, away in matches:
                    probs = predict_match(
                        home, away, data, rf, target_encoder, label_encoders, feature_cols
                    )
                    if probs:
                        print_match_result(home, away, probs)
                    else:
                        print(f"\n  Skipping {home} vs {away} — team(s) not found.")
            else:
                print("  No matches entered.")

        # ── Season simulation ─────────────────────────────
        elif choice == "3":
            print("\n  Simulating season...")
            results = simulate_season(data, rf, target_encoder, label_encoders, feature_cols)
            print(f"\n  {'─' * 60}")
            print(f"  PREDICTED FINAL STANDINGS")
            print(f"  {'─' * 60}")
            print(results.to_string())
            print(
                f"\n  Tip: run again for a different outcome"
                f"  |  NOISE_STD={NOISE_STD}\n"
            )

        elif choice == "q":
            print("\n  Goodbye!\n")
            break

        else:
            print("  Invalid choice. Please enter 1, 2, 3 or q.")


# ==========================
# 9. Entry Point
# ==========================
if __name__ == "__main__":
    data                                           = load_all_data()
    rf, target_encoder, label_encoders, feature_cols = train_model(data)
    run_cli(data, rf, target_encoder, label_encoders, feature_cols)
