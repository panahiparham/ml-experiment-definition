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
