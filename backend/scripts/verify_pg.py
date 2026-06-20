import os
import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import text, inspect

load_dotenv()
db_url = os.environ.get('DATABASE_URL')

# Redact password for printing
parts = db_url.split('@')
if len(parts) == 2:
    credentials = parts[0].split(':')
    redacted_url = f"{credentials[0]}:***@{parts[1]}"
else:
    redacted_url = "INVALID_URL_FORMAT"

print(f"--- DATABASE CONFIGURATION ---")
print(f"Redacted URL: {redacted_url}")
print(f"APP_ENV: {os.environ.get('APP_ENV')}")

engine = sqlalchemy.create_engine(db_url)
print(f"\n--- ENGINE DIALECT ---")
print(f"Dialect Name: {engine.name}")

if engine.name == "sqlite":
    print("FAIL: Engine is SQLite. Silent fallback occurred.")
    exit(1)

with engine.connect() as conn:
    print(f"\n--- POSTGRESQL ENVIRONMENT ---")
    result = conn.execute(text("SELECT current_database(), version();")).fetchone()
    print(f"Current Database: {result[0]}")
    print(f"Version: {result[1]}")
    
    print(f"\n--- PGVECTOR EXTENSION ---")
    ext = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).fetchone()
    if ext:
        print("pgvector extension: INSTALLED")
    else:
        print("pgvector extension: MISSING")

print(f"\n--- TABLE VERIFICATION ---")
inspector = inspect(engine)
tables = inspector.get_table_names()

required_tables = ['users', 'patients', 'sessions', 'transcripts', 'notes', 'reports', 'embeddings']
for table in required_tables:
    if table in tables:
        print(f"Table '{table}': EXISTS")
    else:
        print(f"Table '{table}': MISSING")

print(f"\nALL CHECKS COMPLETED.")
