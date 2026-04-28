import sqlite3
from collections import deque
from pathlib import Path

from flow import build_text2sql_flow


def _seed_db(path: Path) -> None:
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, country TEXT);
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY, customer_id INTEGER,
                amount REAL, ts TEXT
            );
            INSERT INTO customers (name, country) VALUES
                ('Alice', 'US'), ('Bob', 'UK'), ('Carol', 'US'),
                ('Dave', 'DE'), ('Eve', 'UK');
            INSERT INTO orders (customer_id, amount, ts) VALUES
                (1, 100, '2024-01-01'), (1, 250, '2024-02-01'),
                (2, 50,  '2024-01-15'), (3, 700, '2024-03-01'),
                (4, 30,  '2024-02-12'), (5, 410, '2024-03-22');
        """)


def main() -> None:
    here = Path(__file__).parent
    db = here / "shop.sqlite"
    _seed_db(db)
    store = {
        "db_path": str(db),
        "question": "What is the total order amount per country, sorted descending?",
    }
    deque(build_text2sql_flow()(store=store), maxlen=0)


if __name__ == "__main__":
    main()
