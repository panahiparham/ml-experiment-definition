import os
from itertools import product

from typing import Dict, Iterable, Set
from collections import defaultdict

import ml_experiment._utils.sqlite as sqlu
from ml_experiment.metadata.MetadataTableRegistry import MetadataTableRegistry

ValueType = int | float | str | bool

class DefinitionPart:
    def __init__(self, name: str, base: str | None = None):
        self.name = name
        self.base_path = base or os.getcwd()

        self._properties: Dict[str, Set[ValueType]] = defaultdict(set)
        self._prior_values: Dict[str, ValueType] = {}

    def add_property(
        self,
        key: str,
        value: ValueType,
        assume_prior_value: ValueType | None = None,
    ):
        self._properties[key].add(value)

        if assume_prior_value is not None:
            self._prior_values[key] = assume_prior_value

    def add_sweepable_property(
        self,
        key: str,
        values: Iterable[ValueType],
        assume_prior_value: ValueType | None = None,
    ):
        self._properties[key] |= set(values)

        if assume_prior_value is not None:
            self._prior_values[key] = assume_prior_value

    def get_results_path(self) -> str:
        import __main__
        experiment_name = __main__.__file__.split('/')[-2]
        return os.path.join(self.base_path, 'results', experiment_name)

    def commit(self):
        configurations = list(generate_configurations(self._properties))

        save_path = self.get_results_path()
        db_path = os.path.join(save_path, 'metadata.db')
        con = sqlu.init_db(db_path)
        cur = con.cursor()

        table_registry = MetadataTableRegistry()

        # tag configurations with the appropriate configuration id
        # grabbing from prior tables where possible, or generating a unique id for new configs
        next_config_id = table_registry.get_max_configuration_id(cur, self.name) + 1
        for configuration in configurations:
            config_query = self._get_configuration_without_priors(configuration)
            existing_id = table_registry.get_configuration_id(cur, self.name, config_query)

            if existing_id is not None:
                configuration['id'] = existing_id

            else:
                configuration['id'] = next_config_id
                next_config_id += 1


        # determine whether we should build a new table
        # and what version to call that table
        latest_table = table_registry.get_latest_version(cur, self.name)

        next_table_version = 0
        skip_build = False
        if latest_table is not None:
            next_table_version = latest_table.version + 1

            # check if the current latest table contains exactly the same configs
            expected_config_ids = set(c['id'] for c in configurations)
            current_config_ids = latest_table.get_configuration_ids(cur)

            skip_build = expected_config_ids == current_config_ids

        if not skip_build:
            table = table_registry.create_new_table(cur, self.name, next_table_version, self._properties.keys())
            table.add_configurations(cur, configurations)

        con.commit()
        con.close()

    def _get_configuration_without_priors(self, configuration: Dict[str, ValueType]):
        """
        When a new property is introduced that has an assumed prior value,
        then we need to search for configuration ids without the new
        property and associated those with the new config.

        This function gives back the configuration to search for to
        obtain an id.
        """
        out = {}
        for k, v in configuration.items():
            if k in self._prior_values and v == self._prior_values[k]:
                continue

            out[k] = v

        return out


def generate_configurations(properties: Dict[str, Set[ValueType]]):
    for configuration in product(*properties.values()):
        yield dict(zip(properties.keys(), configuration, strict=True))
