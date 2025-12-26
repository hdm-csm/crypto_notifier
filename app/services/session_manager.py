import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from app.db import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')


class SessionManager:
    
    def __init__(self, db: Session = None):
        self._db = db
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        if self._db:
            yield self._db
        else:
            db = SessionLocal()
            try:
                yield db
                db.commit()
            except Exception as e:
                db.rollback()
                logging.error(f"Database error: {e}")
                raise
            finally:
                db.close()
