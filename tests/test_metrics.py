import pandas as pd
import pytest
from src import metrics as m
from src.similarity import SimilarityEngine


def test_data_completeness_basic():
    df = pd.DataFrame({"a": [1, 2, None], "b": [None, None, None]})
    result = m.data_completeness(df, ["a", "b", "missing_col"])
    assert result["a"] == pytest.approx(2 / 3, rel=1e-3)
    assert result["b"] == 0.0
    assert result["missing_col"] == 0.0


def test_position_separation_runs_and_returns_expected_keys():
    config = {
        "ST": {"stats": {"stat1": {"weight": 1.0, "direction": 1}}, "big_game_composite_stats": []},
        "CB": {"stats": {"stat1": {"weight": 1.0, "direction": 1}}, "big_game_composite_stats": []},
    }
    df = pd.DataFrame([
        {"player_id": "p1", "primary_position": "ST", "stat1": 10},
        {"player_id": "p2", "primary_position": "ST", "stat1": 12},
        {"player_id": "p3", "primary_position": "CB", "stat1": 1},
        {"player_id": "p4", "primary_position": "CB", "stat1": 2},
    ])
    engine = SimilarityEngine(config).fit(df)
    result = m.position_separation(df, engine, max_pairs_per_position=5)
    assert "ST" in result and "CB" in result
    assert "within_position_avg_score" in result["ST"]
    assert "cross_position_avg_score" in result["ST"]


def test_score_distribution_basic():
    result = m.score_distribution([80, 90, 70, 100])
    assert result["count"] == 4
    assert result["mean"] == 85.0
    assert result["min"] == 70
    assert result["max"] == 100


def test_score_distribution_handles_empty_list():
    assert m.score_distribution([])["count"] == 0
