# build_db.py — fetch ~3000 FAERS reports from openFDA and load them into SQLite
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

# ── 1. Fetch ~3000 reports from openFDA ──────────────────────────────────────
#
# The API returns at most 1000 results per call, so we make 3 calls and
# combine them. The "skip" parameter tells the API how many results to
# jump over before returning the next batch — like page numbers.

# The unauthenticated openFDA API caps each request at 100 results when
# there is no search filter. We page through 30 batches of 100 to reach 3,000.
BASE_URL = (
    "https://api.fda.gov/drug/event.json"
    "?limit=100&skip={skip}"
)

TOTAL_WANTED = 3000
BATCH_SIZE   = 100

print("Fetching reports from openFDA…")
all_reports = []

for skip in range(0, TOTAL_WANTED, BATCH_SIZE):
    resp = requests.get(BASE_URL.format(skip=skip), timeout=15)
    resp.raise_for_status()
    batch = resp.json()["results"]
    all_reports.extend(batch)
    print(f"  {len(all_reports):,} / {TOTAL_WANTED} reports fetched", end="\r")
    time.sleep(0.3)   # be polite to the free API

print(f"\nTotal reports fetched: {len(all_reports):,}")

print(f"Total reports fetched: {len(all_reports)}")

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
