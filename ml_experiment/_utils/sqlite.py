import os
import sqlite3

from typing import Set, List

# --------------
# -- Creation --
# --------------

def create_table(cur: sqlite3.Cursor, table_name: str, columns: List[str]):
    columns_str = ', '.join(columns)
    cur.execute(f"CREATE TABLE '{table_name}' ({columns_str})")

def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    return con


# -------------
# -- Getters --
# -------------

def get_tables(cur: sqlite3.Cursor) -> Set[str]:
    res = cur.execute("SELECT name FROM sqlite_master")
    return set(r[0] for r in res.fetchall())
