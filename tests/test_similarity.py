import math
import pandas as pd
import pytest
from src.similarity import SimilarityEngine

POSITION_CONFIG = {
    "ST": {
        "stats": {
            "stat1": {"weight": 1.0, "direction": 1},
            "stat2": {"weight": 1.0, "direction": 1},
        },
        "big_game_composite_stats": [],
    }
}


def make_player_stats():
    # stat1: 10, 10, 20, 30 -> mean 17.5, sample std 9.5743
    # stat2: constant 5 -> zero variance (std falls back to 1, contributes nothing)
    return pd.DataFrame([
        {"player_id": "p1", "primary_position": "ST", "stat1": 10, "stat2": 5},
        {"player_id": "p2", "primary_position": "ST", "stat1": 10, "stat2": 5},
        {"player_id": "p3", "primary_position": "ST", "stat1": 20, "stat2": 5},
        {"player_id": "p4", "primary_position": "ST", "stat1": 30, "stat2": 5},
    ])


def test_identical_players_score_100():
    df = make_player_stats()
    engine = SimilarityEngine(POSITION_CONFIG).fit(df)
    p1, p2 = df.iloc[0], df.iloc[1]
    assert engine.match_score(p1, p2) == 100.0


def test_more_different_players_score_lower():
    df = make_player_stats()
    engine = SimilarityEngine(POSITION_CONFIG).fit(df)
    p1, p3, p4 = df.iloc[0], df.iloc[2], df.iloc[3]

    score_p1_p3 = engine.match_score(p1, p3)
    score_p1_p4 = engine.match_score(p1, p4)

    assert score_p1_p3 == pytest.approx(69.1, abs=0.5)
    assert score_p1_p4 == pytest.approx(47.8, abs=0.5)
    assert score_p1_p4 < score_p1_p3 < 100.0


def test_raw_distance_matches_hand_calculation():
    df = make_player_stats()
    engine = SimilarityEngine(POSITION_CONFIG).fit(df)
    p1, p3 = df.iloc[0], df.iloc[2]
    result = engine.explain_score(p1, p3)
    # mean=17.5, sample std=9.5743: z(p1)=-0.7833, z(p3)=0.2611, sq diff=1.0908
    # averaged over 2 equally-weighted stats (stat2 contributes 0) -> sqrt(1.0908/2)
    assert result["raw_distance"] == pytest.approx(math.sqrt(1.0908 / 2), abs=0.005)


def test_explain_score_flags_who_is_favored():
    df = make_player_stats()
    engine = SimilarityEngine(POSITION_CONFIG).fit(df)
    p1, p3 = df.iloc[0], df.iloc[2]  # p3 has the higher stat1
    result = engine.explain_score(p1, p3)
    stat1_row = next(r for r in result["stat_breakdown"] if r["stat"] == "stat1")
    assert stat1_row["favored"] == "b"


def test_rank_candidates_orders_best_first():
    df = make_player_stats()
    engine = SimilarityEngine(POSITION_CONFIG).fit(df)
    target = df.iloc[0]  # p1
    candidates = df.iloc[1:]  # p2, p3, p4
    ranked = engine.rank_candidates(target, candidates)
    assert ranked["player_id"].tolist() == ["p2", "p3", "p4"]


def test_scoring_before_fit_raises():
    engine = SimilarityEngine(POSITION_CONFIG)
    df = make_player_stats()
    with pytest.raises(RuntimeError):
        engine.match_score(df.iloc[0], df.iloc[1])
