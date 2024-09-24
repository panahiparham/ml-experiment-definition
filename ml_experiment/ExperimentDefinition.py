from typing import Any
import os
import sqlite3

from ml_experiment.metadata.MetadataTable import MetadataTable

class ExperimentDefinition:
    def __init__(self, part_name: str, version: int, base: str | None = None):
        self.part_name = part_name
        self.version = version
        self.base_path = base or os.getcwd()

        self.table = MetadataTable(self.part_name, self.version)

    def get_config(self, config_id: int) -> dict[str, Any]:
        save_path = self.get_results_path()
        db_path = os.path.join(save_path, 'metadata.db')

        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            return self.table.get_configuration(cur, config_id)



    def get_configs(self, config_ids: list[int], product_seeds: list[int] | None = None) -> list[dict[str, Any]]:
        save_path = self.get_results_path()
        db_path = os.path.join(save_path, 'metadata.db')

        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            _c = [
                self.table.get_configuration(cur, config_id)
                for config_id in config_ids
            ]

            if product_seeds is not None:
                return [
                    {**c, 'seed': seed}
                    for c in _c
                    for seed in product_seeds
                ]
            else:
                return _c


    def get_results_path(self) -> str:
        import __main__
        experiment_name = __main__.__file__.split('/')[-2]
        return os.path.join(self.base_path, 'results', experiment_name)
