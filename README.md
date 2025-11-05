# CryptoNotifier

A Crypto Tracking Tool.

# Develop and run on your Local Machine

1. Start MySQL container only: `docker-compose -f docker-compose.dev.yml up -d`
2. Install requirements locally: `pip install -r requirements.txt`
3. Initialize and seed DB:
   - `python scripts/init_db.py`
   - `python scripts/seed.py` -> adds sample data
4. Run your app: `python -m app.main` -> start software
5. Run tests: `python -m pytest` or `python -m pytest tests/unit` -> run all tests or only e.g. unit tests

# Branching and deployment

- `feature/` for new features
- `release/` for release candidates
- `main` is the production branch
  - push to main triggers the ci/cd-pipeline including deployment to production server
