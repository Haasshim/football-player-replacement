# EPL Player Matcher

Finds how similar two football players are, so you can check whether one
player is a good replacement for another. Built for the English Premier
League, using real 2026/27 squad data and two real seasons of player
stats.

Pick a team, look at the current lineup on a pitch view, tap a starting
player, search for any other player in the database, and see a match
score between them based on stats that matter for that position -
weighted so that performing well against strong opponents counts for
more - plus an overlaid radar chart, a 0-10 rating, and a separate team
chemistry score.

## Try it

**Live:** https://haasshim.github.io/football-player-replacement/

Or open `frontend/index.html` directly in a browser - everything (data
included) is in that one file. `docs/index.html` is the same file, kept
there for GitHub Pages to serve; re-copy it after regenerating
`frontend/index.html` if you rebuild the data.

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
npm install && npm run test:frontend   # full flow, GK edge case, rating spread, React tiles, React-failure fallback
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

## Team fit ("chemistry")

Alongside the match score (candidate vs the specific player being
replaced), the comparison page shows a second score: how well the
candidate's playing style fits the team as a whole. This uses a small
set of broadly-applicable style stats - passing accuracy, carrying
threat, work rate (recoveries), physicality (duels won), width
reliance (crosses attempted), and creativity (key passes) - averaged
across the team's current outfield players (weighted by minutes
played), then compared against the candidate the same way the match
score compares two players: z-scored against the whole league, turned
into a 0-100% distance-based score. It answers "would this player's
style suit how this team already plays", separately from "is this
player statistically similar to who they're replacing".

## Radar chart and rating

The comparison page also overlays both players on a radar chart - the
standard visualization this category of tool uses (Opta's Player
Radars, StatsBomb's original player radars, and comparison tools like
RenderFoot all converge on the same idea). Each axis is one of the
position's most heavily-weighted stats, plotted as a real empirical
percentile rank against every other player at that position (not an
assumed normal distribution) - direction-corrected so "further out" always
means "better", even for stats where a lower raw number is the good
outcome (fewer fouls, fewer times dribbled past). Only the top 8 stats
by weight are plotted, both for readability and because that matches
how these tools present it in practice - the full stat list is still
below as bars.

Every player also gets a 0-10 rating: the average of their percentile
ranks across their position's stats, scaled down to 10. It's the same
"quick glance" idea as Sofascore's or FotMob's player ratings, built
from the same data already computed for the radar and match score
rather than a separate model.

Each player also shows a nationality flag, age (from date of birth),
market value where known, and a "best attribute" callout - their
single highest-percentile stat, only surfaced when it's genuinely a
strength (60th percentile or above), so it doesn't say something
generic for a player with no standout quality.

Stat rows where neither player has data are hidden entirely, rather
than showing a confusing "- vs -" - a count of how many were hidden is
still shown, so nothing disappears silently.

## Best matches

Picking a player to replace no longer means guessing candidates one at a
time in the search box. The squad page now auto-ranks the top 5 real
candidates from the entire database by match score the moment a current
player is selected - this is the tool's actual stated purpose (finding
good replacements), so making the user manually search for every
candidate one at a time was the biggest usability gap before this. Only
players with real matched stats are suggested (see the bug note in
"Model validation" below for why that matters); the manual search box
is still there for anyone who wants to consider a specific player by name.

## Sources and footer

A persistent footer links to the datasets this project is built on and
the source code. Two of the five source files were identified with real
confidence by matching their exact structure (archive 5's distinctive
`DATA_JSON/Season_YYYY/Club_ID_Year.json` layout, and the team-match-log
file's exact column set) against known Kaggle datasets - the indexing
site used to find them has since shut down, so those links are
constructed from the standard Kaggle URL pattern rather than confirmed
by directly loading the page. The other two source files were not
confidently identified and still need a confirmed link.

## Fonts, homepage, and stat tooltips

Headlines (the homepage title, team names, player names on the
comparison page) use Oswald - a bold, condensed sans-serif that's the
de facto standard for sports branding, paired with the existing IBM
Plex Sans for body text and IBM Plex Mono for stat numbers.

The homepage has a low-opacity (5%) diagonal stripe pattern in the
pitch-green color behind the hero, and all 20 clubs' jersey icons laid
out in a fixed 10-column grid (exactly 2 rows of 10, at any screen
size) with a hover tooltip showing the club name - real photos and the
real Premier League logo aren't things to reproduce without rights to
do so (same reasoning as the badges), so the visual identity stays
built from generated, data-driven graphics.
Two buttons were added beyond the original single CTA: "Try a random
comparison" (jumps straight into a live comparison between two real
players with full data, so the tool is visible immediately) and a
GitHub source link.

