import pandas as pd
from src.team_strength import compute_team_strength


def make_teams():
    return pd.DataFrame([
        {"team_id": "A", "final_league_position": 1, "points_per_game_last10": 2.5, "goal_difference": 50, "uefa_coefficient": 100.0},
        {"team_id": "B", "final_league_position": 10, "points_per_game_last10": 1.2, "goal_difference": 0, "uefa_coefficient": 40.0},
        {"team_id": "C", "final_league_position": 20, "points_per_game_last10": 0.5, "goal_difference": -40, "uefa_coefficient": 5.0},
    ])


def test_best_team_has_highest_index():
    result = compute_team_strength(make_teams())
    ordered = result.sort_values("team_strength_index", ascending=False)["team_id"].tolist()
    assert ordered == ["A", "B", "C"]


def test_index_is_bounded_0_to_1():
    result = compute_team_strength(make_teams())
    assert result["team_strength_index"].between(0, 1).all()


def test_identical_teams_do_not_crash_or_divide_by_zero():
    teams = pd.DataFrame([
        {"team_id": "A", "final_league_position": 5, "points_per_game_last10": 1.5, "goal_difference": 10, "uefa_coefficient": 20.0},
        {"team_id": "B", "final_league_position": 5, "points_per_game_last10": 1.5, "goal_difference": 10, "uefa_coefficient": 20.0},
    ])
    result = compute_team_strength(teams)
    assert result["team_strength_index"].notna().all()
    assert (result["team_strength_index"] == 0.5).all()
