# Data folder: real 2026/27 EPL data

Everything in this folder is now real, not placeholder. It was built by
the scripts in `scripts/real_data/` from:

- the 2026/27 Premier League squad list (current rosters, 20 clubs)
- archive 5 (player bios and fine-grained positions, filtered to seasons
  2022-2026)
- two seasons of player performance stats (2024-25 and 2025-26)
- match results for 2021/22-2024/25 (standings and a team-level
  "big game" factor)

See the main README for the full pipeline write-up and known
limitations. This file just documents the columns.

## teams.csv

| Column | Notes |
|---|---|
| team_id | short code, e.g. `ARS` |
| team_name | full club name |
| league | always `EPL` |
| final_league_position | recency-weighted blend of the last 3-4 seasons (not last season alone) |
| points | same blend |
| goal_difference | same blend |
| points_per_game_last10 | approximated as points / 38, since match-by-match recent-10 data wasn't available |
| big_game_factor_pct | how much better (positive) or worse (negative) the team's points-per-game against top-half opponents was, versus what their overall season form would predict. See README. |
| data_confidence | `recency_weighted_<seasons>` normally, or `no_recent_top_flight_data` for clubs with zero match data in our archives (this season's newly promoted Coventry, Hull, Sunderland) |
| uefa_coefficient | real five-year club coefficient where found; otherwise the UEFA-defined national floor (see README) |

## players.csv

| Column | Notes |
|---|---|
| player_id | generated from the player's resolved name + club |
| full_name | best available display name |
| date_of_birth | from archive 5 bio, if matched |
| primary_position | GK/CB/FB/DM/CM/AM/WING/ST - from archive 5's fine position where matched, otherwise a coarse default from the stat file's D/M/F/G label |
| club | current (2026/27) club - this is the squad list's club, not necessarily the club their stats were recorded at, if they transferred |
| nationality | from archive 5, if matched |
| market_value | from archive 5, if matched |
| data_confidence | `full` (bio + stats both matched), `bio_only` (position/bio known, no performance stats found), `stats_only` (stats found, no bio match, position is a coarse default) |
| low_minutes_flag | true if their profile season has under 270 minutes (3 full games) - rates built on this few minutes are noisy |
| stat_season_used | `2025-26` or `2024-25`, whichever was used for their profile (2025-26 preferred when available) |
| home_grown | from the PDF's Home Grown Player flag |
| squad_tier | `first_team` (on the 25-man list) or `u21_breakout` (a U21-list player who already has real senior stats, pulled in separately - see README) |

## player_season_stats.csv

One row per player who has a matched performance-stats row (376 of the
470 players in players.csv - the rest are `bio_only`). `season_used`
says which of the two seasons this row is from.

Every other column is a season total in the same raw units either
source uses (counts, not rates) - the model computes per-90 rates and
percentages from these directly. Not every column is populated for
every player: which fields exist differs by which of the two seasons'
source was used (see README for exactly what each source does and
doesn't track) - a genuinely untracked field is blank, not zero.

Columns: goals, assists, xg, xa, shots, shots_on_target, key_passes,
passes_completed, passes_attempted, progressive_passes,
progressive_carries, dribbles_completed, dribbles_attempted,
times_dribbled_past, tackles, tackles_won, interceptions, blocks,
clearances, aerial_duels_won, aerial_duels_total, duels_won,
duels_total, recoveries, fouls_committed, crosses_completed,
crosses_attempted, through_balls, touches_in_box,
passes_long_completed, passes_long_attempted, saves, goals_against,
post_shot_xg, goals_prevented, clean_sheets, minutes_played,
matches_played.
