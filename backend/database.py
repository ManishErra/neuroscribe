from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path
from dotenv import load_dotenv
import os

# Load env file robustly using absolute path relative to database.py
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)

db_url = os.getenv("DATABASE_URL", "")
connect_args = {}
if "postgresql" in db_url or "postgres" in db_url:
    connect_args["sslmode"] = "require"

engine = create_engine(
    db_url,
    connect_args=connect_args
)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()