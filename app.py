"""Show student names from the class database.

The browser asks for /. This file runs SQL against the students table, then
fills in templates/index.html and sends that page back.

DATABASE_URL is read from the environment, then from .env. When that Postgres
database is unreachable, the placeholder CSVs in database/ are loaded into a
local SQLite database and the same queries run there.
"""

import csv
import os
import sqlite3
import sys
from pathlib import Path

from flask import Flask, render_template, request

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "model"))

from assignment_rules import assign_groups
from cluster_model import CENTROIDS

DATABASE_DIR = ROOT / "database"
app = Flask(__name__)

SKILLS = (
    ("Programming", "skill_programming"),
    ("Data and statistics", "skill_data_stats"),
    ("Frontend design", "skill_frontend_design"),
    ("Business pitch", "skill_business_pitch"),
)

STUDENT_COLUMNS = (
    "student_id",
    "netid",
    "name",
    "school_year",
    "intro_programming",
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
    "working_style",
    "interests",
    "semester_goal",
    "submitted_at",
)

INTEGER_COLUMNS = {
    "student_id",
    "id",
    "tool_id",
    "availability_id",
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
}


def database_url():
    """Read DATABASE_URL from the environment, then from .env."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    env_path = ROOT / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            return value.strip().strip('"').strip("'")
    return None


def roster_from_cursor(cursor):
    cursor.execute("SELECT name, school_year FROM students ORDER BY name")
    students = [{"name": row[0], "year": row[1]} for row in cursor.fetchall()]

    averages_sql = ", ".join(f"ROUND(AVG({column}), 2)" for _, column in SKILLS)
    cursor.execute(f"SELECT {averages_sql} FROM students")
    row = cursor.fetchone()
    averages = []
    for (label, _), value in zip(SKILLS, row):
        averages.append(
            {"label": label, "value": None if value is None else f"{float(value):.2f}"}
        )
    return students, averages


def roster_postgres(url):
    import psycopg2

    with psycopg2.connect(url, connect_timeout=3) as conn:
        with conn.cursor() as cursor:
            return roster_from_cursor(cursor)


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def typed_row(columns, row):
    values = []
    for column in columns:
        value = row[column]
        if column in INTEGER_COLUMNS and value != "":
            value = int(value)
        values.append(value)
    return values


def load_table(conn, table, columns):
    rows = csv_rows(DATABASE_DIR / f"{table}.csv")
    placeholders = ", ".join("?" for _ in columns)
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        [typed_row(columns, row) for row in rows],
    )


def placeholder_database():
    """Load database/*.csv into SQLite. Those files mirror the SQL tables."""
    students_csv = DATABASE_DIR / "students.csv"
    if not students_csv.exists():
        raise FileNotFoundError(students_csv)

    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY,
            netid TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            school_year TEXT NOT NULL,
            intro_programming TEXT NOT NULL,
            skill_programming INTEGER NOT NULL,
            skill_data_stats INTEGER NOT NULL,
            skill_frontend_design INTEGER NOT NULL,
            skill_business_pitch INTEGER NOT NULL,
            working_style TEXT NOT NULL,
            interests TEXT NOT NULL,
            semester_goal TEXT NOT NULL,
            submitted_at TEXT NOT NULL
        );
        CREATE TABLE tools (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE availability (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE student_tools (
            student_id INTEGER NOT NULL,
            tool_id INTEGER NOT NULL,
            PRIMARY KEY (student_id, tool_id)
        );
        CREATE TABLE student_availability (
            student_id INTEGER NOT NULL,
            availability_id INTEGER NOT NULL,
            PRIMARY KEY (student_id, availability_id)
        );
        """
    )
    load_table(conn, "students", STUDENT_COLUMNS)
    load_table(conn, "tools", ("id", "name"))
    load_table(conn, "availability", ("id", "name"))
    load_table(conn, "student_tools", ("student_id", "tool_id"))
    load_table(conn, "student_availability", ("student_id", "availability_id"))
    conn.commit()
    return conn


def roster():
    url = database_url()
    if url and url.startswith("postgres"):
        try:
            return roster_postgres(url)
        except Exception:
            local = "localhost" in url or "127.0.0.1" in url
            if not local:
                raise

    conn = placeholder_database()
    try:
        return roster_from_cursor(conn.cursor())
    finally:
        conn.close()


def students_for_groups(cursor):
    cursor.execute(
        """
        SELECT netid, name, skill_programming, skill_data_stats,
               skill_frontend_design, skill_business_pitch
        FROM students
        ORDER BY name
        """
    )
    students = []
    names = {}
    for netid, name, programming, data_stats, frontend, pitch in cursor.fetchall():
        students.append(
            {
                "id": netid,
                "skill_programming": int(programming),
                "skill_data_stats": int(data_stats),
                "skill_frontend_design": int(frontend),
                "skill_business_pitch": int(pitch),
            }
        )
        names[netid] = name
    return students, names


def build_groups(cursor, n_groups=8):
    students, names = students_for_groups(cursor)
    assigned = assign_groups(students, n_groups=n_groups)
    present_clusters = sorted({student["cluster"] for student in assigned})
    groups = []
    missing = 0
    for group_number in range(1, n_groups + 1):
        members = [student for student in assigned if student["group"] == group_number]
        counts = {str(cluster): 0 for cluster in present_clusters}
        for student in members:
            counts[str(student["cluster"])] += 1
        if any(count == 0 for count in counts.values()):
            missing += 1
        groups.append(
            {
                "group": group_number,
                "members": [names[student["id"]] for student in members],
                "cluster_counts": counts,
            }
        )

    sizes = {cluster: 0 for cluster in present_clusters}
    for student in assigned:
        sizes[student["cluster"]] += 1
    clusters = [
        {
            "cluster": cluster,
            "students": sizes[cluster],
            "centroid": list(CENTROIDS[cluster]),
        }
        for cluster in present_clusters
    ]
    return {
        "n_groups": n_groups,
        "groups": groups,
        "clusters": clusters,
        "groups_missing_a_cluster": missing,
    }


def groups_from_database(n_groups=8):
    url = database_url()
    if url and url.startswith("postgres"):
        try:
            import psycopg2

            with psycopg2.connect(url, connect_timeout=3) as conn:
                with conn.cursor() as cursor:
                    return build_groups(cursor, n_groups)
        except Exception:
            local = "localhost" in url or "127.0.0.1" in url
            if not local:
                raise

    conn = placeholder_database()
    try:
        return build_groups(conn.cursor(), n_groups)
    finally:
        conn.close()


def requested_group_count():
    raw = request.args.get("n_groups")
    if raw is None or raw == "":
        return 8
    try:
        n_groups = int(raw)
    except ValueError:
        raise ValueError("n_groups must be a whole number") from None
    if n_groups < 1 or n_groups > 30:
        raise ValueError("n_groups must be from 1 to 30")
    return n_groups


@app.get("/")
def index():
    try:
        students, averages = roster()
    except Exception:
        return render_template("index.html", students=[], averages=[], error=True), 500
    return render_template("index.html", students=students, averages=averages, error=False)


@app.get("/groups")
def groups_page():
    return render_template("groups.html")


@app.get("/api/groups")
def api_groups():
    try:
        return groups_from_database(requested_group_count())
    except ValueError as error:
        return {"error": str(error)}, 400
    except Exception:
        return {"error": "Could not build groups"}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5741"))
    app.run(host="0.0.0.0", port=port)
