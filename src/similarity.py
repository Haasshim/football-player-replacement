"""
Turns two players' aggregated stat profiles (from player_aggregation.py)
into a single 0-100% match score, plus a per-stat breakdown for the
comparison UI.

Method: within each position group, every configured stat is z-score
normalized across all players at that position. The two players'
weighted z-score vectors are compared with a weighted distance; the
distance is mapped to a bounded 0-100% score.

This is a statistical comparison, not a trained model: there's no
labeled "good replacement" data to fit against yet. See metrics.py for
sanity checks (position separation, weight sensitivity) that stand in
for accuracy metrics until real outcome data exists.
"""

import math
import pandas as pd

DISTANCE_SCALE = 1.4  # tunable: controls how quickly score falls off with distance


class SimilarityEngine:
    def __init__(self, position_config: dict):
        self.position_config = position_config
        self._position_stats: dict[str, dict[str, tuple[float, float]]] = {}
        self._fitted = False

    def fit(self, player_stats_df: pd.DataFrame) -> "SimilarityEngine":
        """
        Computes per-position mean/std for every stat that position's
        config lists, across all players currently in player_stats_df.
        NaN values (a stat genuinely not available from the data source
        for some players) are skipped automatically by pandas mean/std.
        """
        for position, config in self.position_config.items():
            stat_names = list(config.get("stats", {}).keys())
            group = player_stats_df[player_stats_df["primary_position"] == position]
            stats = {}
            for stat in stat_names:
                if stat not in group.columns or group[stat].dropna().empty:
                    stats[stat] = (0.0, 1.0)
                    continue
                mean = group[stat].mean(skipna=True)
                std = group[stat].std(skipna=True)
                stats[stat] = (float(mean), float(std) if std and not math.isnan(std) else 1.0)
            self._position_stats[position] = stats
        self._fitted = True
        return self

    def _z(self, position: str, stat: str, value: float) -> float:
        mean, std = self._position_stats.get(position, {}).get(stat, (0.0, 1.0))
        std = std if std else 1.0
        return (value - mean) / std

    def explain_score(self, player_a: pd.Series, player_b: pd.Series, position: str | None = None) -> dict:
        """
        Returns the match score plus a per-stat breakdown, sorted by how
        much each stat is currently pulling the two players apart.
        Uses player_a's position's stat config (player_a is treated as
        the player being replaced; player_b is the candidate).
        """
        if not self._fitted:
            raise RuntimeError("call fit() before scoring")

        position = position or player_a["primary_position"]
        config = self.position_config.get(position, {}).get("stats", {})
        if not config:
            raise ValueError(f"no stat config for position: {position}")

        breakdown = []
        weighted_sq_diff_sum = 0.0
        weight_sum = 0.0

        for stat, spec in config.items():
            weight = spec["weight"]
            direction = spec.get("direction", 1)
            val_a = player_a.get(stat, float("nan"))
            val_b = player_b.get(stat, float("nan"))
            val_a = float(val_a) if val_a is not None else float("nan")
            val_b = float(val_b) if val_b is not None else float("nan")

            if math.isnan(val_a) or math.isnan(val_b):
                # stat unavailable for one or both players (real-world data
                # gap) - skip its contribution rather than poisoning the score
                breakdown.append({
                    "stat": stat, "weight": weight, "direction": direction,
                    "player_a_value": val_a, "player_b_value": val_b,
                    "z_diff": None, "favored": "unavailable",
                })
                continue

            za = self._z(position, stat, val_a)
            zb = self._z(position, stat, val_b)
            sq_diff = (za - zb) ** 2

            weighted_sq_diff_sum += weight * sq_diff
            weight_sum += weight

            favored = "a" if (za - zb) * direction > 0 else ("b" if (za - zb) * direction < 0 else "tie")
            breakdown.append({
                "stat": stat,
                "weight": weight,
                "direction": direction,
                "player_a_value": val_a,
                "player_b_value": val_b,
                "z_diff": za - zb,
                "favored": favored,
            })

        raw_distance = math.sqrt(weighted_sq_diff_sum / weight_sum) if weight_sum else 0.0
        score = 100 * math.exp(-raw_distance / DISTANCE_SCALE)
        score = max(0.0, min(100.0, score))

        breakdown.sort(key=lambda r: r["weight"] * abs(r["z_diff"]) if r["z_diff"] is not None else -1, reverse=True)

        return {
            "position_used": position,
            "match_score": round(score, 1),
            "raw_distance": round(raw_distance, 3),
            "stat_breakdown": breakdown,
            "stats_compared": sum(1 for r in breakdown if r["favored"] != "unavailable"),
            "stats_unavailable": sum(1 for r in breakdown if r["favored"] == "unavailable"),
        }

    def match_score(self, player_a: pd.Series, player_b: pd.Series, position: str | None = None) -> float:
        return self.explain_score(player_a, player_b, position)["match_score"]

    def rank_candidates(
        self,
        target_player: pd.Series,
        candidates_df: pd.DataFrame,
        position: str | None = None,
    ) -> pd.DataFrame:
        """
        Scores every row in candidates_df against target_player and
        returns candidates_df with a match_score column, sorted best-first.
        This is the "who is the best replacement" lookup.
        """
        scores = candidates_df.apply(
            lambda row: self.match_score(target_player, row, position), axis=1
        )
        result = candidates_df.copy()
        result["match_score"] = scores
        return result.sort_values("match_score", ascending=False)
