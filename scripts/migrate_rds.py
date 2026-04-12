"""
scripts/migrate_rds.py — Run ALTER TABLE migrations on RDS.

Usage:
    DATABASE_URL=postgresql://... python scripts/migrate_rds.py

Or pass the URL as an argument:
    python scripts/migrate_rds.py "postgresql://user:pass@host:5432/dbname"
"""
import sys
from sqlalchemy import create_engine, text

MIGRATIONS = [
    # Auth tables are created by create_tables() — this handles ALTER TABLE only
    ("procurement_requests", "company_id", "ALTER TABLE procurement_requests ADD COLUMN company_id UUID REFERENCES companies(id)"),
    ("procurement_requests", "created_by_id", "ALTER TABLE procurement_requests ADD COLUMN created_by_id UUID REFERENCES users(id)"),
    ("purchase_orders", "company_id", "ALTER TABLE purchase_orders ADD COLUMN company_id UUID REFERENCES companies(id)"),
    ("supplier_blacklist", "company_id", "ALTER TABLE supplier_blacklist ADD COLUMN company_id UUID REFERENCES companies(id)"),
]


def column_exists(conn, table, column):
    result = conn.execute(text(
        "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.fetchone() is not None


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        import os
        url = os.environ.get("DATABASE_URL", "")

    if not url:
        print("ERROR: Provide DATABASE_URL as env var or argument")
        sys.exit(1)

    engine = create_engine(url)

    # First, ensure companies and users tables exist via create_tables
    from db.models import Base
    Base.metadata.create_all(engine)
    print("Ensured all tables exist (create_tables)")

    with engine.connect() as conn:
        for table, col, sql in MIGRATIONS:
            if column_exists(conn, table, col):
                print(f"  SKIP  {table}.{col} — already exists")
            else:
                conn.execute(text(sql))
                conn.commit()
                print(f"  ADDED {table}.{col}")

    print("\nMigration complete.")


if __name__ == "__main__":
    main()
