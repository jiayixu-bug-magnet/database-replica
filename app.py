"""Show student names from the class database.

The browser asks for /. This file asks Postgres for the names, then fills
in templates/index.html and sends that page back.
"""

import os
from pathlib import Path

import psycopg2
from flask import Flask, render_template

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)


def database_url():
    """Read DATABASE_URL from the environment, then from .env."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    env_path = ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError("DATABASE_URL is not set and .env is missing")

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            return value.strip().strip('"').strip("'")

    raise RuntimeError("DATABASE_URL is not set in .env")


def student_names():
    with psycopg2.connect(database_url()) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM students ORDER BY name")
            return [row[0] for row in cursor.fetchall()]


@app.get("/")
def index():
    try:
        names = student_names()
    except Exception:
        return render_template("index.html", names=[], error=True), 500
    return render_template("index.html", names=names, error=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5741"))
    app.run(host="0.0.0.0", port=port)
