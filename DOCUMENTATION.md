
# Football AI — Technical Documentation

**Project:** Football AI — Premier League Predictor  
**Repository:** [Laca1234/Football-AI](https://github.com/Laca1234/Football-AI)  
**Language:** Python, JavaScript, HTML, CSS  
**Backend:** Flask  
**Machine Learning:** Scikit-learn  
**Data Provider:** TheSportsDB  

---

# Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Application Initialization](#3-application-initialization)
4. [Historical Data Collection](#4-historical-data-collection)
5. [Data Processing](#5-data-processing)
6. [Feature Engineering](#6-feature-engineering)
7. [Machine Learning Model](#7-machine-learning-model)
8. [Match Prediction](#8-match-prediction)
9. [Season Simulation](#9-season-simulation)
10. [Backend API](#10-backend-api)
11. [Frontend Architecture](#11-frontend-architecture)
12. [Logging](#12-logging)
13. [Configuration](#13-configuration)
14. [Installation and Execution](#14-installation-and-execution)
15. [Error Handling and Limitations](#15-error-handling-and-limitations)
16. [Future Development](#16-future-development)

---

# 1. Project Overview

Football AI is a machine-learning-based English Premier League prediction application.

The main objective is to analyze historical football match results and use the extracted statistical patterns to estimate the probability of future match outcomes.

The application provides two primary functionalities:

**Match Prediction**

Evaluates individual fixtures and calculates the probability of a home win, draw, or away win.

**Season Simulation**

Uses the trained model to simulate an entire Premier League season, generating projected standings and statistical insights.

The project is designed as a full-stack application, separating its machine learning logic, backend API, and frontend presentation into distinct components.

## 1.1 Main Objectives

- Analyze historical Premier League results.
- Identify short-term and long-term team performance patterns.
- Evaluate home and away performance separately.
- Generate probability-based match predictions.
- Simulate a complete 20-team league season.
- Present predictions and statistics through an interactive dashboard.
- Minimize repeated external API requests through local caching.

## 1.2 Supported Competition

The application is configured for the English Premier League.

| Parameter | Configuration |
|---|---|
| Competition | English Premier League |
| TheSportsDB League ID | 4328 |
| Historical starting season | 2012/13 |
| Configured final season | 2026/27 |
| Number of configured seasons | 15 |
| Standard league size | 20 teams |
| Standard season fixtures | 380 |

The configured seasons are defined in `model.py`.

---

# 2. System Architecture

The application follows a modular architecture consisting of three main layers.

## 2.1 Backend Layer

Implemented using Python and Flask.

Responsibilities:
- Initialize the application.
- Load historical match data.
- Train the machine learning model.
- Expose REST API endpoints.
- Validate incoming prediction requests.
- Coordinate prediction and simulation operations.
- Return JSON responses.

Main file: `controller.py`

## 2.2 Machine Learning Layer

Implemented using Pandas, NumPy, and Scikit-learn.

Responsibilities:
- Retrieve historical football results.
- Cache historical data.
- Normalize team names.
- Extract match statistics.
- Construct training features.
- Train the Random Forest classifier.
- Maintain team performance histories.

Main file: `model.py`

## 2.3 Business Logic Layer

Contains the actual prediction and simulation algorithms.

Responsibilities:
- Generate feature vectors for selected fixtures.
- Calculate match outcome probabilities.
- Apply probability smoothing.
- Introduce controlled randomness.
- Simulate league fixtures.
- Update team histories during simulations.
- Calculate final league standings.

Main file: `service.py`

## 2.4 Frontend Layer

Implemented using standard web technologies.

Responsibilities:
- Display available teams.
- Provide match selection controls.
- Send requests to the backend.
- Display prediction probabilities.
- Display upcoming fixtures.
- Render simulated league standings.
- Present additional statistical insights.
- Handle language and theme preferences.

Main files:
- `templates/index.html`
- `static/App.js`
- `static/styles.css`

## 2.5 Architecture Diagram

```text
                    USER
                     |
                     v
              WEB INTERFACE
             HTML / CSS / JS
                     |
                     v
               FLASK SERVER
                controller.py
                     |
          +----------+----------+
          |          |          |
          v          v          v
       /teams     /predict   /simulate
          |          |          |
          |          v          v
          |       service.py   service.py
          |          |          |
          +----------+----------+
                     |
                     v
                 model.py
                     |
          +----------+----------+
          |                     |
          v                     v
    HISTORICAL DATA        ML TRAINING
    TheSportsDB API        Random Forest
          |                     |
          v                     v
      JSON CACHE          TEAM HISTORY
          |                     |
          +----------+----------+
                     |
                     v
                JSON RESPONSE
                     |
                     v
                WEB INTERFACE
```

---

# 3. Application Initialization

Application initialization takes place in `controller.py`.

When the Python process starts, the following operations are performed:

1. Import Flask and required dependencies.
2. Import model training and data loading functions.
3. Import prediction and simulation functions.
4. Initialize the Flask application.
5. Enable Cross-Origin Resource Sharing.
6. Retrieve historical match data.
7. Train the machine learning classifier.
8. Initialize the current season configuration.
9. Initialize the team list and badge mappings.
10. Start the Flask development server.

The model is initialized globally:

```python
_data = load_all_data()

_rf, _target_enc, _label_enc, _team_hist, _feat_cols = train_model(_data)
```

The returned objects are reused by the API endpoints.

| Variable | Purpose |
|---|---|
| `_data` | Combined historical match dataset |
| `_rf` | Trained Random Forest classifier |
| `_target_enc` | Encodes match outcome classes |
| `_label_enc` | Stores team label encoders |
| `_team_hist` | Historical performance of each team |
| `_feat_cols` | Ordered machine learning feature columns |

This approach avoids retraining the model every time an individual prediction request is received.

---

# 4. Historical Data Collection

Historical match data is managed in `model.py`.

The application retrieves football results from TheSportsDB API.

## 4.1 API Configuration

The following constants define the data source:

```python
SPORTSDB_KEY = "123"
PL_LEAGUE_ID = "4328"
TOTAL_ROUNDS = 38

FIRST_YEAR = 2012
CURRENT_YEAR = 2027
```

The application constructs requests using the following API structure:

```text
https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsround.php?id={LEAGUE_ID}&r={ROUND}&s={SEASON}
```

Each season contains up to 38 gameweeks.

The application retrieves the rounds individually and combines the returned events.

## 4.2 Historical Season Collection

The configured season list is generated dynamically:

```python
ALL_SEASONS = [
    f"{y}-{y+1}"
    for y in range(FIRST_YEAR, CURRENT_YEAR)
]
```

This generates seasons from 2012/13 through 2026/27.

For each season:

1. Check whether cached data exists.
2. Retrieve all 38 rounds if necessary.
3. Combine the returned events.
4. Generate fallback data if the API returns no events.
5. Save the resulting events locally.
6. Convert the events into a Pandas DataFrame.

## 4.3 API Rate Limiting

The application includes basic protection against API rate limits.

The `_fetch_round()` function:
- Uses a maximum of three attempts.
- Implements a request timeout of 10 seconds.
- Detects HTTP 429 responses.
- Uses exponential retry delays.

The season retrieval process also introduces a 1.5-second delay between round requests.

These measures help reduce the frequency of requests to the external data provider.

## 4.4 Local Data Caching

Historical seasons are stored in the automatically generated `_cache/` directory.

Example:

```text
_cache/
├── season_2012_2013.json
├── season_2013_2014.json
├── season_2014_2015.json
├── season_2015_2016.json
└── ...
```

The cache provides several advantages:

- Reduces unnecessary API calls.
- Improves subsequent application startup times.
- Reduces dependency on external API availability.
- Preserves previously retrieved match events.

The cache is checked before attempting to retrieve a season again.

**Important:** Cached data is not automatically refreshed. Existing files must be removed manually if updated historical results are required.

## 4.5 Fallback Data Generation

If the API returns no events for a season, `_generate_fallback_events()` creates synthetic baseline match data.

The fallback implementation:
- Uses a predefined list of 20 teams.
- Generates ordered team pairings.
- Assigns randomized scores.
- Uses a fixed random seed.

This mechanism allows the application to continue operating when the API is unavailable.

However, synthetic results are not authentic football results. Any season containing fallback data should be excluded from real-world accuracy evaluations.

---

# 5. Data Processing

After retrieving historical events, the application processes them into a structured dataset.

The main functions are:

- `_normalise_team()`
- `_parse_events()`
- `load_all_data()`

## 5.1 Team Name Normalization

Different data providers may use different names for the same football club.

For example:

| API Name | Internal Name |
|---|---|
| Arsenal F.C. | Arsenal |
| Manchester United F.C. | Manchester United |
| Manchester City F.C. | Manchester City |
| Newcastle United F.C. | Newcastle |
| Tottenham Hotspur F.C. | Tottenham |
| Wolverhampton Wanderers | Wolves |
| Sunderland AFC | Sunderland |

The normalization process ensures consistent team identification across historical datasets and API responses.

## 5.2 Match Result Processing

The application extracts the following information:

| Field | Description |
|---|---|
| HomeTeam | Home team |
| AwayTeam | Away team |
| FTHG | Full-time home goals |
| FTAG | Full-time away goals |
| FTR | Full-time result |
| season | Season identifier |
| date | Match date |

Matches without valid final scores are excluded from the training dataset.

The final result is classified using three possible values:

```python
ftr = "H" if hg > ag else ("A" if ag > hg else "D")
```

Where:

- `H` represents a home victory.
- `D` represents a draw.
- `A` represents an away victory.

## 5.3 Historical Season Weights

Each season receives a progressively increasing weight.

```python
weight = 1.0 + 4.0 * (i / (total - 1))
```

The purpose is to increase the influence of more recent football performance.

The weight is subsequently converted into an integer repetition count during model training.

---

# 6. Feature Engineering

Feature engineering is one of the most important parts of the prediction system.

Instead of using only the final league standings, Football AI extracts individual team performance statistics.

The feature generation process is implemented in `_build_features()`.

## 6.1 Team History

The application maintains a historical record for each team.

Every match adds an entry containing:

```python
{
    "is_home": True,
    "gf": 2,
    "ga": 1,
    "win": True,
    "draw": False,
    "season": "2025-2026",
    "date": "2025-08-15"
}
```

The information is used to calculate future match features.

Features are extracted before the current match is added to the historical record. This prevents the current result from influencing its own training features.

## 6.2 Short-Term Form

The model evaluates the last five matches of each team.

Configuration:

```python
FORM_WINDOW = 5
```

The following statistics are calculated:

- Number of wins.
- Number of draws.
- Number of losses.
- Average goals scored.
- Average goals conceded.
- Win rate.

These features provide an overview of recent performance.

## 6.3 Venue-Specific Form

Home and away performance are evaluated separately.

For the home team, the model extracts its latest five home performances.

For the away team, the model extracts its latest five away performances.

This helps distinguish between teams that perform differently depending on their playing venue.

## 6.4 Long-Term Performance

The model also evaluates a longer historical window.

Configuration:

```python
LONG_WINDOW = 38
```

The main statistics are:

- Long-term win rate.
- Average goals scored.
- Average goals conceded.

The purpose is to provide a more stable representation of overall team quality.

## 6.5 Current Season Performance

The model calculates season-to-date statistics independently for each team.

The following values are extracted:

- Average goals scored.
- Average goals conceded.

If no current-season matches are available, baseline values are used.

## 6.6 Complete Feature List

The model uses 30 numerical features.

| Feature Group | Number of Features |
|---|---:|
| Overall recent form | 10 |
| Venue-specific recent form | 10 |
| Long-term performance | 6 |
| Current-season statistics | 4 |
| **Total** | **30** |

The feature columns are defined in `FEATURE_COLS`.

### Overall Recent Form

```text
h_w5
h_d5
h_l5
h_gf5
h_ga5

a_w5
a_d5
a_l5
a_gf5
a_ga5
```

### Venue-Specific Recent Form

```text
h_home_w5
h_home_d5
h_home_l5
h_home_gf5
h_home_ga5

a_away_w5
a_away_d5
a_away_l5
a_away_gf5
a_away_ga5
```

### Long-Term Performance

```text
h_wr38
h_gf38
h_ga38

a_wr38
a_gf38
a_ga38
```

### Current-Season Performance

```text
h_season_gf
h_season_ga

a_season_gf
a_season_ga
```

The `h_` prefix identifies home-team statistics, while `a_` identifies away-team statistics.

---

# 7. Machine Learning Model

The classifier is trained in `train_model()`.

## 7.1 Algorithm Selection

The project uses a Random Forest Classifier.

Random Forest is an ensemble learning algorithm that combines multiple decision trees to generate predictions.

It is suitable for this project because it can identify nonlinear relationships between different statistical features.

## 7.2 Model Configuration

```python
RandomForestClassifier(
    n_estimators=600,
    max_depth=6,
    min_samples_split=30,
    min_samples_leaf=15,
    max_features="sqrt",
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)
```

### Parameter Explanation

| Parameter | Explanation |
|---|---|
| n_estimators | Number of decision trees |
| max_depth | Maximum depth of individual trees |
| min_samples_split | Minimum samples required to split a node |
| min_samples_leaf | Minimum samples required in a leaf |
| max_features | Number of features considered at each split |
| random_state | Reproducibility of model initialization |
| class_weight | Balances the importance of outcome classes |
| n_jobs | Uses available CPU cores |

## 7.3 Target Encoding

The target variable contains three categorical outcomes:

```text
H
D
A
```

A Scikit-learn LabelEncoder converts these categories into numerical labels.

The encoder is retained so that the classifier's output can be mapped back to the original football outcomes.

## 7.4 Weighted Training

The historical season weights are converted into repeated samples:

```python
repeat_counts = feat_df["weight"].apply(
    lambda w: max(1, int(round(w)))
).values
```

The training dataset is then expanded using Pandas index repetition.

This gives newer seasons more influence during training.

## 7.5 Model Output

The classifier uses:

```python
rf.predict_proba(X)
```

This returns a probability distribution for the three outcome classes.

The resulting values are processed by the prediction service before being returned to the frontend.

---

# 8. Match Prediction

Individual match predictions are implemented in `service.py`.

The main function is:

```python
predict_match(
    home,
    away,
    rf,
    target_encoder,
    label_encoders,
    team_history,
    current_season,
    noise=True
)
```

## 8.1 Input Validation

Before generating a prediction, the function verifies that both teams exist in the trained dataset.

Unknown teams return `None`.

## 8.2 Feature Generation

The `_get_features()` function retrieves the historical statistics of both teams.

It calculates:

- Recent overall form.
- Recent home and away form.
- Long-term performance.
- Current-season scoring statistics.

These values are assembled into a single-row Pandas DataFrame.

The column order follows `FEATURE_COLS`.

## 8.3 Probability Generation

The Random Forest classifier produces the initial probabilities.

The model then applies probability smoothing.

The smoothing formula is:

```text
P_final = P_model × 0.88 + 0.12 / 3
```

This reduces excessively extreme predictions by shifting a small proportion of probability toward a uniform distribution.

## 8.4 Controlled Random Variation

The prediction function optionally introduces random variation.

Configuration:

```python
NOISE_STD = 0.035
```

Random values are sampled from a normal distribution and added to the predicted probabilities.

The values are subsequently clipped and normalized.

This creates small differences between repeated predictions.

## 8.5 Final Probability Normalization

The probabilities are normalized:

```python
proba /= proba.sum()
```

The final distribution always sums to 1.

Example:

```json
{
  "H": 0.45,
  "D": 0.27,
  "A": 0.28
}
```

The result represents:

- 45% home win probability.
- 27% draw probability.
- 28% away win probability.

These values are illustrative.

---

# 9. Season Simulation

The full-season simulation is implemented in `simulate_season()`.

It generates a randomized Premier League season using the trained model.

## 9.1 Fixture Generation

The application uses:

```python
fixtures = list(permutations(teams, 2))
```

For a league containing 20 teams, the number of generated fixtures is:

```text
20 × 19 = 380
```

Each team plays every other team once, with every ordered home/away pairing represented.

The fixtures are randomized before simulation.

## 9.2 Independent Simulation History

The simulation creates a copy of the historical team data:

```python
sim_history = copy.deepcopy(team_history)
```

This is important because simulated match results must not modify the original historical dataset.

The copied histories are updated after each simulated match.

## 9.3 Match Probability Processing

For each fixture:

1. Generate the match feature vector.
2. Retrieve Random Forest probabilities.
3. Apply probability transformation.
4. Introduce random variation.
5. Reduce the draw probability.
6. Redistribute the removed draw probability.
7. Normalize the resulting probabilities.
8. Randomly select a match outcome.

### Draw Probability Adjustment

The simulator applies:

```python
proba = np.power(proba, 2.3)
```

This transformation emphasizes higher probabilities.

The draw probability is then reduced by applying a squeeze factor:

```python
squeeze_factor = 0.50
```

The removed probability is redistributed between the home and away outcomes.

The favorite receives 80% of the redistributed probability, while the other team receives 20%.

The resulting distribution is normalized again.

## 9.4 Outcome Selection

The simulator selects one of the three possible outcomes using weighted random sampling.

```python
outcome = np.random.choice(
    ["H", "D", "A"],
    p=[probs["H"], probs["D"], probs["A"]]
)
```

This means that the most probable outcome is not guaranteed to occur.

A lower-probability outcome can still be selected.

## 9.5 Goal Generation

Goals are generated using NumPy's Poisson distribution.

The average scoring rates are derived from the teams' long-term historical statistics.

```python
hg = min(
    int(np.random.poisson(max(h38["avg_gf"], 1.0))),
    7
)

ag = min(
    int(np.random.poisson(max(a38["avg_gf"], 1.0))),
    7
)
```

The maximum generated score is initially capped at seven goals.

The score is then adjusted to match the selected match outcome.

For example:

- A home win must produce more home goals.
- An away win must produce more away goals.
- A draw must produce equal scores.

## 9.6 Dynamic Team History

After each fixture, the simulated result is added to both teams' histories.

The updated histories influence the features of subsequent simulated fixtures.

This allows team performance statistics to evolve throughout the simulated season.

## 9.7 League Table Calculation

The simulator maintains the following statistics:

```text
Points
Wins
Draws
Losses
Goals For
Goals Against
Goal Difference
```

Points are allocated using standard Premier League rules:

| Result | Points |
|---|---:|
| Win | 3 |
| Draw | 1 |
| Loss | 0 |

The final standings are sorted using:

1. Total points.
2. Goal difference.
3. Goals scored.

The final table contains all participating teams.

## 9.8 Season Insights

The simulator additionally calculates:

- Top four teams.
- Relegation positions.
- Promoted team performance.
- Top five teams by goals scored.
- Top five teams by goal difference.

These values are returned alongside the final standings.

## 9.9 Simulation Randomness

The simulation does not use a fixed random seed for each execution.

As a result:

- Different runs may produce different league tables.
- Match outcomes are probabilistic.
- Final standings are not deterministic.
- Repeated simulations can be used to explore different possible scenarios.

The current implementation performs one complete simulation per request, not a multi-run Monte Carlo analysis.

---

# 10. Backend API

The Flask application is responsible for connecting the frontend to the prediction engine.

All API responses use JSON.

## 10.1 GET /

Returns the main HTML application.

Implementation:

```python
@app.route("/")
def index():
    return render_template("index.html")
```

## 10.2 GET /api/teams

Returns the available teams, their badges, and the configured season.

Example response:

```json
{
  "teams": [
    {
      "name": "Arsenal",
      "badge": "https://example.com/badge.png"
    }
  ],
  "season": "2026-2027"
}
```

The example badge URL is illustrative.

## 10.3 POST /api/predict

Accepts one or more fixtures.

Expected request structure:

```json
{
  "matches": [
    {
      "home": "Arsenal",
      "away": "Liverpool"
    }
  ]
}
```

Processing:

1. Read the JSON request.
2. Extract the match list.
3. Validate team selections.
4. Generate predictions.
5. Attach team badge information.
6. Return the results.

Possible validation errors include:

- No matches provided.
- Missing team.
- Both teams are identical.
- Unknown team names.

## 10.4 POST /api/simulate

Starts a complete season simulation.

The endpoint does not require a request body.

Example request:

```http
POST /api/simulate
```

Example response structure:

```json
{
  "season": "2026-2027",
  "standings": [],
  "insights": {
    "top4": [],
    "relegated": [],
    "promoted": [],
    "top_scorers": [],
    "best_gd": []
  }
}
```

The arrays contain the actual simulated team statistics.

## 10.5 GET /api/fixtures

Retrieves upcoming Premier League fixtures.

The endpoint:

1. Retrieves the current season's events.
2. Filters out completed matches.
3. Extracts team names and badges.
4. Groups fixtures by gameweek.
5. Sorts the rounds numerically.
6. Returns the next two gameweeks containing unplayed matches.

The endpoint uses the same season caching mechanism as the historical data loader.

---

# 11. Frontend Architecture

The frontend is built with HTML, CSS, and vanilla JavaScript.

It communicates with the Flask backend through the browser Fetch API.

## 11.1 HTML Structure

`templates/index.html` defines the main application interface.

The interface contains:

- Navigation bar.
- Season indicator.
- Language switch.
- Theme switch.
- Match prediction panel.
- Season simulation panel.
- Upcoming fixtures sidebar.
- Results containers.

## 11.2 JavaScript Functionality

The frontend logic is implemented in `static/App.js`.

Main functions:

| Function | Responsibility |
|---|---|
| `boot()` | Initializes the frontend |
| `initLang()` | Initializes language preferences |
| `initTheme()` | Initializes theme preferences |
| `setMode()` | Switches application panels |
| `createSelect()` | Creates team selection controls |
| `renderOptions()` | Renders available teams |
| `filterOptions()` | Filters team search results |
| `addMatchRow()` | Adds another prediction row |
| `removeRow()` | Removes a match row |
| `loadFixtures()` | Retrieves upcoming fixtures |
| `renderFixtures()` | Displays upcoming fixtures |
| `runPrediction()` | Sends match prediction requests |
| `renderMatchResults()` | Displays probability results |
| `runSimulation()` | Starts a season simulation |
| `renderStandings()` | Displays the league table |
| `renderInsights()` | Displays additional statistics |

## 11.3 API Communication

The frontend uses asynchronous Fetch API requests.

Example:

```javascript
const response = await fetch("/api/predict", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        matches: matches
    })
});
```

The returned JSON is processed and rendered dynamically.

## 11.4 Language Support

The application supports:

- English.
- Hungarian.

Translations are maintained in a JavaScript dictionary.

The selected language is saved using:

```javascript
localStorage.setItem("lang", lang);
```

## 11.5 Theme Support

The application supports dark and light themes.

Theme selection is managed using CSS custom properties and a root HTML attribute.

```javascript
document.documentElement.setAttribute(
    "data-theme",
    theme
);
```

The selected theme is also saved in browser local storage.

---

# 12. Logging

Application activity is recorded through `logger.py`.

The logging system uses Python's built-in logging module.

Configuration:

```python
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
```

The default log filename is:

```text
app_activity.log
```

The `log_event()` function records application events and prints them to the terminal.

Logging is used by the API endpoints and season simulation process.

---

# 13. Configuration

The main configuration values are distributed across the project's modules.

## 13.1 model.py

| Constant | Purpose |
|---|---|
| `SPORTSDB_KEY` | TheSportsDB API key |
| `PL_LEAGUE_ID` | Premier League identifier |
| `TOTAL_ROUNDS` | Number of league rounds |
| `FIRST_YEAR` | First historical season |
| `CURRENT_YEAR` | Final configured season boundary |
| `FORM_WINDOW` | Short-term form window |
| `LONG_WINDOW` | Long-term form window |
| `FEATURE_COLS` | Machine learning feature definitions |

## 13.2 controller.py

| Variable | Purpose |
|---|---|
| `CURRENT_SEASON` | Current application season |
| `ALL_TEAMS` | Available team names |
| `PROMOTED_TEAMS` | Teams highlighted in simulation insights |
| `TEAM_BADGES` | Team badge URLs |

## 13.3 service.py

| Variable | Purpose |
|---|---|
| `NOISE_STD` | Random variation applied to predictions |
| `FORM_WINDOW` | Recent performance window |
| `LONG_WINDOW` | Long-term performance window |

---

# 14. Installation and Execution

## 14.1 Requirements

The application requires:

- Python 3.10 or newer.
- pip.
- An internet connection for initial data collection.
- A compatible web browser.

## 14.2 Installation

Clone the repository:

```bash
git clone https://github.com/Laca1234/Football-AI.git
cd Football-AI
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Activate it on Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r .notes/requirements.txt
```

## 14.3 Start the Backend

```bash
python controller.py
```

The application will initialize the historical dataset and train the classifier before starting the Flask server.

## 14.4 Access the Interface

Open:

```text
http://127.0.0.1:5000
```

The application is now accessible through the browser.

---

# 15. Error Handling and Limitations

## 15.1 External API Availability

The application depends on TheSportsDB for historical and upcoming match information.

If the API is unavailable:
- Requests may fail.
- Historical seasons may use synthetic fallback data.
- Upcoming fixtures may be unavailable.

## 15.2 Historical Data Quality

Prediction quality depends heavily on the accuracy and completeness of historical data.

Synthetic fallback results must not be confused with authentic football statistics.

## 15.3 Model Accuracy

The current project does not implement a complete model evaluation pipeline.

There is no integrated chronological train/test evaluation, probability calibration report, or historical prediction accuracy dashboard.

Consequently, the generated probabilities should be interpreted as model estimates rather than independently validated real-world probabilities.

## 15.4 Season Configuration

The team list, promoted teams, season identifier, and team badges are maintained manually.

These values should be reviewed whenever the Premier League season changes.

## 15.5 Randomness

Randomness is used in both match prediction and season simulation.

The same fixture can produce slightly different probabilities across prediction requests.

Season simulation results can vary substantially between runs.

## 15.6 Frontend Filename Case Sensitivity

The current HTML template references:

```html
<script src="{{ url_for('static', filename='app.js') }}"></script>
```

However, the repository contains:

```text
static/App.js
```

These filenames differ in capitalization. This can cause a missing JavaScript file on case-sensitive operating systems.

The recommended fix is to rename the file to `static/app.js` or update the HTML reference.

## 15.7 Dependency File Location

The dependency file currently resides in:

```text
.notes/requirements.txt
```

The installation instructions therefore use that path.

Moving it to the repository root would make standard Python project setup more straightforward.

---

# 16. Future Development

The existing architecture provides a foundation for several potential improvements.

## 16.1 Advanced Prediction Models

- XGBoost and other gradient boosting algorithms.
- Model comparison and hyperparameter optimization.
- Probability calibration.
- Chronological cross-validation.
- Historical prediction accuracy tracking.

## 16.2 Monte Carlo Season Simulation

Run thousands of independent season simulations to calculate:

- Average final league positions.
- Championship probabilities.
- Top-four qualification probabilities.
- European qualification probabilities.
- Relegation probabilities.
- Expected final points.

This would provide more meaningful season forecasts than a single randomized simulation.

## 16.3 Additional Football Data

Potential data integrations:

- Player statistics.
- Injuries and suspensions.
- Expected goals.
- Squad availability.
- Transfer activity.
- Team formations.
- Historical head-to-head statistics.

## 16.4 Model Persistence

Currently, the application trains the model during startup.

A future implementation could serialize trained models using Joblib and load them directly.

This would significantly reduce startup time when the historical dataset has not changed.

## 16.5 Multiple Competitions

The architecture could be extended to support:

- Championship.
- La Liga.
- Bundesliga.
- Serie A.
- Ligue 1.
- UEFA competitions.

This would require competition-specific datasets, team configurations, and model training.

---

# Conclusion

Football AI combines historical sports data processing, statistical feature engineering, machine learning, probabilistic predictions, and season simulation into a full-stack football analytics application.

Its modular architecture separates data collection, model training, prediction logic, API communication, and frontend presentation.

The project provides a foundation for further experimentation with machine learning techniques and more advanced football forecasting systems.

---

**Author:** Laca1234  
**Repository:** https://github.com/Laca1234/Football-AI
