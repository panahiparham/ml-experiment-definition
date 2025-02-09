from sqlite3 import Cursor

import ml_experiment._utils.sqlite as sqlu

class TagTable:
    def __init__(self, cur: Cursor):
        self._cur = cur

        tables = sqlu.get_tables(self._cur)
        if '__tags__' not in tables:
            self._make_table()

    def _make_table(self):
        cur = self._cur
        sqlu.create_table(
            cur,
            '__tags__',
            ['tag', 'part', 'version'],
        )

    def _insert(self, tag: str, part: str, version: int):
        self._cur.execute(
            "INSERT INTO '__tags__' (tag, part, version) VALUES (?, ?, ?)",
            (tag, part, version),
        )
        self._cur.connection.commit()
        return self._cur

    def _update_or_insert(self, tag: str, part: str, version: int):
        self._cur.execute(
            "INSERT OR REPLACE INTO '__tags__'"
                "(tag, part, version) VALUES (:tag, :part, :version)",
            {'tag': tag, 'part': part, 'version': version},
        )
        self._cur.connection.commit()
        return self._cur

    def add_tag(self, tag: str, part_name: str, version: int):
        self._update_or_insert(tag, part_name, version)

    def get_table(self, tag: str) -> tuple[str, int] | None:
        cur = self._cur
        table = cur.execute(
            "SELECT part, version FROM '__tags__' WHERE tag=?",
            (tag,),
        ).fetchone()

        if table is None:
            return table

        return table[0][0], int(table[0][1])
