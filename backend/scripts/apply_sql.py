import os
from pathlib import Path
from sqlalchemy import text
import sys

# Add backend to sys.path so we can import database
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import engine

def apply_sql():
    sql_file = Path(__file__).resolve().parent.parent / "sql" / "create_users_table.sql"
    if not sql_file.exists():
        print(f"Error: SQL file {sql_file} not found.")
        sys.exit(1)
        
    print(f"Reading SQL file: {sql_file}")
    with open(sql_file, "r") as f:
        sql_content = f.read()
        
    # Split the commands by semicolon (simple parser, ignore semicolons in comments/strings)
    # But PostgreSQL can execute multiple statements in a single text() block!
    # Let's execute it directly.
    print("Executing SQL statements against database...")
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text(sql_content))
            trans.commit()
            print("SQL migration applied successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Failed to execute SQL migration: {e}")
            sys.exit(1)

if __name__ == "__main__":
    apply_sql()
