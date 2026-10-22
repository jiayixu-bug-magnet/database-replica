"""Connect to the Railway database and run a few starter queries.

Uses DATABASE_URL from the .env file in this folder. Add your own queries
to the QUERIES list.
"""

from pathlib import Path

import psycopg2

QUERIES = [
    (
        "Student count",
        "SELECT count(*) FROM students;",
    ),
    (
        "Names and school years",
        """
        SELECT name, school_year
        FROM students
        LIMIT 5;
        """,
    ),
    (
        "Students per tool",
        """
        SELECT t.name, COUNT(*) AS n_students
        FROM student_tools st
        JOIN tools t ON st.tool_id = t.id
        GROUP BY t.name
        ORDER BY n_students DESC;
        """,
    ),
    (
        "Students per availability slot",
        """
        SELECT a.name, COUNT(*) AS n_students
        FROM student_availability sa
        JOIN availability a ON sa.availability_id = a.id
        GROUP BY a.name
        ORDER BY n_students DESC;
        """,
    ),
]


def load_database_url():
    env_path = Path(__file__).resolve().parent / ".env"
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


def print_result(title, cursor):
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    print(f"\n{title}")
    print(" | ".join(columns))
    if not rows:
        print("(no rows)")
        return

    for row in rows:
        print(" | ".join("" if value is None else str(value) for value in row))
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


def main():
    database_url = load_database_url()
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            for title, sql in QUERIES:
                cursor.execute(sql)
                print_result(title, cursor)


if __name__ == "__main__":
    main()
