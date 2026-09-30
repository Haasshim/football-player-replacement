"""
Runs the full pipeline end to end against whatever is in data/, and
writes frontend/data.json for the UI to consume.

Usage: python scripts/run_pipeline.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data_loader import load_data
from src.team_strength import compute_team_strength
from src.opponent_weighting import compute_match_weights
from src.player_aggregation import aggregate_player_stats
from src.similarity import SimilarityEngine
from src import metrics as m


def main():
    tables = load_data(ROOT / "data")
    position_config = json.loads((ROOT / "src" / "config" / "position_weights.json").read_text())
    position_config = {k: v for k, v in position_config.items() if not k.startswith("_")}

    teams_with_strength = compute_team_strength(tables["teams"])
    weighted_matches = compute_match_weights(tables["player_match_stats"], tables["fixtures"], teams_with_strength)
    player_stats = aggregate_player_stats(weighted_matches, tables["players"], position_config)

    engine = SimilarityEngine(position_config).fit(player_stats)

    print("== data completeness (player_match_stats) ==")
    from src.data_loader import REQUIRED_COLUMNS
    completeness = m.data_completeness(tables["player_match_stats"], REQUIRED_COLUMNS["player_match_stats.csv"])
    worst = sorted(completeness.items(), key=lambda kv: kv[1])[:5]
    print("lowest-completeness columns:", worst)

    print("\n== position separation (within vs cross, higher separation_ratio is better) ==")
    sep = m.position_separation(player_stats, engine)
    for pos, res in sep.items():
        print(f"  {pos}: {res}")

    print("\n== score distribution across a sample of same-position pairs ==")
    import random
    rng = random.Random(1)
    sample_scores = []
    for _ in range(150):
        pos = rng.choice(list(position_config.keys()))
        pool = player_stats[player_stats["primary_position"] == pos]
        if len(pool) < 2:
            continue
        a, b = pool.sample(2, random_state=rng.randint(0, 9999)).iloc[0], pool.sample(1, random_state=rng.randint(0, 9999)).iloc[0]
        sample_scores.append(engine.match_score(a, b, pos))
    print(" ", m.score_distribution(sample_scores))

    export = {
        "teams": teams_with_strength.to_dict("records"),
        "players": player_stats.to_dict("records"),
        "position_config": position_config,
    }
    out_path = ROOT / "frontend" / "data.json"
    out_path.write_text(json.dumps(export, indent=2, default=str))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
