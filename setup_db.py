"""One-time setup: creates the database and runs the schema."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path


def create_database():
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="postgres",
        user="postgres", password="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'forget_me_not'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE forget_me_not")
        print("Database 'forget_me_not' created.")
    else:
        print("Database already exists — skipping creation.")
    cur.close()
    conn.close()


def run_schema():
    schema = (Path(__file__).parent / "database" / "schema.sql").read_text()
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="forget_me_not",
        user="postgres", password="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(schema)
    cur.close()
    conn.close()
    print("Schema applied.")


if __name__ == "__main__":
    create_database()
    run_schema()
    print("Setup complete. Run:  python main.py")
