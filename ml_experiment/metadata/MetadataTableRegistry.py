import sqlite3
import ml_experiment._utils.sqlite as sqlu

from typing import Dict, Iterable
from ml_experiment.metadata.MetadataTable import MetadataTable, ValueType


class MetadataTableRegistry:
    def __init__(self):
        # cached results
        self._latest_versions: Dict[str, int] = {}
        self._tables: Dict[str, MetadataTable] = {}


    def get_table(self, cur: sqlite3.Cursor, part_name: str, version: int) -> MetadataTable | None:
        table_name = f'{part_name}-v{version}'

        # check cache
        if table_name in self._tables:
            return self._tables[table_name]

        # ensure table exists
        tables = sqlu.get_tables(cur)
        if table_name not in tables:
            return None

        # construct table object
        self._tables[table_name] = table = MetadataTable(part_name, version)
        return table


    def get_tables(self, cur: sqlite3.Cursor, part_name: str):
        table_names = sqlu.get_tables(cur)

        for t in table_names:
            if not t.startswith(part_name):
                continue

            version = int(t.replace(f'{part_name}-v', ''))
            table = self.get_table(cur, part_name, version)

            if table is not None:
                yield table


    def get_latest_version(self, cur: sqlite3.Cursor, part_name: str) -> MetadataTable | None:
        if part_name in self._latest_versions:
            version = self._latest_versions[part_name]
            return self.get_table(cur, part_name, version)


        tables = list(self.get_tables(cur, part_name))
        if len(tables) == 0:
            return None

        latest = max(t.version for t in tables)
        self._latest_versions[part_name] = latest
        return self.get_table(cur, part_name, latest)


    def get_max_configuration_id(self, cur: sqlite3.Cursor, part_name: str) -> int:
        all_ids = set[int]()

        tables = self.get_tables(cur, part_name)
        for t in tables:
            all_ids |= t.get_configuration_ids(cur)

        # define the no configurations case (e.g. this is table v0)
        # as having a max id of -1
        if len(all_ids) == 0:
            return -1

        return max(all_ids)


    def get_configuration_id(self, cur: sqlite3.Cursor, part_name: str, configuration: Dict[str, ValueType]) -> int | None:
        latest = self.get_latest_version(cur, part_name)

        if latest is None:
            return None

        # walk backwards starting from the latest version
        # if any table contains an id, then stop
        for i in range(latest.version + 1):
            table = self.get_table(cur, part_name, version=latest.version - i)

            if table is None:
                continue

            conf_id = table.get_configuration_id(cur, configuration)
            if conf_id is not None:
                return conf_id

        return None


    def create_new_table(self, cur: sqlite3.Cursor, part_name: str, version: int, config_params: Iterable[str]) -> MetadataTable:
        table_name = f'{part_name}-v{version}'
        sqlu.create_table(cur, table_name, list(config_params) + ['id INTEGER PRIMARY KEY'])

        # since we just created this table, it better be there!
        table = self.get_table(cur, part_name, version)
        assert table is not None

        # invalidate the version cache, since we should now have a new version
        # assert that versions are strictly monotonically increasing
        if part_name in self._latest_versions:
            assert self._latest_versions[part_name] < version
            self._latest_versions[part_name] = version

        return table
