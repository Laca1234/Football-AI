# service.py — prediction and simulation business logic

from itertools import permutations
from collections import defaultdict
import copy

import numpy as np
import pandas as pd

from model import FEATURE_COLS, FORM_WINDOW, LONG_WINDOW
from logger import log_event

NOISE_STD = 0.035


# ─── Form helpers ─────────────────────────────────────────────────────────────

def _team_stats(hist, window):
    recent = hist[-window:]
    if not recent:
        return dict(w=0, d=0, l=0, avg_gf=1.2, avg_ga=1.0, wr=0.33)
    w  = sum(1 for h in recent if h["win"])
    d  = sum(1 for h in recent if h["draw"])
    l  = len(recent) - w - d
    gf = float(np.mean([h["gf"] for h in recent]))
    ga = float(np.mean([h["ga"] for h in recent]))
    return dict(w=w, d=d, l=l, avg_gf=gf, avg_ga=ga, wr=w / len(recent))


def _get_features(home: str, away: str, team_history: dict,
                  current_season: str) -> pd.DataFrame:
    h_hist = team_history.get(home, [])
    a_hist = team_history.get(away, [])

    hf5  = _team_stats(h_hist, FORM_WINDOW)
    af5  = _team_stats(a_hist, FORM_WINDOW)

    h_home = [h for h in h_hist if h["is_home"]]
    a_away = [h for h in a_hist if not h["is_home"]]
    hf5v = _team_stats(h_home, FORM_WINDOW)
    af5v = _team_stats(a_away, FORM_WINDOW)

    hf38 = _team_stats(h_hist, LONG_WINDOW)
    af38 = _team_stats(a_hist, LONG_WINDOW)

    h_szn = [h for h in h_hist if h["season"] == current_season]
    a_szn = [h for h in a_hist if h["season"] == current_season]
    h_szn_gf = float(np.mean([h["gf"] for h in h_szn])) if h_szn else 1.2
    h_szn_ga = float(np.mean([h["ga"] for h in h_szn])) if h_szn else 1.0
    a_szn_gf = float(np.mean([h["gf"] for h in a_szn])) if a_szn else 1.2
    a_szn_ga = float(np.mean([h["ga"] for h in a_szn])) if a_szn else 1.0

    row = {
        "h_w5": hf5["w"],  "h_d5": hf5["d"],  "h_l5": hf5["l"],
        "h_gf5": hf5["avg_gf"], "h_ga5": hf5["avg_ga"],
        "a_w5": af5["w"],  "a_d5": af5["d"],  "a_l5": af5["l"],
        "a_gf5": af5["avg_gf"], "a_ga5": af5["avg_ga"],
        "h_home_w5": hf5v["w"],  "h_home_d5": hf5v["d"],  "h_home_l5": hf5v["l"],
        "h_home_gf5": hf5v["avg_gf"], "h_home_ga5": hf5v["avg_ga"],
        "a_away_w5": af5v["w"],  "a_away_d5": af5v["d"],  "a_away_l5": af5v["l"],
        "a_away_gf5": af5v["avg_gf"], "a_away_ga5": af5v["avg_ga"],
        "h_wr38": hf38["wr"],  "h_gf38": hf38["avg_gf"], "h_ga38": hf38["avg_ga"],
        "a_wr38": af38["wr"],  "a_gf38": af38["avg_gf"], "a_ga38": af38["avg_ga"],
        "h_season_gf": h_szn_gf, "h_season_ga": h_szn_ga,
        "a_season_gf": a_szn_gf, "a_season_ga": a_szn_ga,
    }
    return pd.DataFrame([row], columns=FEATURE_COLS)


# ─── Prediction ───────────────────────────────────────────────────────────────

def predict_match(home: str, away: str, rf, target_encoder,
                  label_encoders: dict, team_history: dict,
                  current_season: str, noise: bool = True) -> dict | None:
    known = set(label_encoders["home_team"].classes_)
    if home not in known or away not in known:
        return None

    X     = _get_features(home, away, team_history, current_season)
    proba = rf.predict_proba(X)[0]

    # Smooth toward uniform to prevent overconfident splits
    proba = proba * 0.88 + 0.12 / 3

    proba /= proba.sum()
    return dict(zip(target_encoder.classes_, proba.tolist()))


# ─── Season simulation ────────────────────────────────────────────────────────

def _update_history(sim_history, team, is_home, gf, ga, ftr, season):
    sim_history[team].append(dict(
        is_home=is_home, gf=gf, ga=ga,
        win=(ftr == "H" if is_home else ftr == "A"),
        draw=(ftr == "D"),
        season=season, date="sim",
    ))


