# CryptoNotifier

A Crypto Tracking Tool.

# Development Setup

## Develop and run on your Local Machine

### Prerequisites

- Python 3.12
- Docker Engine
- [recommended] Anaconda for virtual environment management
- [recommended] DBeaver for database management

### Setup Steps

### initial setup

1. Clone the repo: `git clone <repo_url>`
2. Navigate into project directory: `cd CryptoNotifier`
3. [recommended] Create and activate virtual environment
4. Update `.env.dev` with your configuration (DB credentials, API keys, etc.)
- Schema for Mysql Database URL:
`DATABASE_URL=mysql+mysqldb://<user>:<password>@<host>[:<port>]/<dbname>`
- Note: Use `127.0.0.1` instead of `localhost` in the `DATABASE_URL`

### Daily Development

1. Pull latest changes: `git pull origin <your_branch>`
2. Start MySQL container only: `docker-compose -f docker-compose.dev.yml up -d` \
or with new docker compose command: `docker compose -f docker-compose.dev.yml up -d`
3. Install requirements locally: `pip install -r requirements.txt`
4. Set Python path to project root: `export PYTHONPATH=$PYTHONPATH:$(pwd)` (so imports work correctly)
5. Initialize and seed DB:
   - `python scripts/init_db.py` / `python -m scripts.init_db`
   - `python scripts/seed_data.py` / `python -m scripts.seed_data` -> adds sample data
6. Run your app: `python -m app.main` -> start software
7. Run tests: `python -m pytest` or `python -m pytest tests/unit` -> run all tests or only e.g. unit tests

### Code-Qualität
Nutzung von Black, MyPy & Flake8 für automatisierte Formatierung & Linting. Diese werden über Pre-Commit Hooks gesteuert.
1. Installiere die Entwickler-Abhängigkeiten: `pip install -r requirements-dev.txt`
2. Pre-Commit Hooks aktivieren: `pre-commit install`
Hinweis: Der Befehl pre-commit install sorgt dafür, dass bei jedem git commit automatisch geprüft wird, ob der Code sauber ist.

Damit du nicht manuell formatieren musst, richte deine IDE so ein, dass es den Code beim Speichern automatisch bereinigt mit Black & MyPy.
1. Installiere die "Black Formatter" Extension.
2. Einstellungen -> "Format On Save" aktivieren.
3. Einstellungen -> Default Formatter und wähle Black Formatter.
4. Installiere die "Mypy Type Checker" Extension & aktiviere sie.

#### MyPy Mini-Tutorial:
Statt:
`price = 50000.50`
`name = "Bitcoin"`
`def check_limit(current_price, limit): return current_price > limit`
Mit MyPy nun pflicht:
`price: float = 50000.50`
`name: str = "Bitcoin"`
`def check_limit(current_price: float, limit: float) -> bool: return current_price > limit'`

### Testing

```
docker-compose -f docker-compose.test.yml --env-file .env.test up -d --build
```

```
docker exec crypto_notifier_app_test pytest -v
```

# Branching and deployment Strategy

- `feature/` for new features
- `release/` for release candidates
- `main` is the production branch
  - push to main triggers the ci/cd-pipeline including deployment to production server
