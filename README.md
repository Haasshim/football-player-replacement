# EPL Player Replacement Finder

This project finds how similar two football players are, so you can check if one player is a good replacement for another. It focuses on the English Premier League for now.

The idea: pick a team, look at the current lineup, pick a player to replace, then search for any other player in the database and see a match score between them. The score is based on stats that matter for that position, and it gives extra weight to how a player performs in tough matches against strong opponents.

## What is in this repo

- `src/` the Python code for the models
  - `team_strength.py` works out how strong a team is, based on league position, recent form, goal difference, and UEFA coefficient
  - `opponent_weighting.py` works out how much each match should count, based on how strong the opponent was and how many minutes the player played
  - `player_aggregation.py` turns raw match stats into one weighted stat profile per player
  - `similarity.py` compares two players and turns the difference into a match score from 0 to 100
  - `metrics.py` sanity checks for the model, since there is no labeled data yet to test accuracy against
  - `config/position_weights.json` which stats matter for each position, and how much each one counts
- `data/` the CSV files the pipeline reads. Right now these are filled with generated placeholder data, not real match stats
- `scripts/generate_sample_data.py` makes the placeholder data
- `scripts/run_pipeline.py` runs the whole pipeline and writes `frontend/data.json`
- `frontend/index.html` the web app: team select, squad view, and player comparison, in one self contained file
- `tests/` unit tests for the Python code, and a small script that clicks through the whole web app to check it works

## Data

The data is currently placeholder, not real. See `data/README.md` for the exact columns needed for each file, so real EPL data can be swapped in later.

## Running it

Install dependencies:
```
pip install -r requirements.txt
```

Generate placeholder data and run the pipeline:
```
python scripts/generate_sample_data.py data
python scripts/run_pipeline.py
```

This prints some sanity checks and writes `frontend/data.json`, which the web app reads from.

Run the tests:
```
python -m pytest tests/
```

Open `frontend/index.html` in a browser to use the app.

## How the match score works

Each position has its own list of stats that matter for it (for example a full back is judged on crossing and tackling, a striker on goals and shot quality). Every stat is compared against the average and spread for that position, so a player is judged against others who play the same role. A weighted distance between the two players is then turned into a percentage match score.

Stats are also adjusted so that performances against strong opponents count more than performances against weak ones. This is based on a team strength index built from league position, recent form, goal difference, and UEFA coefficient.

## Status

This is an early version. The model logic and the web app both work end to end on placeholder data. Real data still needs to be sourced and loaded in before the match scores mean anything. See `data/README.md` for what is needed.
