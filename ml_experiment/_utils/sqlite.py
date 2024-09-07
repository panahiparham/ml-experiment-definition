from sqlite3 import Cursor
from typing import Set, List

def get_tables(cur: Cursor) -> Set[str]:
    res = cur.execute("SELECT name FROM sqlite_master")
    return set(r[0] for r in res.fetchall())

def create_table(cur: Cursor, table_name: str, columns: List[str]):
    columns_str = ', '.join(columns)
    cur.execute(f"CREATE TABLE '{table_name}' ({columns_str})")
