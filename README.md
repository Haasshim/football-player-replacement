# EPL Player Replacement Finder

Finds how similar two football players are, so you can check whether one
player is a good replacement for another. Built for the English Premier
League, using real 2026/27 squad data and two real seasons of player
stats.

Pick a team, look at the current lineup on a pitch view, tap a starting
player, search for any other player in the database, and see a match
score between them based on stats that matter for that position -
weighted so that performing well against strong opponents counts for
more.

## Try it

Open `frontend/index.html` in a browser. Everything (data included) is
in that one file.

## What is in this repo

- `src/` the model code
  - `team_strength.py` a computed index from league position, form, goal
    difference, and UEFA coefficient
  - `season_aggregation.py` turns a player's season totals into per-90
    rates and percentages (the real-data path - see below)
  - `similarity.py` compares two players and turns the difference into a
    match score from 0 to 100, skipping any stat that is missing for
    either player rather than guessing
  - `metrics.py` sanity checks for the model, since there is no labeled
    data yet to test accuracy against
  - `config/position_weights.json` which stats matter for each position,
    and how much each one counts
  - `player_aggregation.py`, `opponent_weighting.py` an older, per-match
    version of the weighting logic, kept for synthetic-data testing (see
    "Two pipelines" below)
- `data/` the real teams, players, and season-stat tables the app
  currently runs on (see `data/README.md` for columns)
- `scripts/real_data/` the scripts that built `data/` from the source
  files (PDF squad list, bio archive, stat files, match-result archives)
- `scripts/run_real_pipeline.py` runs the model against `data/` and
  writes `frontend/data.json`
- `frontend/index.html` the web app: team select, a tap-to-pick pitch
  view for the squad, and the comparison page
- `tests/` unit tests, plus a script that clicks through the whole web
  app to check it actually works

## Two pipelines

There are two ways to feed the model, because the real data available
turned out to be season totals, not match-by-match:

- **Real pipeline** (`scripts/run_real_pipeline.py` + `src/season_aggregation.py`):
  what the app actually runs on. Takes season-total stats directly.
- **Match-level demo pipeline** (`scripts/run_pipeline.py` + `src/player_aggregation.py`
  + `src/opponent_weighting.py` + `scripts/generate_sample_data.py`):
  the original design, built and tested against synthetic match-by-match
  data. Kept as a working sandbox in case genuine match-level data (per
  player, per fixture) turns up later - the two are meaningfully
  different (see "Big game weighting" below) and the match-level version
  is the more precise one if the data ever supports it.

Running the demo pipeline overwrites `data/teams.csv` and
`data/players.csv` with synthetic placeholders - regenerate into a
separate folder if you want to try it without touching the real data:
```
python scripts/generate_sample_data.py /tmp/demo_data
```

## Running it

```
pip install -r requirements.txt
python scripts/run_real_pipeline.py   # rebuilds frontend/data.json from data/
python -m pytest tests/               # 22 tests
npm install && node tests/frontend_smoke_test.js   # clicks through the whole app
```

To rebuild `data/` itself from the original source files, run the
scripts in `scripts/real_data/` in order: `parse_squad_pdf.py`,
`parse_archive5_bios.py`, `parse_player_stats.py`,
`parse_team_results.py`, then `build_final_dataset.py`. These reference
absolute paths to the original uploaded source files from the session
that built this, which aren't bundled here (the raw bio archive alone
is tens of thousands of files across 1992-2026) - point the path
constants near the top of each script at wherever you have fresh copies
of that kind of data if you want to rerun ingestion later.

## How the match score works

Each position has its own list of stats that matter for it (a full back
is judged on crossing and tackling, a striker on goals and shot
quality). Every stat is compared against the average and spread for
players at that position, so a player is judged against others who play
the same role. A weighted distance between the two players is turned
into a percentage match score. Any stat missing for either player (see
"Data gaps" below) is left out of that comparison rather than treated as
zero.

## Big game weighting

