# utils/db.py
from sqlalchemy import create_engine
from config import DATABASE_URL

# Global SQLAlchemy engine – reused everywhere
engine = create_engine(DATABASE_URL, future=True)
