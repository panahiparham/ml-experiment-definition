import sys
import os
import sqlite3

from itertools import product

from typing import Dict, Iterable, Set
from collections import defaultdict

import ml_experiment._utils.sqlite as sqlu

ValueType = int | float | str | bool

class DefinitionPart:
    def __init__(self, name: str, base: str | None = None):
        self.name = name
        self.base_path = base or os.getcwd()

        self._properties: Dict[str, Set[ValueType]] = defaultdict(set)

    def add_property(self, key: str, value: ValueType):
        self._properties[key].add(value)

    def add_sweepable_property(self, key: str, values: Iterable[ValueType]):
        self._properties[key] |= set(values)

    def get_results_path(self) -> str:
        import __main__
        experiment_name = __main__.__file__.split('/')[-2]
        return os.path.join(self.base_path, 'results', experiment_name)

    def commit(self):
        configurations = list(generate_configurations(self._properties))

        save_path = self.get_results_path()
        db_path = os.path.join(save_path, 'metadata.db')
        con = _init_db(db_path)
        cur = con.cursor()
        tables = sqlu.get_tables(cur)

        latest_version = 1 # todo

        if latest_version == 1:
            for i, configuration in enumerate(configurations):
                configuration['id'] = i
        else:
            ... # todo

        table_name = self.name + f'-v{latest_version}'


        if table_name not in tables:
            sqlu.create_table(cur, table_name, list(self._properties.keys()) + ['id INTEGER PRIMARY KEY'])
            conf_string = ', '.join(['?'] * (len(self._properties) + 1))
            column_names = ', '.join(list(self._properties.keys()) + ['id'])
            cur.executemany(f"INSERT INTO '{table_name}' ({column_names}) VALUES ({conf_string})", [list(c.values()) for c in configurations])
        else:
            ... # todo

        con.commit()
        con.close()


def _init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    return con

def generate_configurations(properties: Dict[str, Set[ValueType]]):
    for configuration in product(*properties.values()):
        yield dict(zip(properties.keys(), configuration, strict=True))
