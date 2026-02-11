import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config
from contextlib import contextmanager

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
Session_Factory = sessionmaker(bind=engine, expire_on_commit=False)


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
