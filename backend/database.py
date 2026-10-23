import os, shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# Ensure migration from aegis.db if arhiea.db does not exist
if 'sqlite' in settings.DATABASE_URL:
    try:
        _db_path = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
        _old_db = _db_path.parent / 'aegis.db'
        if not _db_path.exists() and _old_db.exists():
            shutil.copy2(_old_db, _db_path)
    except Exception:
        pass

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend import models
    Base.metadata.create_all(bind=engine)
