import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "postgres")

    url = (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{db}"
    )

    ssl_mode = os.getenv("POSTGRES_SSLMODE")
    if ssl_mode:
        url += f"?sslmode={ssl_mode}"
    elif "supabase.co" in host or os.getenv("POSTGRES_SSL", "").lower() in ("1", "true", "yes"):
        url += "?sslmode=require"

    return url


engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    return SessionLocal()
