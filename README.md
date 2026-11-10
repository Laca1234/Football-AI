# ⚽ Football AI — Premier League Predictor

An AI-powered English Premier League prediction and season simulation platform built with Python, Flask, Scikit-learn, and JavaScript.

Football AI analyzes historical Premier League match data, evaluates team performance, and generates probabilistic predictions for upcoming fixtures. It also features a full-season simulation that produces projected league standings, team statistics, and performance insights.

---

## ✨ Features

### 1. Match Prediction & Probabilistic Evaluation
Predict the outcome probabilities of individual Premier League fixtures.
- Generates probabilities for all three possible outcomes: **H** (Home Win), **D** (Draw), **A** (Away Win).
- Evaluates prediction quality using **Multiclass Log Loss** and **Brier Score** for robust probabilistic calibration.
- Automatically handles edge cases such as missing classes and extreme probabilities with epsilon clipping.

### 2. Full Season Simulation
Simulate an entire Premier League season using the trained machine learning model across 380 fixtures.

### 3. Automated Testing Suite
Includes comprehensive unit and integration tests powered by `pytest` under `tests/`.

---

## 🚀 Installation & Testing

### 1. Clone the Repository
```bash
git clone https://github.com/Laca1234/Football-AI.git
cd Football-AI
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
pip install -r .notes/requirements.txt
```

### 3. Run the Test Suite
Verify model training, feature generation, and evaluation pipelines:
```bash
py -m pytest
```

### 4. Start the Application
```bash
python controller.py
```
Open `http://127.0.0.1:5000` in your browser.

---

## 👨‍💻 Author
**Laca1234**  
Repository: [Football-AI](https://github.com/Laca1234/Football-AI)