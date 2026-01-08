# scripts/init_db.py
from app.db import Base, engine


def init_db():
    # MUST import models to register them with Base to create tables
    from app.models import Account, Notification, Cryptocurrency  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")


if __name__ == "__main__":
    init_db()
