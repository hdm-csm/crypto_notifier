# CryptoNotifier

A Crypto Tracking Tool.

# Develop and run on your local machine (host Python)

You run Python on your host machine (VS Code / terminal / PyCharm).
Your code is in the same folder, with your virtual environment activated.
Connect to the Postgres container via the exposed port (localhost:5432).
Example DATABASE_URL for host dev: postgresql+psycopg2://user:pass@localhost:5432/crypto_db

## Workflow:

### Local Development

1. Start MySQL container only: `docker-compose -f docker-compose.dev.yml up -d`
2. Install requirements locally: `pip install -r requirements.txt`
3. Initialize and seed DB:
   - `python scripts/init_db.py`
   - `python scripts/seed.py` -> adds sample data
4. Run your app: `python -m app.main` -> start software
5. Run tests: `python -m pytest` or `python -m pytest tests/unit` -> run all tests or only e.g. unit tests
