"""
There's no labeled "this replacement worked out" data to compute
precision/recall against yet, so these are the sanity and monitoring
metrics used instead:

  - data_completeness:      are the source CSVs actually filled in
  - position_separation:    does the similarity engine actually tell
                             positions apart (a CB profile should look
                             more like other CBs than like strikers)
  - weight_sensitivity:     how much a match score moves under small,
                             random nudges to the stat weights (a very
                             unstable score means the weighting is too
                             sensitive to be trusted)
  - score_distribution:     are match scores spread out sensibly, or
                             bunched up in a way that makes the %
                             meaningless

Once real transfer/scouting outcomes exist, replace or add to this
with a proper accuracy metric (e.g. Spearman correlation between
match_score and human-judged similarity).
"""

import random
import statistics
import pandas as pd


def data_completeness(df: pd.DataFrame, required_cols: list[str]) -> dict:
    """Returns the fraction (0-1) of non-null values per required column."""
    result = {}
    for col in required_cols:
        if col not in df.columns:
            result[col] = 0.0
        else:
            result[col] = float(df[col].notna().mean())
    return result


def position_separation(
    player_stats_df: pd.DataFrame,
    engine,
    max_pairs_per_position: int = 30,
    seed: int = 42,
    n_trials: int = 1,
) -> dict:
    """
    For each position with at least 2 players, compares the average
    match_score between two players of that position (within) against
    the average match_score between a player of that position and a
    random player from a different position (cross), both scored using
    the same position's stat config. within should be clearly higher
    than cross if the model is capturing real positional signal.

    n_trials > 1 repeats the sampling across that many seeds and pools
    every trial's scores before averaging, for a more stable estimate -
    a single trial at max_pairs_per_position=30 can swing the separation
    ratio by several tenths purely from sampling noise on positions with
    a modest population (see README "Model validation").
    """
    results = {}

    for position in player_stats_df["primary_position"].unique():
        same_pos = player_stats_df[player_stats_df["primary_position"] == position]
        other_pos = player_stats_df[player_stats_df["primary_position"] != position]
        if len(same_pos) < 2 or other_pos.empty:
            continue

        within_scores = []
        cross_scores = []
        same_pos_records = same_pos.to_dict("records")

        for trial in range(n_trials):
            rng = random.Random(seed + trial)
            for _ in range(max_pairs_per_position):
                a, b = rng.sample(same_pos_records, 2)
                within_scores.append(engine.match_score(pd.Series(a), pd.Series(b), position))

                a = rng.choice(same_pos_records)
                b = other_pos.sample(1, random_state=rng.randint(0, 10_000)).iloc[0]
                cross_scores.append(engine.match_score(pd.Series(a), b, position))

        within_avg = statistics.mean(within_scores)
        cross_avg = statistics.mean(cross_scores)
        results[position] = {
            "within_position_avg_score": round(within_avg, 1),
            "cross_position_avg_score": round(cross_avg, 1),
            "separation_ratio": round(within_avg / cross_avg, 2) if cross_avg else None,
        }

    return results


def weight_sensitivity(
    engine_factory,
    position_config: dict,
    player_a: pd.Series,
    player_b: pd.Series,
    position: str,
    perturbation: float = 0.1,
    n_trials: int = 20,
    seed: int = 42,
) -> dict:
    """
    Recomputes the match score n_trials times, each time nudging every
    weight for `position` up or down by up to `perturbation` (fraction),
    to see how stable the resulting score is. engine_factory() must
    return a freshly-fitted SimilarityEngine for the perturbed config.
    """
    rng = random.Random(seed)
    scores = []

    for _ in range(n_trials):
        perturbed_config = {
            k: {"stats": {}, **{ck: cv for ck, cv in v.items() if ck != "stats"}}
            for k, v in position_config.items()
        }
        for pos, spec in position_config.items():
            for stat, stat_spec in spec.get("stats", {}).items():
                factor = 1 + rng.uniform(-perturbation, perturbation)
                perturbed_config[pos]["stats"][stat] = {
                    "weight": max(0.0, stat_spec["weight"] * factor),
                    "direction": stat_spec.get("direction", 1),
                }

        engine = engine_factory(perturbed_config)
        scores.append(engine.match_score(player_a, player_b, position))

    return {
        "mean_score": round(statistics.mean(scores), 1),
        "stdev": round(statistics.pstdev(scores), 2),
        "min": round(min(scores), 1),
        "max": round(max(scores), 1),
    }


def score_distribution(scores: list[float]) -> dict:
    """Basic spread check: a healthy set of match scores shouldn't all bunch near one value."""
    if not scores:
        return {"count": 0}
    return {
        "count": len(scores),
        "mean": round(statistics.mean(scores), 1),
        "stdev": round(statistics.pstdev(scores), 2) if len(scores) > 1 else 0.0,
        "min": round(min(scores), 1),
        "max": round(max(scores), 1),
    }
