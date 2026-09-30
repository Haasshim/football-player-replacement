import pandas as pd
import pytest
from src.player_aggregation import aggregate_player_stats

REQUIRED_RAW_COLS = [
    "goals", "assists", "xg", "xa", "shots", "shots_on_target", "key_passes",
    "passes_completed", "passes_attempted", "progressive_passes", "progressive_carries",
    "dribbles_completed", "dribbles_attempted", "times_dribbled_past", "tackles",
    "tackles_won", "interceptions", "blocks", "clearances", "aerial_duels_won",
    "aerial_duels_total", "duels_won", "duels_total", "recoveries", "fouls_committed",
    "crosses_completed", "crosses_attempted", "through_balls", "touches_in_box",
    "passes_long_completed", "passes_long_attempted", "saves", "goals_against",
    "post_shot_xg", "clean_sheet",
]


def blank_row(**overrides):
    row = {col: 0 for col in REQUIRED_RAW_COLS}
    row["clean_sheet"] = False
    row.update(overrides)
    return row


def test_weighted_per90_and_pct_stats():
    stats = pd.DataFrame([
        blank_row(fixture_id="F1", player_id="p1", team_id="A", minutes_played=90,
                  match_weight=1.0, goals=1, xg=0.8, passes_completed=20, passes_attempted=25),
        blank_row(fixture_id="F2", player_id="p1", team_id="A", minutes_played=90,
                  match_weight=2.0, goals=2, xg=1.6, passes_completed=15, passes_attempted=20),
    ])
    players = pd.DataFrame([{"player_id": "p1", "full_name": "Test Player", "primary_position": "ST", "club": "A"}])
    position_config = {"ST": {"big_game_composite_stats": ["xg_p90", "goals_p90"]}}

    result = aggregate_player_stats(stats, players, position_config).iloc[0]

    assert result["goals_p90"] == pytest.approx(5 / 3, rel=1e-3)
    assert result["pass_completion_pct"] == pytest.approx(50 / 65, rel=1e-3)
    assert result["big_game_delta_pct"] == pytest.approx((3.0 - 2.7) / 2.7 * 100, rel=1e-3)


def test_big_game_delta_is_zero_when_no_composite_configured():
    stats = pd.DataFrame([
        blank_row(fixture_id="F1", player_id="p1", team_id="A", minutes_played=90, match_weight=1.0, goals=1),
    ])
    players = pd.DataFrame([{"player_id": "p1", "full_name": "Test Player", "primary_position": "CB", "club": "A"}])
    result = aggregate_player_stats(stats, players, {"CB": {"big_game_composite_stats": []}}).iloc[0]
    assert result["big_game_delta_pct"] == 0.0


def test_player_not_in_players_table_is_skipped():
    stats = pd.DataFrame([
        blank_row(fixture_id="F1", player_id="ghost", team_id="A", minutes_played=90, match_weight=1.0),
    ])
    players = pd.DataFrame([{"player_id": "p1", "full_name": "Test Player", "primary_position": "CB", "club": "A"}])
    result = aggregate_player_stats(stats, players, {"CB": {"big_game_composite_stats": []}})
    assert result.empty
