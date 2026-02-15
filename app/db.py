import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from config import Config

DATABASE_URL = Config.DATABASE_URL

# Better engine settings for bot workloads
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,      # prevents stale connections
    pool_recycle=3600        # refresh connections periodically
)

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,         # prevents unexpected flush
    autocommit=False,
    expire_on_commit=False
)

Base = declarative_base()


@contextmanager
def session_scope():
    """
    Provides a transactional scope.
    Safe for Telegram notification writes.
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        logging.error("DB session error, rolling back.", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


def get_session():
    """
    Use this when you need manual control (e.g., async bot handlers).
    """
    return SessionFactory()


def test_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful:", result.fetchone())
    except Exception as e:
        print("✗ Database connection failed:", e)
        raise


if __name__ == "__main__":
    test_connection()
## fixed the Prevents lost notifications due to stale DB connections
#Ensures commits always happen
#Avoids unexpected auto-flush errors
#Gives you get_session() for bot handlers
