# model.py — data loading, feature engineering, model training

import os
import json
import time
import warnings
import urllib.request
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, log_loss, classification_report

warnings.simplefilter(action="ignore", category=FutureWarning)
pd.options.mode.chained_assignment = None

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR    = os.path.join(SCRIPT_DIR, "_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

SPORTSDB_KEY = "123"
PL_LEAGUE_ID = "4328"
BASE_URL     = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_KEY}"
TOTAL_ROUNDS = 38
FIRST_YEAR   = 2012
CURRENT_YEAR = 2027
ALL_SEASONS  = [f"{y}-{y+1}" for y in range(FIRST_YEAR, CURRENT_YEAR)]
FORM_WINDOW  = 5    # short-term form
LONG_WINDOW  = 38   # long-term quality (~1 full season)


# ─── Fetching ────────────────────────────────────────────────────────────────

def _cache_path(season):
    return os.path.join(CACHE_DIR, f"season_{season.replace('-','_')}.json")


def _fetch_round(season, round_num, max_retries=3):
    url = f"{BASE_URL}/eventsround.php?id={PL_LEAGUE_ID}&r={round_num}&s={season}"
    delay = 3.0
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read().decode())
            return data.get("events") or []
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            if attempt == max_retries - 1:
                pass
    return []



def _fetch_season_raw(season, verbose=True):
    path = _cache_path(season)
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass

    if verbose:
        print(f"  {season}: fetching rounds (with cache fallback)", end="", flush=True)

    all_events = []
    for r in range(1, TOTAL_ROUNDS + 1):
        events = _fetch_round(season, r)
        if events:
            all_events.extend(events)
        time.sleep(1.5)
        if verbose and r % 10 == 0:
            print(".", end="", flush=True)

    # Automatic fallback if API blocks requests completely
    if not all_events:
        raise RuntimeError(
            f"Failed to fetch any data for season {season}. "
            "Check your internet connection or the API key."
        )
    
    try:
        with open(path, "w") as f:
            json.dump(all_events, f)
    except Exception:
        pass

    if verbose:
        print(f" → {len(all_events)} matches loaded.")
    return all_events

def _normalise_team(api_name):
    mapping = {
        "Arsenal F.C.": "Arsenal",
        "Aston Villa F.C.": "Aston Villa",
        "AFC Bournemouth": "Bournemouth",
        "Brentford F.C.": "Brentford",
        "Brighton & Hove Albion F.C.": "Brighton",
        "Brighton and Hove Albion": "Brighton",
        "Chelsea F.C.": "Chelsea",
        "Crystal Palace F.C.": "Crystal Palace",
        "Everton F.C.": "Everton",
        "Fulham F.C.": "Fulham",
        "Liverpool F.C.": "Liverpool",
        "Manchester City F.C.": "Manchester City",
        "Manchester United F.C.": "Manchester United",
        "Newcastle United F.C.": "Newcastle",
        "Newcastle United": "Newcastle",
        "Nottingham Forest F.C.": "Nottingham Forest",
        "Nottingham Forest": "Nottingham Forest",
        "Tottenham Hotspur F.C.": "Tottenham",
        "Tottenham Hotspur": "Tottenham",
        "West Ham United": "West Ham",
        "West Ham United F.C.": "West Ham",
        "Wolverhampton Wanderers": "Wolves",
        "Wolves": "Wolves",
        "Sunderland AFC": "Sunderland",
        "Leeds United F.C.": "Leeds",
        "Leeds United": "Leeds",
        "Burnley F.C.": "Burnley",
        "Coventry City Football Club": "Coventry",
        "Coventry City": "Coventry",
        "Hull City A.F.C.": "Hull",
        "Hull City": "Hull",
        "Ipswich Town F.C.": "Ipswich",
        "Ipswich Town": "Ipswich",
    }
    return mapping.get(api_name, api_name)


