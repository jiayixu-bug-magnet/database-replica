# Class database replica

Same process as [pipF26002_database_deploy_exercise](https://github.com/jiayixu-bug-magnet/pipF26002_database_deploy_exercise): `schema.sql`, `class_dataset.csv`, a Python virtual environment, and the loader.

`load_data.py` drops and recreates the tables from `schema.sql`, then loads the survey CSV. `query_db.py` runs the starter queries. Both read `DATABASE_URL` from `.env`. The virtual environment and `.env` stay untracked.

Railway is still offline after the October 21, 2026 outage, so this primes a local Postgres database with the same scripts. When Railway accepts connections again, replace `DATABASE_URL` in `.env` with the Postgres URL from the Railway service and run the loader again. Do not commit that URL.

## Local database

```bash
sudo -u postgres psql -c "CREATE ROLE replica LOGIN PASSWORD 'replica';"
sudo -u postgres psql -c "CREATE DATABASE classdb OWNER replica;"
sudo -u postgres psql -d classdb -c "GRANT ALL ON SCHEMA public TO replica;"
```

## Virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Load and query

```bash
source venv/bin/activate
python load_data.py
python query_db.py
```

A successful load prints 23 students, 5 tools, 6 availability slots, 74 student-tool rows, and 73 student-availability rows.
