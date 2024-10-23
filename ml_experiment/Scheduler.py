from __future__ import annotations

import sys
import os
sys.path.append(os.getcwd())

import sqlite3
from typing import Self, Callable, NamedTuple
from dataclasses import dataclass
from itertools import product
from multiprocessing.pool import Pool
import subprocess
from ml_experiment.metadata.MetadataTableRegistry import MetadataTableRegistry

class RunSpec(NamedTuple):
    part_name: str
    version: int
    config_id: int
    seed: int


@dataclass
class RunConfig:
    ...


@dataclass
class LocalRunConfig(RunConfig):
    tasks_in_parallel: int

    log_path: str = ".logs/"



Pred = Callable[[str, int, int, int], bool]
VersionSpec = int | dict[str, int | None] | None

class Scheduler:
    def __init__(self, exp_name: str, seeds: list[int], entry: str, version: VersionSpec = None, base: str | None = None):
        self.exp_name = exp_name
        self.seeds = seeds
        self.entry = entry
        self.base_path = base or os.getcwd()
        self.version = version if version is not None else -1

        self.all_runs = set[RunSpec]() # TODO: polars dataframe!

        self._sanity_check()

    def __repr__(self):
        return f'Scheduler({self.exp_name}, {self.seeds}, {self.version}, {self.all_runs})'

    def get_all_runs(self) -> Self:
        res_path = os.path.join(self.base_path, 'results', self.exp_name, 'metadata.db')

        meta = MetadataTableRegistry()

        with sqlite3.connect(res_path) as con:
            cur = con.cursor()
            parts = meta.get_parts(cur)
            resloved_ver = self._resolve_version(parts, cur, meta)

            for k, v in resloved_ver.items():
                t = meta.get_table(cur, k, v)
                assert t is not None
                config_ids = t.get_configuration_ids(cur)
                self.all_runs |= {RunSpec(k, v, c, s) for c, s in product(config_ids, self.seeds)}

        return self


    def filter(self, already_exists: Pred) -> Scheduler:
        filtered = Scheduler(self.exp_name, self.seeds, self.entry, self.version, self.base_path)

        for r in self.all_runs:
            if not already_exists(*r):
                filtered.all_runs.add(r)

        return filtered


    def run(self, c: RunConfig) -> None:
        type(c)
        if isinstance(c, LocalRunConfig):
            self._run_local(c)
        else:
            raise ValueError('Unknown RunConfig type')


    # ----------------------
    # -- Internal Methods --
    # ----------------------

    def _run_local(self, c: LocalRunConfig) -> None:
        pool = Pool(c.tasks_in_parallel)
        pool.map(self._run_single, self.all_runs)


    def _run_single(self, r: RunSpec) -> None:
        subprocess.run(['python', self.entry, '--part', r.part_name, '--config-id', str(r.config_id), '--seed', str(r.seed), '--version', str(r.version)])


    def _resolve_version(
        self,
        parts: set[str],
        cur: sqlite3.Cursor,
        meta: MetadataTableRegistry,
    ) -> dict[str, int]:
        if isinstance(self.version, int):
            _r = {p: self.version for p in parts}
        elif isinstance(self.version, dict):
            _r = {}
            for p in parts:
                v = self.version.get(p, -1)
                _r[p] = v if v is not None else -1
        else:
            _r = {p: -1 for p in parts}

        for k, v in _r.items():
            if v == -1:
                table = meta.get_latest_version(cur, k)
                assert table is not None
                _r[k] = table.version

        return _r

    def _sanity_check(self):
        res_path = os.path.join(self.base_path, 'results', self.exp_name, 'metadata.db')
        assert os.path.exists(res_path), f'{self.exp_name} does not exist'


