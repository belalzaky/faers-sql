# build_db.py — fetch ~3300 FAERS reports from openFDA and load them into SQLite
#               Lap 5: stratified by year (300 reports × 11 years, 2013–2023)
#               so the year trend is spread across real calendar time instead
#               of being a consecutive dump from a single year.
#
# ── What is a database? ───────────────────────────────────────────────────────
#
# A database is an organised place to store data so you can search and filter
# it efficiently with a standard language called SQL.
#
# Inside a database there are TABLES. A table is like a spreadsheet:
#   • each COLUMN is one type of information (e.g. "drug", "reaction")
#   • each ROW is one record (e.g. one drug–reaction pair from one report)
#
# This script creates one table called "events" with these columns:
#   report_id  — the FDA's unique ID for the safety report
#   drug       — the name of the drug mentioned in that report
#   reaction   — the adverse reaction term (MedDRA)
#   sex        — 1 = Male, 2 = Female, 0 = Unknown
#   age        — patient age (years; null if not recorded)
#   year       — the year the report was received
#   serious    — 1 = the report was flagged as serious, 2 = not serious
#
# One report can mention several drugs AND several reactions, so we create
# one row for every drug–reaction pair in that report. A report with 2 drugs
# and 3 reactions produces 6 rows, all sharing the same report_id.

import time
import sqlite3    # built into Python — no pip install needed
import requests

DB_FILE = "faers.db"

# ── 1. Fetch ~300 reports per year, 2013–2023 ────────────────────────────────
#
# Old approach: skip=0,100,200,… with no filter → consecutive block of records
# that all happened to be from 2014. Useless for a year-over-year trend.
#
# New approach: add a receivedate range filter for each year so we explicitly
# request records spread across 11 different calendar years.
#
# URL structure:
#   search=receivedate:[20190101+TO+20191231]
#       ↳ only return reports whose receive date falls inside this year
#   &limit=100&skip={skip}
#       ↳ page through up to 300 results per year (3 pages × 100)
#
# With a search filter, the unauthenticated API allows up to 1000 per call,
# but we keep limit=100 and take 3 pages so we don't hammer the free endpoint.

YEARS      = range(2013, 2024)   # 2013 → 2023 inclusive
PER_YEAR   = 300
BATCH_SIZE = 100

# ── Retry-with-backoff helper ─────────────────────────────────────────────────
#
# What is retry-with-backoff?
# ───────────────────────────
# Real-world APIs are imperfect. Even a well-run free service like openFDA
# will occasionally drop a connection, time out, or briefly rate-limit you.
# If your code crashes on the first failure, a single blip wipes out all your
# progress. Retry-with-backoff is the standard fix:
#
#   1. Try the request.
#   2. If it fails, wait a short time and try again.
#   3. Wait a bit longer each time (the "backoff") so you're not spamming
#      a server that's already struggling.
#   4. Give up after a fixed number of attempts.
#
# "Backoff" means the wait grows with each retry:
#   attempt 1 fails → wait 2 s
#   attempt 2 fails → wait 4 s
#   attempt 3 fails → wait 8 s
#   attempt 4 fails → give up and raise the error
#
# This is called "exponential backoff" because the wait doubles each time
# (2^1, 2^2, 2^3 …). It's the industry-standard pattern for any code that
# calls an external service.

def fetch_with_retry(url, max_attempts=4, timeout=20):
    """GET url, retrying up to max_attempts times with exponential backoff."""
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 404:
                return None          # no results — not an error, just empty
            resp.raise_for_status()  # raises on 4xx/5xx
            return resp
        except requests.RequestException as e:
            if attempt == max_attempts:
                raise               # out of retries — let it bubble up
            wait = 2 ** attempt     # 2 s, 4 s, 8 s …
            print(f"\n  ⚠ attempt {attempt} failed ({e}). Retrying in {wait}s…")
            time.sleep(wait)

# ─────────────────────────────────────────────────────────────────────────────

print("Fetching reports from openFDA (300 per year, 2013–2023)…\n")
all_reports = []

for year in YEARS:
    year_reports = []
    for skip in range(0, PER_YEAR, BATCH_SIZE):
        url = (
            "https://api.fda.gov/drug/event.json"
            f"?search=receivedate:[{year}0101+TO+{year}1231]"
            f"&limit={BATCH_SIZE}&skip={skip}"
        )
        resp = fetch_with_retry(url)
        if resp is None:
            break                    # fewer than PER_YEAR reports exist for this year
        year_reports.extend(resp.json()["results"])
        time.sleep(0.5)             # 0.5 s between requests — gentler on the API

    all_reports.extend(year_reports)
    print(f"  {year}: {len(year_reports):>3} reports  (total so far: {len(all_reports):,})")

print(f"\nTotal reports fetched: {len(all_reports):,}")

# ── 2. Flatten reports into rows ──────────────────────────────────────────────
#
# Each raw report is a nested JSON object. We "flatten" it into simple rows
# that fit a table: one row per drug–reaction pair.

rows = []

for report in all_reports:
    report_id = report.get("safetyreportid", "")
    serious   = report.get("serious", 0)

    # receivedate looks like "20210315" → take the first 4 chars for the year
    receive_date = report.get("receivedate", "")
    year = int(receive_date[:4]) if len(receive_date) >= 4 else None

    patient = report.get("patient", {})
    sex     = patient.get("patientsex", 0)
    age     = patient.get("patientage", None)   # may be None if not recorded

    # Build a list of drug names from this report
    drug_names = [
        d.get("medicinalproduct", "").strip().upper()
        for d in patient.get("drug", [])
        if d.get("medicinalproduct")
    ]

    # Build a list of reaction terms from this report
    reaction_terms = [
        r.get("reactionmeddrapt", "").strip().upper()
        for r in patient.get("reaction", [])
        if r.get("reactionmeddrapt")
    ]

    # Cross-join: one row for every (drug, reaction) combination
    for drug in drug_names:
        for reaction in reaction_terms:
            rows.append((report_id, drug, reaction, sex, age, year, serious))

print(f"Rows to insert (drug–reaction pairs): {len(rows):,}")

# ── 3. Create the SQLite database and table ───────────────────────────────────
#
# sqlite3.connect() opens the database file. If the file doesn't exist yet,
# SQLite creates it automatically — no server, no password, just a plain file.
#
# A "connection" is the channel between Python and the database.
# A "cursor" is the object we use to send SQL commands down that channel.

conn   = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# DROP TABLE IF EXISTS means: if a table called "events" already exists from
# a previous run, delete it first so we start fresh.
cursor.execute("DROP TABLE IF EXISTS events")

# CREATE TABLE defines the table's structure — its columns and their types.
# INTEGER stores whole numbers. TEXT stores strings. NULL means "no value".
cursor.execute("""
    CREATE TABLE events (
        report_id  TEXT,
        drug       TEXT,
        reaction   TEXT,
        sex        INTEGER,
        age        REAL,
        year       INTEGER,
        serious    INTEGER
    )
""")

# ── 4. Insert all rows ────────────────────────────────────────────────────────
#
# executemany() is the efficient way to insert many rows at once. The "?"
# placeholders are filled in safely from the tuples in `rows` — this prevents
# a security issue called SQL injection where bad data could corrupt a query.

cursor.executemany(
    "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
    rows,
)

# conn.commit() saves the changes to disk permanently. Without this, the
# inserts would be lost when the script ends.
conn.commit()
conn.close()

print(f"\nDatabase saved to: {DB_FILE}")
print("Table: events")
print(f"Rows: {len(rows):,}")
