# Football AI — Technical Documentation

**Project:** Football AI — Premier League Predictor  
**Repository:** [Laca1234/Football-AI](https://github.com/Laca1234/Football-AI)  
**Language:** Python, JavaScript, HTML, CSS  
**Backend:** Flask  
**Machine Learning:** Scikit-learn, Pytest  
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
8. [Model Evaluation & Metrics](#8-model-evaluation--metrics)
9. [Match Prediction](#9-match-prediction)
10. [Season Simulation](#10-season-simulation)
11. [Backend API](#11-backend-api)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Logging](#13-logging)
14. [Configuration](#14-configuration)
15. [Installation and Execution](#15-installation-and-execution)
16. [Testing Suite](#16-testing-suite)
17. [Error Handling and Limitations](#17-error-handling-and-limitations)
18. [Future Development](#18-future-development)

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
- Generate probability-based match predictions using calibrated multiclass evaluation.
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
- Evaluate probabilistic calibration via Multiclass Log Loss and Brier Score.

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

---

# 8. Model Evaluation & Metrics

The application incorporates a rigorous chronological train/test evaluation framework (`evaluate_chronological_model` in `model.py`) to validate model performance without data leakage.

## 8.1 Multiclass Log Loss
To measure the quality of probability estimates, the application utilizes **Multiclass Log Loss** (cross-entropy loss):

$$\text{LogLoss} = -\frac{1}{N} \sum_{i=1}^{N} \sum_{c=1}^{C} y_{i,c} \log(p_{i,c})$$

- **Lower is Better**: A log loss of `0.0` represents a perfectly calibrated model. Random uniform guessing across 3 classes yields a baseline log loss of $\approx 1.0986$.
- **Confidence Penalty**: Confident incorrect predictions (e.g., assigning 95% probability to a home win when an away win occurs) are heavily penalized.
- **Epsilon Clipping**: Probabilities are clipped using `eps=1e-15` to prevent numerical instability and `KeyError`/`ValueError` issues caused by unseen labels or `log(0)`.

## 8.2 Evaluation Metrics Suite
The evaluation report outputs:
1. **Test Accuracy**: Fraction of correctly predicted match outcomes.
2. **Test Log Loss**: Cross-entropy loss evaluating predicted probability distributions against actual outcomes.
3. **Multiclass Brier Score**: Mean squared difference between predicted probabilities and one-hot encoded true outcomes.
4. **Classification Report**: Precision, recall, and F1-score per match outcome class (`H`, `D`, `A`).

---

# 16. Testing Suite

The project includes an automated test suite implemented with `pytest`.

## 16.1 Test Modules
- `tests/test_model.py`: Validates model training output shapes, feature engineering pipelines, and chronological evaluation execution.
- `tests/test_api.py`: Tests API endpoints and routing logic.
- `tests/test_data.py`: Tests data loading and parsing functions.

## 16.2 Running Tests
Execute the test suite using `pytest`:

```bash
py -m pytest
```

---

**Author:** Laca1234  
**Repository:** https://github.com/Laca1234/Football-AI