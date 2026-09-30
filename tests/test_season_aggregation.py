import math
import pandas as pd
import pytest
from src.season_aggregation import aggregate_season_stats
from src.similarity import SimilarityEngine


def test_season_aggregation_computes_per90_and_pct():
    stats = pd.DataFrame([{
        "player_id": "p1", "season_used": "2025-26",
        "goals": 10, "minutes_played": 900, "matches_played": 10,
        "passes_completed": 400, "passes_attempted": 500,
        "clean_sheets": 3, "goals_prevented": 2.0,
    }])
    players = pd.DataFrame([{"player_id": "p1", "full_name": "Test Player", "primary_position": "ST", "club": "ARS"}])
    teams = pd.DataFrame([{"team_id": "ARS", "big_game_factor_pct": 5.5}])

    result = aggregate_season_stats(stats, players, teams).iloc[0]
    assert result["goals_p90"] == pytest.approx(1.0)  # 10 goals / (900/90)
    assert result["pass_completion_pct"] == pytest.approx(0.8)
    assert result["clean_sheet_pct"] == pytest.approx(0.3)
    assert result["psxg_prevented_p90"] == pytest.approx(0.2)
    assert result["big_game_delta_pct"] == 5.5


def test_save_pct_computed_for_goalkeepers():
    stats = pd.DataFrame([{
        "player_id": "gk1", "season_used": "2025-26",
        "minutes_played": 900, "matches_played": 10,
        "saves": 30, "goals_against": 10,
    }])
    players = pd.DataFrame([{"player_id": "gk1", "full_name": "Test Keeper", "primary_position": "GK", "club": "ARS"}])
    teams = pd.DataFrame([{"team_id": "ARS", "big_game_factor_pct": 0.0}])

    result = aggregate_season_stats(stats, players, teams).iloc[0]
    assert result["save_pct"] == pytest.approx(30 / 40)  # 30 saves out of 40 shots faced


def test_save_pct_is_nan_when_no_shots_faced():
    stats = pd.DataFrame([{
        "player_id": "gk1", "season_used": "2025-26",
        "minutes_played": 90, "matches_played": 1,
        "saves": 0, "goals_against": 0,
    }])
    players = pd.DataFrame([{"player_id": "gk1", "full_name": "Test Keeper", "primary_position": "GK", "club": "ARS"}])
    teams = pd.DataFrame([{"team_id": "ARS", "big_game_factor_pct": 0.0}])

    result = aggregate_season_stats(stats, players, teams).iloc[0]
    assert math.isnan(result["save_pct"])


def test_season_aggregation_missing_fields_become_nan_not_zero():
    stats = pd.DataFrame([{
        "player_id": "p1", "season_used": "2024-25",
        "goals": 5, "minutes_played": 900, "matches_played": 10,
        # xg, xa, progressive_passes etc. deliberately absent (real 2024-25 gap)
    }])
    players = pd.DataFrame([{"player_id": "p1", "full_name": "Test Player", "primary_position": "ST", "club": "ARS"}])
    teams = pd.DataFrame([{"team_id": "ARS", "big_game_factor_pct": 0.0}])

    result = aggregate_season_stats(stats, players, teams).iloc[0]
    assert math.isnan(result["xg_p90"])
    assert math.isnan(result["dribble_success_pct"])


def test_similarity_skips_unavailable_stats_instead_of_breaking():
    config = {
        "ST": {
            "stats": {
                "goals_p90": {"weight": 1.0, "direction": 1},
                "xg_p90": {"weight": 1.0, "direction": 1},
            },
            "big_game_composite_stats": [],
        }
    }
    # xg_p90 is NaN for both players (simulating the 2024-25 data gap)
    df = pd.DataFrame([
        {"player_id": "a", "primary_position": "ST", "goals_p90": 0.5, "xg_p90": float("nan")},
        {"player_id": "b", "primary_position": "ST", "goals_p90": 0.5, "xg_p90": float("nan")},
        {"player_id": "c", "primary_position": "ST", "goals_p90": 0.9, "xg_p90": float("nan")},
    ])
    engine = SimilarityEngine(config).fit(df)

    result = engine.explain_score(df.iloc[0], df.iloc[1])
    assert result["match_score"] == 100.0  # identical on the only available stat
    assert result["stats_unavailable"] == 1
    assert result["stats_compared"] == 1

    # still works, and still discriminates, when one stat is simply missing everywhere
    result2 = engine.explain_score(df.iloc[0], df.iloc[2])
    assert result2["match_score"] < 100.0
