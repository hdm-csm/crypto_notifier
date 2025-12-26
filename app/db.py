from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)
Session_Factory = sessionmaker(bind=engine)
Base = declarative_base()

def test_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful:", result.fetchone())
    except Exception as e:
        print("✗ Database connection failed:", e)
        raise

if __name__ == '__main__':
    test_connection()