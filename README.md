Footy AI
A machine-learning-powered Premier League match predictor and season simulator.

Footy AI is a web application that uses historical English Premier League results to estimate match outcomes and simulate a league season. It combines a Python prediction backend with a lightweight JavaScript frontend.

The application is designed to explore how historical team performance, recent form and goal statistics can be used to model football outcomes.
Features
- Match predictions – Select home and away teams and receive estimated home-win, draw and away-win probabilities.
- Multiple match predictions – Add more than one fixture to a prediction request.
- Season simulation – Simulate a complete league season and generate a predicted table.
- Season insights – Display additional standings-based insights, including top-four positions, relegation places, goals scored and goal difference.
- Upcoming fixtures – Retrieve upcoming Premier League fixtures from TheSportsDB.
- Historical data – Load match results across multiple seasons.
- Local data cache – Store downloaded season data as JSON to reduce repeated API requests.
- Responsive interface – A custom HTML, CSS and JavaScript interface with dark/light theme support.
Technology Stack
Technology	Purpose
Python	Backend and prediction logic
Flask	Web server and REST API
Flask-CORS	Cross-origin request support
pandas	Historical match data processing
NumPy	Numerical operations and simulation
scikit-learn	Gradient Boosting classification model
HTML, CSS, JavaScript	Frontend
TheSportsDB API	Premier League results and fixtures


How It Works
1. Historical Premier League results are loaded from the local cache where available.
2. Missing season data is requested from TheSportsDB and saved locally.
3. The backend processes match results and builds team-performance features.
4. A Gradient Boosting classifier is trained using the historical dataset.
5. The prediction service estimates the probabilities of a home win, draw or away win.
6. The season simulator uses the model to simulate fixtures and calculate a final league table.
The model uses historical results and team statistics. Predictions are estimates, not guarantees of real-world outcomes.
Project Structure
The application is currently stored inside nested project folders:
Football-AI/
└── Footy AI project/
    ├── FOOTY.png
    └── Footy AI project/
        └── premier-league/
            ├── _cache/
            ├── controller.py
            ├── model.py
            ├── service.py
            ├── import sys.py
            ├── static/
            │   ├── App.js
            │   └── styles.css
            └── templates/
                └── index.html
Requirements
- Python 3.10 or newer
- pip
- Internet connection for retrieving uncached historical data and upcoming fixtures
Installation and Setup
1. Clone the repository
git clone https://github.com/Laca1234/Football-AI.git
cd Football-AI
2. Navigate to the application directory
cd "Footy AI project/Footy AI project/premier-league"
3. Create and activate a virtual environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / macOS
python3 -m venv venv
source venv/bin/activate
4. Install dependencies
The repository does not currently include a requirements.txt file. Install the backend dependencies with:
pip install Flask Flask-Cors numpy pandas scikit-learn
5. Start the application
python controller.py
Open the application in your browser:
http://127.0.0.1:5000
The first startup may take longer if historical season data needs to be downloaded. Retrieved data is cached for subsequent runs.
API Endpoints
Endpoint	Method	Description
/	GET	Serves the web application
/api/teams	GET	Returns the available teams and current season information
/api/predict	POST	Predicts the selected match or matches
/api/simulate	POST	Runs a full-season simulation
/api/fixtures	GET	Retrieves upcoming Premier League fixtures


Notes and Limitations
- Prediction quality depends on the completeness and quality of the historical data.
- Upcoming fixture information requires access to TheSportsDB.
- First-time data retrieval can take several minutes.
- Football predictions are probabilistic estimates and should not be treated as certain results.
- The repository currently has no dedicated dependency lockfile or automated test suite.
License
No license has currently been specified for this repository.