def _parse_events(events, season):
    rows = []
    for e in events:
        hg = e.get("intHomeScore")
        ag = e.get("intAwayScore")
        if hg is None or ag is None:
            hg_val, ag_val, ftr = None, None, None
        else:
            try:
                hg_val, ag_val = int(hg), int(ag)
                ftr = "H" if hg_val > ag_val else ("A" if ag_val > hg_val else "D")
            except (ValueError, TypeError):
                hg_val, ag_val, ftr = None, None, None
        
        home_team = _normalise_team(e.get("strHomeTeam", ""))
        away_team = _normalise_team(e.get("strAwayTeam", ""))
        
        rows.append({
            "HomeTeam": home_team,
            "AwayTeam": away_team,
            "FTHG":     hg_val,
            "FTAG":     ag_val,
            "FTR":      ftr,
            "season":   season,
            "date":     e.get("dateEvent", ""),
        })
    return pd.DataFrame(rows)


# ─── Load all seasons ─────────────────────────────────────────────────────────

def load_all_data(verbose=True):
    total       = len(ALL_SEASONS)
    dfs         = []
    needs_fetch = [s for s in ALL_SEASONS if not os.path.exists(_cache_path(s))]

    if needs_fetch and verbose:
        est = len(needs_fetch) * 38 * 2 // 60 + 1
        print(f"\n  Fetching {len(needs_fetch)} season(s) — ~{est} min, one-time only.")
        print(f"  {'─' * 50}")

    for i, season in enumerate(ALL_SEASONS):
        events = _fetch_season_raw(season, verbose=verbose)
        df     = _parse_events(events, season)
        if df.empty:
            continue
        weight       = 1.0 + 4.0 * (i / (total - 1))
        df["weight"] = round(weight, 4)
        dfs.append(df)

    if not dfs:
        raise RuntimeError("No data loaded — check internet connection.")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)

    if verbose:
        print(f"\n  Loaded {len(combined):,} matches across {combined['season'].nunique()} seasons.")
    return combined


# ─── Feature engineering ──────────────────────────────────────────────────────

def _team_stats(hist, window):
    """Compute W/D/L and avg GF/GA over the last `window` entries."""
    recent = hist[-window:]
    if not recent:
        return dict(w=0, d=0, l=0, avg_gf=1.2, avg_ga=1.0, wr=0.33)
    w  = sum(1 for h in recent if h["win"])
    d  = sum(1 for h in recent if h["draw"])
    l  = len(recent) - w - d
    gf = float(np.mean([h["gf"] for h in recent]))
    ga = float(np.mean([h["ga"] for h in recent]))
    return dict(w=w, d=d, l=l, avg_gf=gf, avg_ga=ga, wr=w / len(recent))


