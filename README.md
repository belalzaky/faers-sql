# FAERS in SQL

Learning SQL by querying the FDA Adverse Event Reporting System (FAERS) — the same public drug-safety dataset explored in [faers-explorer](https://github.com/belalzaky/faers-explorer), now loaded into a local SQLite database and queried with plain SQL instead of pandas. Each script is a self-contained "lap" that introduces one new SQL concept: `COUNT`, `GROUP BY`, `ORDER BY`, and more to come.

## How to run

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Fetch ~3,000 reports from openFDA and build the database
python build_db.py              # creates faers.db

# 4. Run the queries
python query.py                 # first SQL: COUNT(*) and LIMIT
python top_reactions.py         # top 10 reactions with GROUP BY
```

## Scripts

| File | SQL concepts | What it does |
|---|---|---|
| `build_db.py` | `CREATE TABLE`, `INSERT` | Fetches 3,000 FAERS reports via openFDA and loads them into `faers.db` |
| `query.py` | `SELECT`, `COUNT(*)`, `LIMIT` | First queries: row count and a five-row preview |
| `top_reactions.py` | `GROUP BY`, `ORDER BY`, `AS` | Top 10 most-reported adverse reactions |

## Stack

Python 3 · SQLite (built-in) · requests · openFDA drug/event API (free, no key required)
