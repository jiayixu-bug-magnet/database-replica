# Integrating the group model

Instructions for an agent working in the app repo. The model files are already written. Do not edit `cluster_model.py` or `assignment_rules.py`. Change the app so it can call them. Backend only. Do not change the frontend.

## 1. What these two files do

`cluster_model.py` stores the three fitted skill centroids as plain numbers and labels one student by nearest centroid. `assignment_rules.py` labels the whole class with that function, then deals students into groups so the groups mix skill types. The app never refits the model and does not need pandas or scikit-learn.

## 2. Files to copy

Copy these from the model repo into a new `model/` folder next to `app.py`:

- `cluster_model.py`
- `assignment_rules.py`
- `INTEGRATION.md`

Leave them there. `assignment_rules.py` contains `from cluster_model import predict_cluster`. That import only works when `model/` is on `sys.path`. In `app.py`, before importing either file:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "model"))

from assignment_rules import assign_groups
from cluster_model import CENTROIDS
```

Do not rewrite that import inside `assignment_rules.py`, and do not turn `model/` into a package import such as `from model.assignment_rules import ...`.

## 3. The two functions

`predict_cluster(skills)` takes the four ratings in this order: programming, data/stats, frontend design, business pitch. It returns a cluster number, `0`, `1`, or `2`.

```python
predict_cluster([3, 4, 2, 5])  # 0
```

`assign_groups(students, n_groups=8)` takes the whole class. Each student is a dict with `id` and the four skill ratings. It returns a list of dicts with `id`, `cluster`, and `group`. Groups are numbered from 1. One student is a complete example of the shape; the real call passes every student, because the deal depends on the whole class.

```python
assign_groups([
    {
        "id": "jq2306",
        "skill_programming": 3,
        "skill_data_stats": 4,
        "skill_frontend_design": 2,
        "skill_business_pitch": 5,
    }
])
# [{"id": "jq2306", "cluster": 0, "group": 1}]
```

The four skill keys must be those names. Ratings must be numbers, not strings.

## 4. Where the data comes from

The model was fit on `class_dataset.csv`. The app reads Postgres, using `schema.sql`. `load_data.py` loads that CSV into the tables. When Postgres is down, `app.py` loads `database/*.csv` into SQLite and runs the same queries. Both paths use the column names below.

The student `id` is `students.netid`. Do not use `students.student_id`. That value is a generated integer and is not the id the model sorts on.

| What the model needs | Table | Column | Difference from the CSV |
| --- | --- | --- | --- |
| `id` | `students` | `netid` | Same text as the CSV `netid`. Not `student_id`. |
| `skill_programming` | `students` | `skill_programming` | Same name. `SMALLINT` in Postgres, integer in the SQLite fallback. Cast with `int`. |
| `skill_data_stats` | `students` | `skill_data_stats` | Same name. Cast with `int`. |
| `skill_frontend_design` | `students` | `skill_frontend_design` | Same name. Cast with `int`. |
| `skill_business_pitch` | `students` | `skill_business_pitch` | Same name. Cast with `int`. |
| member name in the JSON | `students` | `name` | Not a model input. The CSV also has `name`. Schema says `name` is not unique. |

Leave these out of the model call. They are on `students` but the functions do not read them: `school_year`, `intro_programming`, `working_style`, `interests`, `semester_goal`, `submitted_at`. Tools and availability are not columns. They live in `tools`, `availability`, `student_tools`, and `student_availability`.

Query:

```sql
SELECT netid, name, skill_programming, skill_data_stats,
       skill_frontend_design, skill_business_pitch
FROM students
ORDER BY name
```

Use the same Postgres-or-SQLite connection the roster already uses. Build one dict per row and pass the full list to `assign_groups`.

## 5. Backend

Add `GET /api/groups`. Read every student, call `assign_groups(students, n_groups=8)`, and return JSON. Do not return any one person's cluster. Members are names only.

```json
{
  "n_groups": 8,
  "groups": [
    {
      "group": 1,
      "members": ["Ada Example", "Bo Example"],
      "cluster_counts": {"0": 2, "1": 0, "2": 0}
    }
  ],
  "clusters": [
    {
      "cluster": 0,
      "students": 13,
      "centroid": [2.923076923076923, 3.0769230769230766, 2.8461538461538463, 4.0]
    }
  ],
  "groups_missing_a_cluster": 6
}
```

- `groups` has one object for each group from 1 to 8. `members` is a list of names. `cluster_counts` has a key for every cluster that appears in the class. The keys are the cluster numbers as strings. A count of 0 means that group is missing that cluster.
- `clusters` has one object per cluster. `students` is how many students are in it, not their names. `centroid` is `CENTROIDS[cluster]` from `cluster_model.py`, four numbers in the same skill order as `predict_cluster`.
- `groups_missing_a_cluster` is how many groups have a 0 in `cluster_counts`.
- On a database failure, return a JSON error and status 500. Do not change `GET /`.

## 6. Frontend

Do not change `templates/index.html` or any other page. Nothing new should appear in the browser.

A later page can read this JSON as follows. `n_groups` is 8. Each item in `groups` is one project group: its number, the members' names, and how many people from each skill cluster it has. `clusters` describes the three skill types without naming who is in them: the cluster number, how many students, and the four average ratings. `groups_missing_a_cluster` is how many groups are missing at least one skill type. The page must not expect a cluster label on a person. That field is not in the JSON.

## 7. Packaging

No dependency change. Do not add scikit-learn or pandas to `requirements.txt`.

`Dockerfile` already runs `COPY . .`, and `.dockerignore` does not exclude `model/`. A `model/` folder at the repo root is copied into the image at `/app/model`. `.gitignore` does not ignore it either. Commit the folder. Do not commit `.env`.

The start command stays:

```text
gunicorn --bind 0.0.0.0:${PORT:-5741} app:app
```

`app.py` imports the model modules when it loads, so a deploy without `model/` will fail at startup.

## 8. Test

From the app repo, with its virtual environment active, start the app the same way as the deploy lab:

```text
python app.py
```

The default port is 5741 unless `PORT` is set. In another terminal:

```text
curl http://localhost:5741/api/groups
```

Expect `n_groups` of 8 and `groups_missing_a_cluster` of 6. Group sizes, in order, are 3, 3, 3, 3, 3, 3, 3, 2. Cluster counts by group:

| Group | Size | Cluster 0 | Cluster 1 | Cluster 2 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 3 | 2 | 1 | 0 |
| 2 | 3 | 2 | 1 | 0 |
| 3 | 3 | 2 | 0 | 1 |
| 4 | 3 | 2 | 0 | 1 |
| 5 | 3 | 2 | 0 | 1 |
| 6 | 3 | 1 | 1 | 1 |
| 7 | 3 | 1 | 1 | 1 |
| 8 | 2 | 1 | 1 | 0 |

Cluster sizes are 13, 5, and 5. Open `http://localhost:5741/` and confirm the roster page is unchanged: the same names, averages, and Shuffle button, with no group list.