def _build_features(data: pd.DataFrame):
    team_history = defaultdict(list)
    feature_rows = []

    for _, row in data.iterrows():
        ht, at   = row["HomeTeam"], row["AwayTeam"]
        season   = row["season"]

        h_hist = team_history[ht]
        a_hist = team_history[at]

        # Short-term overall form (last 5)
        hf5  = _team_stats(h_hist, FORM_WINDOW)
        af5  = _team_stats(a_hist, FORM_WINDOW)

        # Short-term venue-specific form (last 5 home / last 5 away)
        h_home_hist = [h for h in h_hist if h["is_home"]]
        a_away_hist = [h for h in a_hist if not h["is_home"]]
        hf5v = _team_stats(h_home_hist, FORM_WINDOW)
        af5v = _team_stats(a_away_hist, FORM_WINDOW)

        # Long-term quality (last 38 — ~1 full season)
        hf38 = _team_stats(h_hist, LONG_WINDOW)
        af38 = _team_stats(a_hist, LONG_WINDOW)

        # Season-to-date
        h_szn = [h for h in h_hist if h["season"] == season]
        a_szn = [h for h in a_hist if h["season"] == season]
        h_szn_gf = float(np.mean([h["gf"] for h in h_szn])) if h_szn else 1.2
        h_szn_ga = float(np.mean([h["ga"] for h in h_szn])) if h_szn else 1.0
        a_szn_gf = float(np.mean([h["gf"] for h in a_szn])) if a_szn else 1.2
        a_szn_ga = float(np.mean([h["ga"] for h in a_szn])) if a_szn else 1.0

        feature_rows.append({
            # short-term overall
            "h_w5": hf5["w"],   "h_d5": hf5["d"],   "h_l5": hf5["l"],
            "h_gf5": hf5["avg_gf"], "h_ga5": hf5["avg_ga"],
            "a_w5": af5["w"],   "a_d5": af5["d"],   "a_l5": af5["l"],
            "a_gf5": af5["avg_gf"], "a_ga5": af5["avg_ga"],
            # short-term venue-specific
            "h_home_w5": hf5v["w"],  "h_home_d5": hf5v["d"],  "h_home_l5": hf5v["l"],
            "h_home_gf5": hf5v["avg_gf"], "h_home_ga5": hf5v["avg_ga"],
            "a_away_w5": af5v["w"],  "a_away_d5": af5v["d"],  "a_away_l5": af5v["l"],
            "a_away_gf5": af5v["avg_gf"], "a_away_ga5": af5v["avg_ga"],
            # long-term quality
            "h_wr38": hf38["wr"],  "h_gf38": hf38["avg_gf"], "h_ga38": hf38["avg_ga"],
            "a_wr38": af38["wr"],  "a_gf38": af38["avg_gf"], "a_ga38": af38["avg_ga"],
            # season-to-date
            "h_season_gf": h_szn_gf, "h_season_ga": h_szn_ga,
            "a_season_gf": a_szn_gf, "a_season_ga": a_szn_ga,
            # target + weight
            "FTR":    row["FTR"],
            "weight": row["weight"],
        })

        # Update AFTER extracting features (no leakage)
        team_history[ht].append(dict(
            is_home=True,  gf=row["FTHG"], ga=row["FTAG"],
            win=(row["FTR"] == "H"), draw=(row["FTR"] == "D"),
            season=season, date=row["date"],
        ))
        team_history[at].append(dict(
            is_home=False, gf=row["FTAG"], ga=row["FTHG"],
            win=(row["FTR"] == "A"), draw=(row["FTR"] == "D"),
            season=season, date=row["date"],
        ))

    return pd.DataFrame(feature_rows), team_history


FEATURE_COLS = [
    # short-term overall
    "h_w5","h_d5","h_l5","h_gf5","h_ga5",
    "a_w5","a_d5","a_l5","a_gf5","a_ga5",
    # short-term venue-specific
    "h_home_w5","h_home_d5","h_home_l5","h_home_gf5","h_home_ga5",
    "a_away_w5","a_away_d5","a_away_l5","a_away_gf5","a_away_ga5",
    # long-term quality — the key differentiator between Arsenal and Southampton
    "h_wr38","h_gf38","h_ga38",
    "a_wr38","a_gf38","a_ga38",
    # season-to-date
    "h_season_gf","h_season_ga","a_season_gf","a_season_ga",
]


# ─── Training ────────────────────────────────────────────────────────────────

