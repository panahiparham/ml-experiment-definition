import sqlite3
from typing import Dict, Iterable, Set

# TODO: find some root-level place to store these types
ValueType = int | float | str | bool

class MetadataTable:
    def __init__(self, part_name: str, version: int):
        self.part_name = part_name
        self.version = version

        # cached results
        self._cols: Set[str] | None = None
        self._configuration_ids: Set[int] | None = None


    def get_table_name(self):
        return f'{self.part_name}-v{self.version}'


    def get_columns(self, cur: sqlite3.Cursor) -> Set[str]:
        if self._cols is not None:
            return self._cols

        res = (
            cur.execute(f"PRAGMA table_info('{self.get_table_name()}')")
            .fetchall()
        )
        self._cols = set(x[1] for x in res)
        return self._cols


    def get_configuration_columns(self, cur: sqlite3.Cursor):
        cols = self.get_columns(cur)
        return cols - {'id'}


    def get_configuration_ids(self, cur: sqlite3.Cursor) -> Set[int]:
        if self._configuration_ids is not None:
            return self._configuration_ids

        res = (
            cur.execute(f"SELECT DISTINCT id FROM '{self.get_table_name()}'")
            .fetchall()
        )
        self._configuration_ids = set(x[0] for x in res)
        return self._configuration_ids


    def get_configuration_id(self, cur: sqlite3.Cursor, configuration: Dict[str, ValueType]) -> int | None:
        col_names = self.get_configuration_columns(cur)

        # if this table does not have the same columns
        # then we already know it does not have the correct id
        # shortcutting here prevents an SQL error due to mismatching columns
        if col_names != set(configuration.keys()):
            return None

        # otherwise, query the table for the id
        table_name = self.get_table_name()
        where = ' AND '.join(f'"{k}"={configuration[k]}' for k in col_names)

        res = (
            cur.execute(f"SELECT id FROM '{table_name}' WHERE {where}")
            .fetchone()
        )

        if res is None:
            return None

        return res[0]

    def get_configuration(self, cur: sqlite3.Cursor, config_id: int) -> Dict[str, ValueType]:
        if config_id not in self.get_configuration_ids(cur):
            raise ValueError(f"config_id <{config_id}> is not in table <{self.get_table_name()}>")

        table_name = self.get_table_name()
        cols = list(self.get_columns(cur))
        col_str = ', '.join(cols)
        res = (
            cur.execute(f"SELECT {col_str} FROM '{table_name}' WHERE id=?", (config_id,))
            .fetchone()
        )

        return {k: v for k, v in zip(cols, res, strict=True)}


    def add_configurations(self, cur: sqlite3.Cursor, configurations: Iterable[Dict[str, ValueType]]):
        # get an ordered list of cols
        cols = list(self.get_columns(cur))

        table_name = self.get_table_name()
        conf_str = ', '.join(['?'] * len(cols))
        col_names = ', '.join(cols)
        conf_values = [[c[k] for k in cols] for c in configurations]

        cur.executemany(f"INSERT INTO '{table_name}' ({col_names}) VALUES ({conf_str})", conf_values)
