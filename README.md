
# ⚽ Football AI — Premier League Predictor

An AI-powered English Premier League prediction and season simulation platform built with Python, Flask, Scikit-learn, and JavaScript.

Football AI analyzes historical Premier League match data, evaluates team performance, and generates probabilistic predictions for upcoming fixtures. It also features a full-season simulation that produces projected league standings, team statistics, and performance insights.

The project combines machine learning, historical football statistics, a dynamic backend, and an interactive web interface into one application.

---

## ✨ Features

### 1. Match Prediction

Predict the outcome probabilities of individual Premier League fixtures.

- Select home and away teams from searchable team selectors.
- Add multiple matches and analyze them in one request.
- Generate probabilities for all three possible outcomes:
  - **H — Home Win**
  - **D — Draw**
  - **A — Away Win**
- View percentage-based probability bars.
- Account for historical performance, recent form, and venue-specific statistics.
- Apply probability smoothing to reduce excessively confident predictions.

The prediction engine uses a trained Random Forest classifier to estimate the likelihood of each match outcome.

### 2. Full Season Simulation

Simulate an entire Premier League season using the trained machine learning model.

- Simulates all 380 fixtures across 20 teams.
- Generates match outcomes probabilistically.
- Updates team performance histories throughout the simulation.
- Calculates league points, wins, draws, losses, goals scored, goals conceded, and goal difference.
- Produces a complete league table.
- Generates additional statistical insights.

The season simulation includes:

| Statistic | Description |
|---|---|
| PTS | Total league points |
| W | Wins |
| D | Draws |
| L | Losses |
| GF | Goals scored |
| GA | Goals conceded |
| GD | Goal difference |

Additional insights include:
- Top four teams.
- Projected relegation positions.
- Promoted teams' performance.
- Top-scoring teams.
- Best goal differences.

Each simulation is randomized, meaning subsequent runs can produce different league tables.

### 3. Historical Data Analysis

The machine learning model uses historical English Premier League results.

- Historical seasons from 2012/13 through 2026/27.
- Match results retrieved through TheSportsDB API.
- Automatic local JSON caching.
- Historical performance weighting.
- Team-specific statistical histories.
- Automatic team name normalization.

Older and newer seasons receive different training weights, allowing more recent results to have greater influence on the model.

### 4. Interactive Web Interface

The frontend provides a responsive dashboard with two main operating modes.

**Match Prediction**
- Dynamic match selection.
- Searchable team dropdowns.
- Multiple simultaneous predictions.
- Visual probability indicators.
- Upcoming fixture sidebar.

**Season Simulation**
- Interactive league standings.
- Team performance statistics.
- Qualification and relegation indicators.
- Additional season insights.

### 5. User Interface Customization

- English and Hungarian language support.
- Dark and light themes.
- Responsive layouts.
- Team badges and visual identifiers.
- Animated transitions and loading indicators.
- Persistent language and theme preferences using browser local storage.

---

## 🧠 Machine Learning

The prediction system uses a Scikit-learn Random Forest classifier.

### Model Configuration

| Parameter | Value |
|---|---|
| Algorithm | Random Forest Classifier |
| Estimators | 600 |
| Maximum depth | 6 |
| Minimum samples split | 30 |
| Minimum samples leaf | 15 |
| Maximum features | sqrt |
| Class weighting | Balanced |
| Random state | 42 |

### Feature Engineering

Instead of relying exclusively on overall league standings, the model evaluates multiple dimensions of team performance.

**Short-term form**
- Wins in the last 5 matches.
- Draws in the last 5 matches.
- Losses in the last 5 matches.
- Average goals scored.
- Average goals conceded.

**Venue-specific performance**
- Home team's recent home record.
- Away team's recent away record.
- Venue-specific goals scored and conceded.

**Long-term performance**
- Win rate over the last 38 matches.
- Average goals scored over the last 38 matches.
- Average goals conceded over the last 38 matches.

**Current season performance**
- Average goals scored during the current season.
- Average goals conceded during the current season.

All match features are constructed using the team's available history before that particular match, helping prevent future match results from leaking into historical training features.

### Historical Weighting

Historical seasons receive progressively increasing weights.

The weighting formula is:

`weight = 1.0 + 4.0 × (season_index / (total_seasons - 1))`

This produces a weighting range from 1 to 5.

The resulting weights are converted into repeated training samples, giving newer seasons greater representation during model training.

### Probability Processing

Match predictions receive additional probability processing:

1. Generate class probabilities using the trained classifier.
2. Smooth the probabilities toward a uniform distribution.
3. Optionally introduce small random variation.
4. Clip invalid or excessively small values.
5. Normalize the probabilities to sum to 100%.

The final prediction represents the estimated probability distribution across home wins, draws, and away wins.

---

## 🛠️ Technology Stack

### Backend
- Python
- Flask
- Flask-CORS
- NumPy
- Pandas
- Scikit-learn

