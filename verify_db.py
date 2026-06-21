from database.connection import execute

tables = execute(
    "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
    fetch="all",
)
print("Tables:", [t["tablename"] for t in tables])
