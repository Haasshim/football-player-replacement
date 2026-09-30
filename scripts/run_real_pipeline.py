"""
Runs the pipeline against the real data in data/ (teams.csv, players.csv,
player_season_stats.csv, produced by scripts/real_data/build_final_dataset.py)
instead of the synthetic sample data. Writes frontend/data.json.

Usage: python scripts/run_real_pipeline.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from src.team_strength import compute_team_strength
from src.season_aggregation import aggregate_season_stats
from src.similarity import SimilarityEngine
from src import metrics as m


def main():
    data_dir = ROOT / "data"
    teams = pd.read_csv(data_dir / "teams.csv")
    players = pd.read_csv(data_dir / "players.csv")
    season_stats = pd.read_csv(data_dir / "player_season_stats.csv")

    position_config = json.loads((ROOT / "src" / "config" / "position_weights.json").read_text())
    position_config = {k: v for k, v in position_config.items() if not k.startswith("_")}

    teams_with_strength = compute_team_strength(teams)
    player_stats = aggregate_season_stats(season_stats, players, teams_with_strength)

    # fit and validate on players who actually have real stats - padding in
    # bio-only players (no stat row at all) would make metrics meaningless,
    # since their comparisons would rest almost entirely on the one team-level
    # stat every player has (big_game_delta_pct), not genuine performance data
    engine = SimilarityEngine(position_config).fit(player_stats)

    print("== data completeness (players.csv) ==")
    completeness = m.data_completeness(players, ["date_of_birth", "nationality", "market_value"])
    print(" ", completeness)
    print("  data_confidence breakdown:", players["data_confidence"].value_counts().to_dict())

    print("\n== position separation (within vs cross, higher is better) ==")
    sep = m.position_separation(player_stats, engine, max_pairs_per_position=40, n_trials=8)
    for pos, res in sep.items():
        print(f"  {pos}: {res}")

    print("\n== score distribution across a sample of same-position pairs ==")
    import random
    rng = random.Random(1)
    sample_scores = []
    for _ in range(200):
        pos = rng.choice(list(position_config.keys()))
        pool = player_stats[player_stats["primary_position"] == pos]
        if len(pool) < 2:
            continue
        a = pool.sample(1, random_state=rng.randint(0, 9999)).iloc[0]
        b = pool.sample(1, random_state=rng.randint(0, 9999)).iloc[0]
        if a["player_id"] == b["player_id"]:
            continue
        sample_scores.append(engine.match_score(a, b, pos))
    print(" ", m.score_distribution(sample_scores))

    # NOW pad in bio-only players (no stat row) so the frontend's squad view
    # can still show and flag them, per the "show everyone, flag low-data"
    # decision - they just take no part in the metrics above
    stats_covered_ids = set(player_stats["player_id"])
    missing = players[~players["player_id"].isin(stats_covered_ids)].copy()
    if not missing.empty:
        for col in player_stats.columns:
            if col not in missing.columns:
                missing[col] = float("nan")
        missing["big_game_delta_pct"] = missing["club"].map(
            teams_with_strength.set_index("team_id")["big_game_factor_pct"]
        )
        player_stats = pd.concat([player_stats, missing[player_stats.columns]], ignore_index=True)

    # merge in bio fields the frontend needs (date_of_birth, nationality, etc.)
    bio_cols = ["player_id", "date_of_birth", "nationality", "market_value",
                "data_confidence", "low_minutes_flag", "stat_season_used",
                "home_grown", "squad_tier"]
    player_stats = player_stats.merge(players[bio_cols], on="player_id", how="left")

    def clean_json(df):
        return json.loads(df.to_json(orient="records"))

    export = {
        "teams": clean_json(teams_with_strength),
        "players": clean_json(player_stats),
        "position_config": position_config,
    }
    out_path = ROOT / "frontend" / "data.json"
    out_path.write_text(json.dumps(export, indent=2, default=str))
    print(f"\nwrote {out_path} ({len(player_stats)} players, {len(teams_with_strength)} teams)")


if __name__ == "__main__":
    main()