The original plan was to weight each player's stats by the strength of
the specific opponent in each match they played. The stat sources
actually available are season totals, not match logs, so that is not
possible per-player. Instead, `scripts/real_data/parse_team_results.py`
computes a real, match-result-derived **team-level** factor:

For each team each season, points-per-game against top-half opponents
is compared to what that team's *overall* season form would predict,
given how much harder top-half opponents are for the league as a whole.
A team that is just generally good (and so beats everyone, strong
opponents included) nets out near zero here; a positive number means
they specifically raise their level against strong opposition beyond
what their general level predicts. This is blended across each team's
last 3-4 seasons, recency-weighted.

Every player on the same team in the same season gets the same value
for this stat (`big_game_delta_pct`) - it is a team property, not a
per-player one, because the data cannot support more than that. This is
weighted lower (0.3, versus 0.5-1.0 for genuinely player-specific stats)
in the position configs for exactly this reason: an earlier version
weighted it at 1.0, and because it is present for essentially every
player while position-specific stats have real 15-20% missingness, it
was diluting positional signal more than it was adding useful
information (see "Model validation" below).

## UEFA coefficients

Not present in any of the source files, so these were researched
separately (football-coefficient.eu, five-year club totals as of
roughly April 2026). Clubs with real recent European football have
their actual total; every other current club defaults to the
UEFA-defined floor (20% of England's five-season association
coefficient, ~19.7) since that is UEFA's own rule for clubs without
enough recent European points to exceed it. Newcastle's figure is a
rough estimate (two recent Champions League campaigns, an exact
up-to-date total was not found) and is flagged as such in the code.

## Data gaps, honestly

The two stat seasons come from different sources with different
schemas, so they don't track the same things:

- **2024-25** (standalone CSV): no xG/xA at all, no separate
  dribble-attempt counts, no split tackles-won-vs-attempted, no
  touches-in-box.
- **2025-26** (archive 4): has xG/xA, split dribbles, split tackles -
  but also no touches-in-box, and no progressive-passes/progressive-carries
  in the main file used.

When a player's profile season doesn't track a stat, it is left blank,
not zero - the similarity engine skips that stat for that comparison
rather than penalizing the player for a zero they never had.

94 of 470 players have a resolved bio/position but no matched
performance stats at all (`data_confidence: bio_only` - mostly brand
new signings to the league). 10 have stats but no bio match
(`stats_only` - their position is a coarse default). Both are flagged
in the UI wherever a player's name appears in search or the comparison
page.

Five clubs (Chelsea, Crystal Palace, Hull, Manchester City, and
Newcastle) are short a player or two in at least one formation slot
given the real data matched for their squad - the squad view just shows
however many are available for that slot rather than breaking.

Coventry, Hull, and Sunderland have zero match data in the archives used
(newly promoted for 2026/27) - they get an explicit, clearly-flagged
default team strength rather than a guessed number.

## Model validation

There's no labeled "this replacement worked out" data to compute real
accuracy against, so `src/metrics.py` checks things that stand in for
it:

- **Position separation**: does a player's profile actually look more
  like same-position players than other positions? Run against the real
  data, 7 of 8 positions separate clearly (ratio > 1.0, e.g. GK at 1.6,
  CB at 1.4, ST at 1.3). **Central midfielders are the exception**
  (ratio 0.83, meaning a CM's profile currently looks slightly *more*
  like a random non-CM than another CM) - this held regardless of the
  big-game-weight fix above, so it looks like a genuine finding: CM stat
  profiles are less statistically distinctive than specialist roles in
  this data, not a bug to chase further right now.
- **Score distribution**: match scores across a same-position sample
  spread from ~5 to ~100 with a mean around 45-50 - not degenerately
  bunched at one value.

Once real transfer/scouting outcomes exist, replace or add to this with
a proper accuracy metric (e.g. Spearman correlation between match_score
and human-judged similarity).

## Status

Real 2026/27 squads, real 2024-25 and 2025-26 stats, real match-result-derived
team strength and schedule-difficulty, a working similarity engine, and a
working web app, all tested end to end. Known gaps are flagged in the UI
and documented above rather than papered over.
