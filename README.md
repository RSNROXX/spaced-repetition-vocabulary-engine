# Spaced Repetition Vocabulary Engine

A full-stack web application designed for language learning, utilizing a mathematically rigorous implementation of the SM-2 spaced repetition algorithm to optimize memory retention.

**Live Demo:** [http://rishikeshnaware.pythonanywhere.com](http://rishikeshnaware.pythonanywhere.com)

## 🏗️ Architecture

This application strictly separates the mathematical engine from the web routing and database layers.

* **Backend:** Python 3.10 / Flask
* **Database:** SQLite3 (Persistent local storage)
* **Algorithm:** Pure Python implementation of the SuperMemo-2 (SM-2) engine (`sm2.py`)
* **Frontend:** Vanilla HTML, CSS, and asynchronous JavaScript (`fetch` API)
* **Testing:** Pytest (100% coverage on the SM-2 math engine)

## 🗂️ Core File Structure

* `app.py`: The Flask application and API routing layer.
* `sm2.py`: The isolated spaced-repetition mathematical engine.
* `init_db.py`: The schema generation and initial data seeding script.
* `test_sm2.py`: The Pytest suite verifying standard and edge-case interval calculations.
* `requirements.txt`: Strict dependency locking for production deployment.

## 🚀 Local Development Setup

To run this application on a local development machine, follow these exact steps.

**1. Clone the repository**
```bash
git clone https://github.com/RSNROXX/spaced-repetition-vocabulary-engine
cd spaced-repetition-vocabulary-engine
```

**2. Create and activate a virtual environment**
```bash
# On Linux/macOS
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Initialize the database.** 
***This script will build the vocab.db file and seed it with initial deck and vocabulary data.***
```bash
python init_db.py
```

**5. Launch the Flask development server**
```bash
flask run
```
Access the application at http://127.0.0.1:5000/.

## 🧪 Testing

The mathematical integrity of the SM-2 engine is strictly enforced via Pytest.
To run the test suite:

```bash
pytest test_sm2.py
```

## 🌍 Production Deployment (PythonAnywhere)

This application is configured for deployment on PythonAnywhere via WSGI.

Critical Production Notes:
1. **Absolute Pathing**: The production `app.py` and `init_db.py` must use absolute paths to locate `vocab.db` (e.g., `/home/username/spaced-repetition-vocabulary-engine/vocab.db`). For Linux paths are strictly case-sensitive.
2. **WSGI Configuration**: The web server must point to the specific virtual environment created via `mkvirtualenv` and map the Flask `app` object to `application` in the WSGI config file.
3. **Ephemeral Storage Avoidance**: Standard Docker/Render containers wipe SQLite databases on restart. PythonAnywhere provides the required persistent file system for `vocab.db`.

## 👥 Authors
[Rishikesh Naware](https://github.com/your-github-username)

[Chandu Makuta](https://github.com/madukachandu26-a11y) 
