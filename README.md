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
4. Initialize and seed DB:
   - `python scripts/init_db.py` / `python -m scripts.init_db`
   - `python scripts/seed_data.py` / `python -m scripts.seed_data` -> adds sample data
5. Run your app: `python -m app.main` -> start software
6. Run tests: `python -m pytest` or `python -m pytest tests/unit` -> run all tests or only e.g. unit tests

# Branching and deployment Strategy

- `feature/` for new features
- `release/` for release candidates
- `main` is the production branch
  - push to main triggers the ci/cd-pipeline including deployment to production server
