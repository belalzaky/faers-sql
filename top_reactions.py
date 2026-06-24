# top_reactions.py — find the 10 most-reported adverse reactions using SQL
#
# The query we're running:
#
#   SELECT reaction, COUNT(*) AS n
#   FROM events
#   GROUP BY reaction
#   ORDER BY n DESC
#   LIMIT 10;
#
# Let's break it down clause by clause before the code runs.
#
# ── GROUP BY reaction ────────────────────────────────────────────────────────
#
# Without GROUP BY, SELECT would return one line per row (35,565 lines).
# GROUP BY tells the database: "collect all rows that share the same value
# in the `reaction` column into one bucket."
#
# Think of it like sorting a deck of cards by suit — every NAUSEA row goes
# into the NAUSEA pile, every HEADACHE row into the HEADACHE pile, etc.
# After grouping, each pile becomes exactly ONE output row.
#
# ── COUNT(*) AS n ─────────────────────────────────────────────────────────────
#
# COUNT(*) counts the rows in each bucket (pile). The result is the number
# of times that reaction appears across all 35,565 rows.
#
# AS n is an alias — it gives the result column a short name ("n") so the
# rest of the query (and our Python code) can refer to it by that name
# instead of typing COUNT(*) again.
#
# ── ORDER BY n DESC ───────────────────────────────────────────────────────────
#
# ORDER BY sorts the output rows by a column.
# DESC means descending — largest value first (like a leaderboard).
# ASC (ascending, smallest first) is the default if you leave it out.
#
# ── Putting it all together ───────────────────────────────────────────────────
#
# 1. FROM events        → start with all 35,565 rows
# 2. GROUP BY reaction  → collapse into one row per unique reaction term
# 3. COUNT(*) AS n      → for each group, count how many rows it had
# 4. ORDER BY n DESC    → sort by that count, biggest first
# 5. LIMIT 10           → keep only the top 10
#
# Pandas equivalent:
#   df.groupby("reaction").size().reset_index(name="n")
#     .sort_values("n", ascending=False).head(10)

import sqlite3

conn   = sqlite3.connect("faers.db")
cursor = conn.cursor()

SQL = """
    SELECT reaction, COUNT(*) AS n
    FROM events
    GROUP BY reaction
    ORDER BY n DESC
    LIMIT 10
"""

cursor.execute(SQL)
rows = cursor.fetchall()
conn.close()

# ── Print a clean ranked list ─────────────────────────────────────────────────

print("Top 10 Most-Reported Reactions (FAERS sample, 3,000 reports)\n")
print(f"{'Rank':<6}{'Reaction':<40}{'Count':>7}")
print("─" * 53)

for rank, (reaction, count) in enumerate(rows, start=1):
    print(f"{rank:<6}{reaction:<40}{count:>7,}")
