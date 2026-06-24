# drug_reactions.py — filter to one drug's reactions using WHERE
#
# New concept: WHERE
# ─────────────────
# WHERE is a row filter. It runs BEFORE any grouping or counting, and it
# throws away every row that doesn't match its condition — just like
# df[df["drug"] == "HUMIRA"] in pandas.
#
# The key difference between WHERE and GROUP BY:
#
#   WHERE   → decides which ROWS enter the query  (a sieve)
#   GROUP BY → decides how the surviving rows are COLLAPSED  (a pile-sorter)
#
# You always write them in this order:
#   SELECT … FROM … WHERE … GROUP BY … ORDER BY … LIMIT …
#
# SQL executes them in this logical order too:
#   1. FROM      — pick the table
#   2. WHERE     — discard rows that don't match
#   3. GROUP BY  — collapse what's left into buckets
#   4. SELECT    — compute COUNT(*) etc. for each bucket
#   5. ORDER BY  — sort the buckets
#   6. LIMIT     — keep only the top N

import sqlite3

conn   = sqlite3.connect("faers.db")
cursor = conn.cursor()

# ── Query 1: top 10 drugs ─────────────────────────────────────────────────────
# No WHERE here — we want every row, grouped by drug name.

print("Top 10 Most-Reported Drugs\n")
print(f"{'Rank':<6}{'Drug':<40}{'Count':>7}")
print("─" * 53)

cursor.execute("""
    SELECT drug, COUNT(*) AS n
    FROM events
    GROUP BY drug
    ORDER BY n DESC
    LIMIT 10
""")

top_drugs = cursor.fetchall()

for rank, (drug, count) in enumerate(top_drugs, start=1):
    print(f"{rank:<6}{drug:<40}{count:>7,}")

# ── Pick the #1 drug and query its reactions ──────────────────────────────────

top_drug = top_drugs[0][0]   # first row, first column = drug name

print(f"\n\nTop 10 Reactions for {top_drug}\n")
print(f"{'Rank':<6}{'Reaction':<40}{'Count':>7}")
print("─" * 53)

# WHERE drug = ? filters the table to only rows where the drug column
# matches top_drug. The "?" placeholder is filled in safely by sqlite3
# (same SQL-injection protection as in build_db.py).
cursor.execute("""
    SELECT reaction, COUNT(*) AS n
    FROM events
    WHERE drug = ?
    GROUP BY reaction
    ORDER BY n DESC
    LIMIT 10
""", (top_drug,))

for rank, (reaction, count) in enumerate(cursor.fetchall(), start=1):
    print(f"{rank:<6}{reaction:<40}{count:>7,}")

conn.close()
