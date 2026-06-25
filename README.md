# FAERS in SQL

Learning SQL by querying the FDA Adverse Event Reporting System (FAERS) — the same public drug-safety dataset explored in [faers-explorer](https://github.com/belalzaky/faers-explorer), now loaded into a local SQLite database and queried with plain SQL. Each script introduces one new concept, building from a blank database to real analytical questions.

> First-year Pharmacology student at King's College London, building data skills in public.
> Write-ups: [belalzaky.substack.com](https://belalzaky.substack.com) · [LinkedIn](https://www.linkedin.com/in/belalzaky)

---

## What this project does

`build_db.py` pulls ~3,300 adverse-event reports from the free [openFDA API](https://open.fda.gov/apis/drug/event/) — 300 reports per year from 2013 to 2023 — and loads them into a local SQLite database (`faers.db`). Each report can mention several drugs and several reactions, so the table stores one row per drug–reaction pair (~52,000 rows from 3,300 reports). The remaining scripts each ask one analytical question using SQL.

---

## Files

| File | SQL concepts | What it does |
|---|---|---|
| `build_db.py` | `CREATE TABLE`, `INSERT` | Fetches 3,300 FAERS reports from openFDA (year-stratified, with retry-with-backoff) and loads them into `faers.db` |
| `query.py` | `SELECT`, `COUNT(*)`, `LIMIT` | First queries: total row count and a five-row preview |
| `top_reactions.py` | `GROUP BY`, `ORDER BY`, `AS` | Top 10 most-reported adverse reactions across all drugs |
| `drug_reactions.py` | `WHERE` | Top 10 drugs by report count, then top 10 reactions for the #1 drug |
| `trend.py` | `COUNT(DISTINCT ...)` | Reports per year, deduplicating by report ID so each real report counts once |

---

## How to run

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies (just requests — sqlite3 is built into Python)
pip install -r requirements.txt

# 3. Build the database (~90 seconds; fetches from the openFDA API)
python build_db.py

# 4. Run each query script
python query.py
python top_reactions.py
python drug_reactions.py
python trend.py
```

`faers.db` is listed in `.gitignore` — it's a generated file, not source code. Anyone cloning this repo runs `build_db.py` to recreate it.

---

## What I learned

### SQL: GROUP BY, WHERE, COUNT(DISTINCT)

`GROUP BY` collapses many rows into one per unique value — the foundation of any aggregation query. `WHERE` filters rows *before* grouping, acting as a sieve that narrows the dataset to a specific drug, year, or condition. Understanding that `WHERE` runs before `GROUP BY` (and that `HAVING` runs after) is the key to writing correct aggregate queries.

`COUNT(DISTINCT report_id)` versus `COUNT(*)` was the most important distinction in this project. Because one report becomes many rows after flattening, a plain `COUNT(*)` inflates totals by however many drug–reaction pairs each report contained. `DISTINCT` deduplicates first, so the count reflects real reports rather than rows.

### Retry-with-backoff

Any code that calls an external API needs to handle transient failures gracefully. A single dropped connection or momentary rate-limit shouldn't crash a 30-minute data collection run. The standard pattern — catch the exception, wait `2^attempt` seconds, try again up to N times — is called exponential backoff. It's in production systems everywhere.

### Balanced sampling ≠ representative sampling

Fetching exactly 300 reports per year produced a clean, evenly distributed dataset that's useful for learning SQL joins and aggregations. But it's not representative of FAERS: the real database has far more reports in later years (reporting volume grew substantially after 2015) and certain years are dominated by single events like the 2019 Zantac recall. A balanced sample answers "what SQL can I write?" — a representative sample is needed before drawing any real pharmacovigilance conclusions.

---

## Stack

Python 3 · SQLite (built-in) · requests · openFDA drug/event API (free, no key required)
