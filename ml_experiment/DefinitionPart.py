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

        # get table version
        latest_version = -1
        for t in {t for t in tables if t.startswith(self.name)}:
            version = int(t.replace(self.name + '-v', ''))
            if version > latest_version:
                latest_version = version

        if latest_version == -1:
            for i, configuration in enumerate(configurations):
                configuration['id'] = i
        else:

            # find next id for new configurations
            all_ids = []
            for i in range(latest_version + 1):
                _table_name = self.name + f'-v{i}'
                cur.execute(f"SELECT DISTINCT id FROM '{_table_name}'")
                all_ids.extend([x[0] for x in cur.fetchall()])
            next_id = max(all_ids) + 1

            # assign ids to new configurations / find ids for existing configurations
            for configuration in configurations:
                _id = None

                for i in range(latest_version, -1, -1):
                    table_name = self.name + f'-v{i}'

                    # check if properties match the table schema
                    cur.execute(f"PRAGMA table_info('{table_name}')")
                    columns = set([x[1] for x in cur.fetchall()])

                    if not set(configuration.keys()) == columns - {'id'} :
                        continue

                    # check if configuration exists
                    cur.execute(f"SELECT id FROM '{table_name}' WHERE {' AND '.join([f'{k}=?' for k in configuration.keys()])}", list(configuration.values()))
                    _id = cur.fetchone()
                    if _id:
                        break

                if _id:
                    configuration['id'] = _id[0]
                else:
                    configuration['id'] = next_id
                    next_id += 1

        table_name = self.name + f'-v{latest_version + 1}'

        sqlu.create_table(cur, table_name, list(self._properties.keys()) + ['id INTEGER PRIMARY KEY'])
        conf_string = ', '.join(['?'] * (len(self._properties) + 1))
        column_names = ', '.join(list(self._properties.keys()) + ['id'])
        cur.executemany(f"INSERT INTO '{table_name}' ({column_names}) VALUES ({conf_string})", [list(c.values()) for c in configurations])

        con.commit()
        con.close()


def _init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    return con

def generate_configurations(properties: Dict[str, Set[ValueType]]):
    for configuration in product(*properties.values()):
        yield dict(zip(properties.keys(), configuration, strict=True))