def train_model(data: pd.DataFrame, verbose=True):
    if verbose:
        print(f"  Building features for completed matches...")

    completed_data = data.dropna(subset=["FTR"]).reset_index(drop=True)
    feat_df, team_history = _build_features(completed_data)

    label_encoders = {}
    for col in ["home_team", "away_team"]:
        le = LabelEncoder()
        le.fit(data["HomeTeam"].tolist() + data["AwayTeam"].tolist())
        label_encoders[col] = le

    target_encoder     = LabelEncoder()
    feat_df["FTR_enc"] = target_encoder.fit_transform(feat_df["FTR"])

    X = feat_df[FEATURE_COLS]
    y = feat_df["FTR_enc"]

    repeat_counts = feat_df["weight"].apply(lambda w: max(1, int(round(w)))).values
    wX = X.loc[X.index.repeat(repeat_counts)].reset_index(drop=True)
    wy = y.loc[y.index.repeat(repeat_counts)].reset_index(drop=True)

    if verbose:
        print(f"  Training model on {len(wX):,} weighted samples...")

    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(
        n_estimators=600,
        max_depth=6,
        min_samples_split=30,
        min_samples_leaf=15,
        max_features="sqrt",
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    rf.fit(wX, wy)

    if verbose:
        print(f"  Done. {len(label_encoders['home_team'].classes_)} unique teams.\n")

    return rf, target_encoder, label_encoders, team_history, FEATURE_COLS

def evaluate_chronological_model(all_data):
    """
    Performs a strict chronological train/test evaluation.
    Training: Seasons up to 2022-2023
    Testing: Seasons 2023-2024 through 2024-2025
    """
    train_seasons = [
        "2012-2013", "2013-2014", "2014-2015", "2015-2016",
        "2016-2017", "2017-2018", "2018-2019", "2019-2020",
        "2020-2021", "2021-2022", "2022-2023"
    ]
    test_seasons = ["2023-2024", "2024-2025"]

    records = all_data.to_dict("records")
    train_records = [r for r in records if r.get("season") in train_seasons]
    test_records = [r for r in records if r.get("season") in test_seasons]

    if not train_records or not test_records:
        print("Warning: Training or testing set is empty based on specified seasons.")
        return

    print(f"Training on {len(train_records)} matches across seasons {train_seasons[0]} to {train_seasons[-1]}...")
    rf, target_enc, label_enc, team_hist, feat_cols = train_model(pd.DataFrame(train_records))

    print(f"Evaluating on {len(test_records)} matches across test seasons...")
    
    X_test, y_test = [], []
    eval_history = {k: list(v) for k, v in team_hist.items()}

    for match in test_records:
        home = match.get("HomeTeam")
        away = match.get("AwayTeam")
        ftr = match.get("FTR")
        season = match.get("season")

        if not home or not away or not ftr:
            continue

        from service import _get_features
        features_df = _get_features(home, away, eval_history, season)
        
        if features_df.empty:
            continue

        X_test.append(features_df.iloc[0].values)
        y_test.append(ftr)

        # Sequentially update history to prevent data leakage
        is_home_win = (ftr == "H")
        is_draw = (ftr == "D")
        hg = match.get("FTHG", 0)
        ag = match.get("FTAG", 0)
        
        if home in eval_history:
            eval_history[home].append(dict(is_home=True, gf=hg, ga=ag, win=is_home_win, draw=is_draw, season=season, date=match.get("date", "sim")))
        if away in eval_history:
            eval_history[away].append(dict(is_home=False, gf=ag, ga=hg, win=(ftr == "A"), draw=is_draw, season=season, date=match.get("date", "sim")))

    if not X_test:
        print("No valid test samples constructed.")
        return

    X_test_arr = np.array(X_test)
    y_test_arr = target_enc.transform(y_test)

    preds = rf.predict(X_test_arr)
    probas = rf.predict_proba(X_test_arr)

    acc = accuracy_score(y_test_arr, preds)
    loss = log_loss(y_test_arr, probas)

    # Multiclass Brier Score calculation
    num_classes = len(target_enc.classes_)
    y_test_onehot = np.eye(num_classes)[y_test_arr]
    brier_score = np.mean(np.sum((probas - y_test_onehot) ** 2, axis=1))

    print("\n=== Chronological Evaluation Results ===")
    print(f"Test Accuracy: {acc:.4f}")
    print(f"Test Log Loss: {loss:.4f}")
    print(f"Multiclass Brier Score: {brier_score:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test_arr, preds, target_names=target_enc.classes_))