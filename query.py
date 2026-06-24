# query.py — connect to faers.db and run your first two SQL queries
#
# SQL (Structured Query Language) is the standard language for asking
# questions of a relational database. Every question is called a QUERY.
#
# The most common SQL command is SELECT, which means:
#   "Go into this table and give me back some rows."
#
# A SELECT statement always follows this pattern:
#   SELECT <what columns>
#   FROM   <which table>
#   WHERE  <optional filter>
#   LIMIT  <optional max rows to return>

import sqlite3

# ── Connect to the database ───────────────────────────────────────────────────
# Same call as in build_db.py, but now we're reading, not writing.

conn   = sqlite3.connect("faers.db")
cursor = conn.cursor()

# ── Query 1: COUNT(*) ─────────────────────────────────────────────────────────
#
# SELECT COUNT(*) FROM events
#
#   SELECT        → "give me back…"
#   COUNT(*)      → "…the total number of rows" (the * means "count everything")
#   FROM events   → "…from the events table"
#
# This is the SQL equivalent of len(df) in pandas.

print("── Query 1: how many rows are in the table? ──────────────────────────")
print("SQL: SELECT COUNT(*) FROM events\n")

cursor.execute("SELECT COUNT(*) FROM events")
result = cursor.fetchone()   # fetchone() retrieves a single row of results
print(f"Total rows in events: {result[0]:,}\n")

# ── Query 2: LIMIT ────────────────────────────────────────────────────────────
#
# SELECT * FROM events LIMIT 5
#
#   SELECT *      → "give me back all columns"  (* means "every column")
#   FROM events   → "from the events table"
#   LIMIT 5       → "but stop after 5 rows"
#
# Without LIMIT, SELECT * would return every row — potentially millions.
# LIMIT is your safety net: always use it when exploring.
#
# This is the SQL equivalent of df.head(5) in pandas.

print("── Query 2: preview the first 5 rows ────────────────────────────────")
print("SQL: SELECT * FROM events LIMIT 5\n")

cursor.execute("SELECT * FROM events LIMIT 5")
rows = cursor.fetchall()   # fetchall() retrieves every row the query returns

# Print a header row using the column names stored in cursor.description
headers = [description[0] for description in cursor.description]
print("  ".join(f"{h:<12}" for h in headers))
print("  ".join("─" * 12 for _ in headers))

for row in rows:
    print("  ".join(f"{str(col):<12}" for col in row))

conn.close()
