# Expense Tracker

A small command-line expense tracker written in plain Python, backed by SQLite.
I built it to get hands-on with core Python data structures (lists, tuples,
dicts, sets, `defaultdict`) and to practise a clean CRUD + reporting workflow.

## Features

- Add, view, update and delete expense transactions (SQLite storage)
- Seed random sample data for trying things out
- Spend totals by month, category and merchant
- Reports: top 3 merchants by transaction count, highest-spend category,
  lowest-spend month
- Merchant comparison: merchants used in a month but not in the previous one

## Requirements

- Python 3.8+
- No third-party packages (standard library only)

## Usage

The database file `expensetracker.db` is created automatically on first run.

```bash
# add 50 random sample transactions
python expense_tracker.py seed-data --number-of-transactions 50

# list everything
python expense_tracker.py list-data

# change the amount of one transaction
python expense_tracker.py update-transaction --transaction-id 5 --transaction-amount 1234.50

# delete one transaction (asks for confirmation)
python expense_tracker.py delete-transaction --transaction-id 5

# spend totals by month / category / merchant
python expense_tracker.py run-analytics

# top merchants, highest category, lowest month
python expense_tracker.py spend-reports

# merchants new in October 2026 compared with September 2026
python expense_tracker.py check-merchants --current-year-month 2026-10

# wipe all data (asks for confirmation)
python expense_tracker.py delete-all-data
```

Run `python expense_tracker.py --help` for the full list of actions.

## How it works

Rows are fetched from SQLite as a list of tuples. Totals are built in a single
pass using `defaultdict`, and month-to-month merchant comparisons use a
`defaultdict(set)` with set difference.

## Notes

- Sample data is random and spans the last 365 days, so the first and last
  months are partial.
- Amounts are stored as numbers for simplicity. A production system would
  store money as integer paise or use `Decimal`.

## Roadmap

- Tests with `pytest` for the aggregation logic
- Analysis with pandas / numpy (rolling averages, outlier detection)
- Charts with matplotlib
