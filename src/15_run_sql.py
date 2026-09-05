import duckdb
from pathlib import Path

SQL_FILE = Path("sql/04_executive_commercial_intelligence.sql")

print("=" * 70)
print("RUNNING SQL CUSTOMER INTELLIGENCE")
print("=" * 70)

if not SQL_FILE.exists():
    raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")

sql = SQL_FILE.read_text(encoding="utf-8")

con = duckdb.connect()

try:
    statements = [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]

    for i, statement in enumerate(statements, start=1):

        print()
        print(f"[SQL {i}/{len(statements)}] Executing...")
        print("-" * 70)

        result = con.execute(statement)

        if result.description is not None:

            df = result.df()

            if not df.empty:
                print(df.to_string(index=False))
            else:
                print("Query returned no rows.")

    print()
    print("=" * 70)
    print("SQL CUSTOMER INTELLIGENCE COMPLETE")
    print("=" * 70)

finally:
    con.close()