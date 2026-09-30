import pandas as pd
from src.opponent_weighting import compute_match_weights, DEFAULT_K


def test_weight_is_higher_against_a_stronger_opponent():
    teams = pd.DataFrame([
        {"team_id": "STRONG", "team_strength_index": 1.0},
        {"team_id": "WEAK", "team_strength_index": 0.2},
        {"team_id": "MID", "team_strength_index": 0.5},
    ])
    fixtures = pd.DataFrame([
        {"fixture_id": "F1", "home_team_id": "MID", "away_team_id": "STRONG"},
        {"fixture_id": "F2", "home_team_id": "MID", "away_team_id": "WEAK"},
    ])
    stats = pd.DataFrame([
        {"fixture_id": "F1", "player_id": "P1", "team_id": "MID", "minutes_played": 90},
        {"fixture_id": "F2", "player_id": "P1", "team_id": "MID", "minutes_played": 90},
    ])

    result = compute_match_weights(stats, fixtures, teams)
    vs_strong = result.loc[result["fixture_id"] == "F1", "match_weight"].iloc[0]
    vs_weak = result.loc[result["fixture_id"] == "F2", "match_weight"].iloc[0]

    assert vs_strong > vs_weak


def test_fewer_minutes_reduces_weight():
    teams = pd.DataFrame([
        {"team_id": "A", "team_strength_index": 0.5},
        {"team_id": "B", "team_strength_index": 0.5},
    ])
    fixtures = pd.DataFrame([{"fixture_id": "F1", "home_team_id": "A", "away_team_id": "B"}])
    stats = pd.DataFrame([
        {"fixture_id": "F1", "player_id": "FULL_GAME", "team_id": "A", "minutes_played": 90},
        {"fixture_id": "F1", "player_id": "SUB", "team_id": "A", "minutes_played": 10},
    ])
    result = compute_match_weights(stats, fixtures, teams)
    full = result.loc[result["player_id"] == "FULL_GAME", "match_weight"].iloc[0]
    sub = result.loc[result["player_id"] == "SUB", "match_weight"].iloc[0]
    assert full > sub


def test_equal_strength_gives_no_difficulty_bonus():
    teams = pd.DataFrame([
        {"team_id": "A", "team_strength_index": 0.6},
        {"team_id": "B", "team_strength_index": 0.6},
    ])
    fixtures = pd.DataFrame([{"fixture_id": "F1", "home_team_id": "A", "away_team_id": "B"}])
    stats = pd.DataFrame([{"fixture_id": "F1", "player_id": "P1", "team_id": "A", "minutes_played": 90}])
    result = compute_match_weights(stats, fixtures, teams, k=DEFAULT_K)
    assert result["match_weight"].iloc[0] == 1.0
