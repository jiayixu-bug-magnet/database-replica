"""Show student names from the placeholder CSV database.

The browser asks for /. This file reads database/students.csv, then fills
in templates/index.html and sends that page back. That folder stands in
for Postgres until the real database is connected.
"""

import csv
from pathlib import Path

from flask import Flask, render_template

ROOT = Path(__file__).resolve().parent
STUDENTS_CSV = ROOT / "database" / "students.csv"
app = Flask(__name__)

SKILLS = (
    ("Programming", "skill_programming"),
    ("Data and statistics", "skill_data_stats"),
    ("Frontend design", "skill_frontend_design"),
    ("Business pitch", "skill_business_pitch"),
)


def roster():
    if not STUDENTS_CSV.exists():
        raise FileNotFoundError(STUDENTS_CSV)

    with STUDENTS_CSV.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    names = sorted(row["name"] for row in rows)
    averages = []
    for label, column in SKILLS:
        ratings = [int(row[column]) for row in rows]
        value = round(sum(ratings) / len(ratings), 2) if ratings else None
        averages.append({"label": label, "value": value})
    return names, averages


@app.get("/")
def index():
    try:
        names, averages = roster()
    except Exception:
        return render_template("index.html", names=[], averages=[], error=True), 500
    return render_template("index.html", names=names, averages=averages, error=False)


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "5741"))
    app.run(host="0.0.0.0", port=port)
