# trend.py — count distinct reports per year
#
# The problem with COUNT(*) here
# ────────────────────────────────
# When we built the database, one raw report was "flattened" into many rows —
# one row for every drug–reaction pair. A report with 2 drugs and 3 reactions
# became 6 rows, all sharing the same report_id.
#
# If we wrote COUNT(*) and grouped by year, we'd count rows, not reports.
# A busy report would be counted 6× instead of 1×. The totals would be
# inflated and meaningless as a report count.
#
# The fix: COUNT(DISTINCT report_id)
# ─────────────────────────────────────────────────────────────────────────────
# DISTINCT tells COUNT to deduplicate before counting.
#
#   COUNT(*)                 → count every row, including duplicates
#   COUNT(DISTINCT report_id) → count each unique report_id only once
#
# Example with four rows in year 2020:
#
#   report_id  | drug    | reaction
#   -----------+---------+----------
#   RPT-001    | HUMIRA  | NAUSEA       ← \
#   RPT-001    | HUMIRA  | HEADACHE     ←  } same report → should count as 1
#   RPT-002    | ASPIRIN | PAIN         ←    different report → count as 1
#
#   COUNT(*)                  = 3   ← wrong; inflated by flattening
#   COUNT(DISTINCT report_id) = 2   ← correct; two real reports
#
# Pandas equivalent:
#   df.groupby("year")["report_id"].nunique()

import sqlite3

conn   = sqlite3.connect("faers.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT year, COUNT(DISTINCT report_id) AS reports
    FROM events
    GROUP BY year
    ORDER BY year
""")

rows = cursor.fetchall()
conn.close()

print("FAERS Reports per Year (sample of 3,000 reports)\n")
print(f"{'Year':<8}{'Reports':>9}")
print("─" * 18)

for year, reports in rows:
    bar = "█" * (reports // 5)          # one block per 5 reports
    print(f"{str(year):<8}{reports:>9,}  {bar}")