### Machine Learning
- Random Forest Classifier
- Label Encoding
- Historical feature engineering
- Weighted training samples
- Probabilistic outcome generation

### Frontend
- HTML5
- CSS3
- JavaScript
- Fetch API
- Browser Local Storage

### Data Source
- [TheSportsDB API](https://www.thesportsdb.com/)

### Development Tools
- Git
- GitHub
- Python virtual environments

---

## 📁 Project Structure

```text
Football-AI/
│
├── controller.py
│   └── Flask application, API routes and backend initialization
│
├── model.py
│   └── Historical data loading, feature engineering and model training
│
├── service.py
│   └── Match prediction and full-season simulation logic
│
├── logger.py
│   └── Application activity logging
│
├── import sys.py
│   └── Python interpreter diagnostic script
│
├── templates/
│   └── index.html
│       └── Main web application interface
│
├── static/
│   ├── App.js
│   │   └── Frontend functionality and API communication
│   │
│   └── styles.css
│       └── Application styling and themes
│
├── .notes/
│   └── requirements.txt
│       └── Python dependencies
│
├── _cache/
│   └── Cached historical season data (generated automatically)
│
├── .alpha/
├── .beta/
├── .backups/
│   └── Development and backup directories
│
├── .gitignore
├── README.md
└── DOCUMENTATION.md
```

---

## 🚀 Installation

### Requirements

- Python 3.10 or newer.
- pip.
- Internet connection for initial historical data retrieval.
- Modern web browser.

### 1. Clone the Repository

```bash
git clone https://github.com/Laca1234/Football-AI.git
cd Football-AI
```

### 2. Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

The dependency file is currently located inside `.notes/`.

```bash
pip install -r .notes/requirements.txt
```

Alternatively, install the dependencies manually:

```bash
pip install flask flask-cors scikit-learn pandas numpy joblib
```

### 4. Start the Application

```bash
python controller.py
```

The Flask development server starts on:

```text
http://127.0.0.1:5000
```

Open this address in your browser to access Football AI.

### 5. Initial Data Loading

During the first startup, the application retrieves historical Premier League match data through TheSportsDB.

This process can take several minutes because the application retrieves individual gameweeks and implements request delays to reduce API rate limiting.

Subsequent startups use locally cached season data whenever available.

---

## 🔌 API Endpoints

The Flask backend exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the main application |
| GET | `/api/teams` | Returns available teams and current season |
| POST | `/api/predict` | Generates match predictions |
| POST | `/api/simulate` | Simulates a complete Premier League season |
| GET | `/api/fixtures` | Retrieves upcoming fixtures |

### Match Prediction Example

**Request:**

```json
{
  "matches": [
    {
      "home": "Arsenal",
      "away": "Liverpool"
    },
    {
      "home": "Chelsea",
      "away": "Manchester City"
    }
  ]
}
```

**Response:**

```json
{
  "results": [
    {
      "home": "Arsenal",
      "away": "Liverpool",
      "probs": {
        "H": 0.45,
        "D": 0.27,
        "A": 0.28
      }
    }
  ]
}
```

The values above are illustrative response data, not actual predictions.

---

## ⚙️ Configuration

Several model and application settings can be modified directly in the source code.

| File | Configuration |
|---|---|
| `model.py` | Historical seasons, league ID, API key, feature windows and data caching |
| `model.py` | Random Forest training configuration |
| `service.py` | Probability smoothing and simulation behavior |
| `controller.py` | Current season, team list and team badges |
| `static/App.js` | Frontend translations and interface behavior |
| `static/styles.css` | Visual styling and themes |

---

## ⚠️ Limitations

- Predictions are statistical estimates, not guaranteed outcomes.
- The model does not currently incorporate live injuries, player availability, transfers, tactical formations, or bookmaker odds.
- Historical data availability depends on TheSportsDB.
- Team lists and season configuration require manual maintenance.
- The season simulator generates one randomized season per execution rather than calculating an average across thousands of simulations.
- When historical API retrieval fails completely, the current implementation can generate synthetic fallback match data. Such data must not be treated as authentic football results.
- The current simulation is a probabilistic approximation and does not reproduce every aspect of real football.

---

## 🔮 Potential Future Improvements

- Monte Carlo simulations across thousands of seasons.
- Model evaluation using chronological train/test splits.
- Probability calibration and prediction accuracy reports.
- Expected goals (xG) modeling.
- Player-level statistics and injury information.
- Automated season and team updates.
- Additional football leagues.
- Historical prediction tracking.
- Model persistence to avoid retraining on every startup.
- More detailed team comparison dashboards.

---

## 👨‍💻 Author

**Laca1234**

GitHub: [github.com/Laca1234](https://github.com/Laca1234)

Project: [Football-AI](https://github.com/Laca1234/Football-AI)

---

## License

This project is licensed under the MIT License.

You are free to use, modify, and distribute this software under the terms of the license.

See the [LICENSE](LICENSE) file for details.