Every stat name on the comparison page is clickable - tapping it
reveals a plain-language definition beneath the row ("Expected assists:
the likelihood the passes a player made would end in a goal..."),
tapping again collapses it. This doubles as the app's only tooltip
mechanism, deliberately: a hover-only tooltip doesn't work on a touch
screen, so a click-to-reveal pattern was used everywhere instead of
building two separate interaction paths for desktop and mobile.

## Why React only for the team-select page

The team-select tiles are a real React component (React 18, loaded via
UMD script tags, no build step or JSX/Babel - that would add close to
1MB for no real benefit here). Hovering a tile transitions it to the
club's actual color with a computed complementary accent for the
border and strength bar; the rest of the app stays the plain JS/string-
templating it already used.

That split is deliberate, not partial effort: React's value is
managing complex, deeply nested state across many interdependent
components. This app's pages are simple, independent screens that each
rebuild their own DOM on navigation - introducing a framework for the
whole thing would add real weight (bundle size, mount/unmount
bookkeeping) without making anything look or work better. The one place
a framework genuinely earns its cost is the per-tile hover state here
(20 tiles, each tracking its own hover independently, each computing a
derived color) - that's exactly the kind of localized, repeated,
state-driven UI React is good at, so that's the one place it's used.

If the CDN script fails to load for any reason (blocked host, ad
blocker, network blip), the page falls back to a plain, non-interactive
version of the same tiles rather than rendering an empty grid -
covered by its own test (`tests/react_fallback_check.js`).

## Team badges

Real club crests are trademarked, so instead of reproducing actual
badge artwork, each club gets a generated shield in its real colors
with its short code (e.g. ARS, LIV), plus a simple generated jersey
icon in the same colors - gives every team a distinct, recognizable
visual identity without using logo or kit assets that aren't ours
to redistribute. Player photos are left out for the same reason - real
photos of real, named people aren't something to source and embed
without rights to do so, so the visual identity here is built from
data instead: badges, an overlaid radar chart, a rating, and color.
Badge text color, and the rating pill colors, are chosen by real WCAG
contrast calculation (not a rough luminance guess) so every one of the
20 clubs' colors and every rating tier stays readable - a first pass
using a simplified heuristic had misjudged a few saturated mid-tones
(Man City sky blue, Hull orange) as fine for white text when they only
hit ~2.5:1 contrast; both the badge and rating-pill colors were
corrected after checking every case against the real formula.

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

- **A real bug, found by sanity-checking the "best matches" feature**: when
  two players share zero comparable stats (most commonly, one of them has
  no real data at all), the weighted-distance formula divides by a zero
  weight-sum. The old code defaulted that to "distance 0", which silently
  meant "0% distance apart" - a perfect 100% match - for any pair of
  players neither of which has any data. This was invisible on the
  comparison page (nobody manually picks a zero-data player to compare
  against), but the moment "best matches" started scoring every player in
  the database against a real one, several zero-data players tied for
  first place at 98-100%, which is how it was caught. Fixed in both
  `src/similarity.py` and the frontend port: zero comparable stats now
  scores 0, not 100, and `computeTopMatches` additionally only suggests
  players with real data in the first place. Covered by a new regression
  test (`test_zero_comparable_stats_scores_zero_not_a_perfect_match`).

## Model validation

There's no labeled "this replacement worked out" data to compute real
accuracy against, so `src/metrics.py` checks things that stand in for
it, and the tunable parameters were picked by testing against these
checks, not guessed - including one negative result, kept here because
a documented dead end is still useful:

- **A real bug, found by this process**: `save_pct` was configured and
  weighted for goalkeepers but the real-data pipeline never actually
  computed it (a leftover gap from the placeholder-to-real-data
  migration) - every GK comparison was silently running on one fewer
  stat than intended. Fixed in `src/season_aggregation.py` and covered
  by two new tests.
- **The separation metric itself was noisy**: an early single-sample
  check (30 pairs, one seed) showed central midfielders separating
  worse than random (ratio 0.83). Re-running the same config with a
  stable, seed-averaged measurement (320 samples: 8 seeds x 40 pairs)
  showed CM actually separates fine (1.12) - the original number was
  mostly sampling noise on a modest-sized position, not a real model
  weakness. `position_separation()` now supports an `n_trials` argument
  for exactly this reason, and the pipeline uses it by default.
- **Position separation** (does a player's profile actually look more
  like same-position players than other positions), measured this
  stable way: **all 8 positions separate clearly** (ratio > 1.0) - CB
  1.28, GK 4.68, AM/DM/CM/WING 1.08-1.12, FB/ST ~1.1.
- **`DISTANCE_SCALE`** (in `src/similarity.py`) and each position's
  `big_game_delta_pct` weight were chosen by grid search over
  `DISTANCE_SCALE` (1.0-4.0) x weight (0.15-0.5): separation kept
  improving as `DISTANCE_SCALE` increased, but past about 2.5 the score
  distribution compressed so hard the tool almost never showed a
  genuinely poor match (0% of a 300-pair sample scored 20% or below) -
  less honest even though the one metric looked better. `2.0` / `0.4`
  was the best trade-off: strong separation without flattening the
  score range.
- **A data-informed reweight was tried and rejected**: stats where a
  position's hand-set weight looked high relative to how much that
  stat actually differs from other positions (e.g. full-backs' `xa_p90`
  was weighted 0.9 despite barely differing from the rest of the
  league) were identified and tested as a batch adjustment. Measured
  the same stable way, it made no real difference to 7 of 8 positions
  and slightly *worsened* goalkeepers - so it wasn't applied. Chasing a
  single correlation-style statistic without validating the actual
  effect would have been a regression dressed up as an improvement.
- **Score distribution**: match scores across a same-position sample
  spread from ~11 to ~95 with a mean around 55 and a real spread
  (std ~14) - informative in both directions, not bunched at one value.
- **An entirely different model was tried and rejected**: weighted
  cosine similarity, instead of weighted Euclidean distance, as the
  core comparison. Cosine similarity judges the *shape* of a player's
  stat profile (which things they're relatively strong or weak at)
  rather than the absolute size of the difference on each stat. Tested
  head to head with the same stable methodology: it separated *worse*
  on every single position, several dropping below the random baseline,
  and it nearly erased the goalkeeper/outfielder separation entirely
  (8.0 down to 1.0). That tracks - cosine similarity is magnitude-
  invariant, so a genuinely excellent player and a mediocre one with a
  similar *pattern* of strengths and weaknesses would score as highly
  similar, which is the wrong answer for a tool about judging whether
  someone is a good replacement in absolute terms, not just a
  similarly-shaped one. The current weighted-Euclidean approach stands
  as the better-tested choice, not just the original one.

What "model" means here, plainly: this is a weighted nearest-neighbor-
style distance function - position-specific weighted Euclidean
distance between two players' z-scored stat profiles, mapped to a 0-100
score by exponential decay - not a trained machine learning model.
There's no gradient descent and no neural net, because there's no
labeled "this was a good replacement" data to train one against. It's
closer to classical statistics / information retrieval than deep
learning, and the validation work above (grid search, the rejected
reweight, the rejected cosine-similarity alternative) is what "training"
looks like for a scoring function instead of a learned model: define a
metric that stands in for ground truth, test changes against it
honestly, and keep only what actually holds up.

Once real transfer/scouting outcomes exist, replace or add to this with
a proper accuracy metric (e.g. Spearman correlation between match_score
and human-judged similarity).

## Status

Real 2026/27 squads, real 2024-25 and 2025-26 stats, real match-result-derived
team strength and schedule-difficulty, a working similarity engine, and a
working web app, all tested end to end. Known gaps are flagged in the UI
and documented above rather than papered over.
