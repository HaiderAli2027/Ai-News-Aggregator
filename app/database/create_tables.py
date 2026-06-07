import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.exc import OperationalError

from app.database.models import Base
from app.database.connection import engine, get_database_url


if __name__ == "__main__":
    host = get_database_url().split("@")[-1].split("?")[0]
    print(f"Connecting to {host} ...")

    try:
        Base.metadata.create_all(engine)
        print("Tables created successfully:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
    except OperationalError as e:
        print("Failed to connect to the database.")
        print(f"Error: {e.orig}")
        print("\nCheck your .env file in the project root:")
        print("  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB")
        print("For Supabase, POSTGRES_DB should be 'postgres'.")
        sys.exit(1)