def simulate_season(teams: list, rf, target_encoder,
                    label_encoders: dict, team_history: dict,
                    current_season: str) -> list:
    log_event("simulate_season started")
    sim_history = copy.deepcopy(team_history)
    fixtures    = list(permutations(teams, 2))
    np.random.shuffle(fixtures)

    points = defaultdict(int)
    wins   = defaultdict(int)
    draws  = defaultdict(int)
    losses = defaultdict(int)
    gf_tot = defaultdict(int)
    ga_tot = defaultdict(int)

    for home, away in fixtures:
        X     = _get_features(home, away, sim_history, current_season)
        proba = rf.predict_proba(X)[0]
        proba = np.power(proba, 2.3)
        proba += np.random.normal(0, NOISE_STD, size=len(proba))
        proba  = np.clip(proba, 0.001, None)
        proba /= proba.sum()
        draw_idx = list(target_encoder.classes_).index("D")
        squeeze_factor = 0.50 # Reduce draws by 25%
        squeezed_val = proba[draw_idx] * squeeze_factor
        proba[draw_idx] -= squeezed_val

        # 4. Weighted Redistribution (The "Closer" Logic)
        h_idx = list(target_encoder.classes_).index("H")
        a_idx = list(target_encoder.classes_).index("A")

        if proba[h_idx] > proba[a_idx]:
            # Home is favorite: gets 80% of the squeezed draw points
            proba[h_idx] += squeezed_val * 0.8
            proba[a_idx] += squeezed_val * 0.2
        else:
            # Away is favorite: gets 80% of the squeezed draw points
            proba[a_idx] += squeezed_val * 0.8
            proba[h_idx] += squeezed_val * 0.2
        
        # Final normalization to ensure it equals 1.0 exactly
        proba /= proba.sum()
        probs = dict(zip(target_encoder.classes_, proba.tolist()))

        # 5. Pick the outcome
        outcome = np.random.choice(
            ["H", "D", "A"], p=[probs["H"], probs["D"], probs["A"]]
        )


        # xG from long-term scoring rate (stable, not affected by sim variance)
        h38 = _team_stats(sim_history.get(home, []), LONG_WINDOW)
        a38 = _team_stats(sim_history.get(away, []), LONG_WINDOW)
        h_quality = h38["wr"]
        a_quality = a38["wr"]

        # If there is a massive quality gap (e.g., Arsenal vs Ipswich)
        if abs(h_quality - a_quality) > 0.35:
            if h_quality > a_quality:
                probs["H"] *= 1.35  # 15% boost to favorite
            else:
                probs["A"] *= 1.35
            # Re-normalize dict values
            total = sum(probs.values())
            probs = {k: v/total for k, v in probs.items()}
        hg  = min(int(np.random.poisson(max(h38["avg_gf"], 1.0))), 7)
        ag  = min(int(np.random.poisson(max(a38["avg_gf"], 1.0))), 7)
        # Strength check: compare long-term win rates


        if outcome == "H" and hg <= ag:
            hg = ag + np.random.randint(1, 3)
        elif outcome == "A" and ag <= hg:
            ag = hg + np.random.randint(1, 3)
        elif outcome == "D":
            draw_score = max(hg, ag) 
            hg = ag = draw_score

        if hg > ag:
            ftr = "H"
            points[home] += 3; wins[home] += 1; losses[away] += 1
        elif ag > hg:
            ftr = "A"
            points[away] += 3; wins[away] += 1; losses[home] += 1
        else:
            ftr = "D"
            points[home] += 1; points[away] += 1
            draws[home]  += 1; draws[away]  += 1

        gf_tot[home] += hg; ga_tot[home] += ag
        gf_tot[away] += ag; ga_tot[away] += hg

        _update_history(sim_history, home, True,  hg, ag, ftr, current_season)
        _update_history(sim_history, away, False, ag, hg, ftr, current_season)

    standings = sorted(
        teams,
        key=lambda t: (points[t], gf_tot[t] - ga_tot[t], gf_tot[t]),
        reverse=True,
    )
    log_event("simulate_season finished")
    return [
        {
            "pos": i + 1, "team": t,
            "pts": points[t], "w": wins[t], "d": draws[t], "l": losses[t],
            "gf": gf_tot[t],  "ga": ga_tot[t], "gd": gf_tot[t] - ga_tot[t],
        }
        for i, t in enumerate(standings)
    ]