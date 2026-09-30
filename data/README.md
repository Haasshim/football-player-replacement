# EPL Data Requirements — v1 Schema

Scope: one season of EPL (whichever season is easiest to source — recommend the most recently completed full season, so nothing is mid-season/incomplete). Four tables needed. Match-level granularity is required for the big-game weighting to work — season totals alone won't let us tell which games were against strong opposition.

---

## Table 1: `teams.csv` (one row per EPL team, that season)

| Column | Type | Notes |
|---|---|---|
| team_id | text | short code, e.g. `ARS` |
| team_name | text | |
| league | text | `EPL` (kept for when we expand later) |
| final_league_position | int | 1–20 |
| points | int | season total |
| points_per_game_last10 | float | at end of season, or rolling if you want mid-season snapshots later |
| goal_difference | int | season total |
| uefa_coefficient | float | club coefficient for that season (available on UEFA's site) |

---

## Table 2: `players.csv` (one row per player who featured that season)

| Column | Type | Notes |
|---|---|---|
| player_id | text | unique id, e.g. `haaland_erling` |
| full_name | text | |
| date_of_birth | date | |
| primary_position | text | one of: GK, CB, FB, DM, CM, AM, WING, ST |
| club | text | matches `team_id` in teams.csv |
| nationality | text | |
| preferred_foot | text | optional |

---

## Table 3: `fixtures.csv` (one row per EPL match that season)

| Column | Type | Notes |
|---|---|---|
| fixture_id | text | e.g. `2024-08-16_ARS_WOL` |
| date | date | |
| home_team_id | text | |
| away_team_id | text | |
| home_score | int | |
| away_score | int | |

---

## Table 4: `player_match_stats.csv` (one row per player per match played)

This is the big one — it's what everything else is computed from. If your source (e.g. FBref) already splits these into separate tables (Standard/Passing/Defense/Possession/Shooting/Keepers), that's fine — send them as separate files, they don't need to be pre-merged. Just make sure `fixture_id` + `player_id` are on every row so they can be joined.

| Column | Type | Notes |
|---|---|---|
| fixture_id | text | joins to fixtures.csv |
| player_id | text | joins to players.csv |
| team_id | text | which team they played for |
| minutes_played | int | |
| position_played | text | can differ from primary_position for that match |
| goals | int | |
| assists | int | |
| xg | float | expected goals |
| xa | float | expected assists |
| shots | int | |
| shots_on_target | int | |
| key_passes | int | |
| passes_completed | int | |
| passes_attempted | int | |
| progressive_passes | int | |
| progressive_carries | int | |
| dribbles_completed | int | successful take-ons |
| dribbles_attempted | int | |
| times_dribbled_past | int | i.e. beaten by an opponent's dribble |
| tackles | int | |
| tackles_won | int | |
| interceptions | int | |
| blocks | int | |
| clearances | int | |
| aerial_duels_won | int | |
| aerial_duels_total | int | |
| duels_won | int | ground duels |
| duels_total | int | |
| recoveries | int | ball recoveries |
| fouls_committed | int | |
| crosses_completed | int | |
| crosses_attempted | int | |
| through_balls | int | |
| touches_in_box | int | attacking third/box touches |
| passes_long_completed | int | |
| passes_long_attempted | int | |
| **Goalkeeper-only columns (leave blank for outfield players):** | | |
| saves | int | |
| goals_against | int | |
| post_shot_xg | float | for computing PSxG-GA |
| clean_sheet | bool | |

---

## Notes on sourcing

- If a source only gives season *totals* per player, still useful, but tell us clearly it's season-level — we can approximate opponent difficulty using minutes-weighted averages against the team's fixture list instead of true per-match weighting, but match-level is strongly preferred for accuracy.
- Missing columns for some players (e.g. no xG for a CB) are fine — leave blank, we won't force stats onto positions that don't need them.
- You don't need to fill in every stat perfectly before sending — partial data is useful, we can start building and validating with whatever arrives first (e.g. just Standard + Passing tables) and layer in Defense/Possession/Keeper stats after.
