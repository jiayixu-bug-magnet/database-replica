"""Create the class tables and load class_dataset.csv into Railway Postgres.

Connects with DATABASE_URL from .env. Drops and recreates the tables from
schema.sql, then splits the semicolon-separated tools and availability
values into the bridge tables. Prints the row count of every table.
"""

import csv
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent
TABLES = (
    "students",
    "tools",
    "availability",
    "student_tools",
    "student_availability",
)


def load_database_url():
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise SystemExit(f"Missing {env_path}")

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            return value.strip().strip('"').strip("'")

    raise SystemExit("DATABASE_URL is not set in .env")


def dataset_path():
    for path in (ROOT / "data" / "class_dataset.csv", ROOT / "class_dataset.csv"):
        if path.exists():
            return path
    raise SystemExit("Could not find data/class_dataset.csv or class_dataset.csv")


def split_list(cell):
    return [part.strip() for part in cell.split(";") if part.strip()]


def lookup_id(cursor, table, cache, name):
    if name in cache:
        return cache[name]

    cursor.execute(
        f"INSERT INTO {table} (name) VALUES (%s) "
        "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name "
        "RETURNING id",
        (name,),
    )
    row_id = cursor.fetchone()[0]
    cache[name] = row_id
    return row_id


def load_students(cursor, csv_path):
    tool_ids = {}
    availability_ids = {}

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            cursor.execute(
                """
                INSERT INTO students (
                    netid, name, school_year, intro_programming,
                    skill_programming, skill_data_stats,
                    skill_frontend_design, skill_business_pitch,
                    working_style, interests, semester_goal, submitted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING student_id
                """,
                (
                    row["netid"],
                    row["name"],
                    row["school_year"],
                    row["intro_programming"],
                    int(row["skill_programming"]),
                    int(row["skill_data_stats"]),
                    int(row["skill_frontend_design"]),
                    int(row["skill_business_pitch"]),
                    row["working_style"],
                    row["interests"],
                    row["semester_goal"],
                    row["submitted_at"],
                ),
            )
            student_id = cursor.fetchone()[0]

            for tool in split_list(row["tools"]):
                tool_id = lookup_id(cursor, "tools", tool_ids, tool)
                cursor.execute(
                    "INSERT INTO student_tools (student_id, tool_id) VALUES (%s, %s)",
                    (student_id, tool_id),
                )

            for slot in split_list(row["availability"]):
                availability_id = lookup_id(cursor, "availability", availability_ids, slot)
                cursor.execute(
                    """
                    INSERT INTO student_availability (student_id, availability_id)
                    VALUES (%s, %s)
                    """,
                    (student_id, availability_id),
                )


def main():
    schema_sql = (ROOT / "schema.sql").read_text(encoding="utf-8")
    csv_path = dataset_path()

    with psycopg2.connect(load_database_url()) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DROP TABLE IF EXISTS
                    student_tools,
                    student_availability,
                    students,
                    tools,
                    availability
                CASCADE
                """
            )
            cursor.execute(schema_sql)
            load_students(cursor, csv_path)

            print(f"Loaded {csv_path.name}")
            for table in TABLES:
                cursor.execute(f"SELECT count(*) FROM {table}")
                print(f"{table}: {cursor.fetchone()[0]}")


if __name__ == "__main__":
    main()
