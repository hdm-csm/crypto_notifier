import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config
from contextlib import contextmanager

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,  # 5 connections open to the DB at all times, even if they aren't being used
    max_overflow=5,  # up to 5 temporary extra connections, if the main 5 are busy
    pool_pre_ping=True,  # Before giving the bot a connection, the engine checks if it's still alive (usually by running SELECT 1)
    pool_recycle=3600,  # If a connection has been open for 1 hour, close it and open a new one.
    pool_timeout=30,  # If all 10 connections (5 size + 5 overflow) are busy, wait 30s for one to free up before crashing
    connect_args={"connect_timeout": 10, "charset": "utf8mb4"},  # Network timeout
)
Session_Factory = sessionmaker(
    bind=engine,
    autoflush=False,  # change a user's setting in code but haven't committed yet, querying that user won't force a write.
    autocommit=False,
    expire_on_commit=False,  # After you commit, the Python objects remain valid and readable without reloading data from the DB
    join_transaction_mode="create",
)


def get_session():
    """
    Get a new database session.
    Use this when you need manual control over session lifecycle
    (e.g., async bot handlers, scripts).
    """
    return Session_Factory()


# "with Session.begin() as session" would also commit the transaction + close the session
@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session_Factory()
    try:
        yield session
        session.commit()
    except Exception:
        logging.error("Error in session_scope, rolling back transaction.", exc_info=True)
        session.rollback()
        raise  # re-throw the exception
    finally:
        session.close()


Base = declarative_base()


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
