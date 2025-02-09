from pathlib import Path
from sqlite3 import Cursor
import click

from ml_experiment._utils.maybe import Maybe
from ml_experiment.expdata.tag_table import TagTable
from ml_experiment.metadata.metadata_table_registry import MetadataTableRegistry

import ml_experiment._utils.sqlite as sqlu


@click.group()
def main():
    ...

@main.group('tag')
def tag():
    ...

@tag.command('add')
@click.argument('tag')
@click.argument('experiment')
@click.argument('part_name')
@click.argument('version', type=int, required=False)
def add_tag(tag: str, experiment: str, part_name: str, version: int | None):
    path = Path('results') / experiment / 'metadata.db'

    if not path.exists():
        raise Exception(f'Experiment {experiment} does not exist')

    cur = sqlu.init_db(path).cursor()
    v = Maybe(version) \
        .flat_otherwise(lambda: _get_latest_version(cur, part_name)) \
        .expect('Did not find a version for given part name')

    tag_table = TagTable(cur)
    tag_table.add_tag(tag, part_name, v)


def _get_latest_version(cur: Cursor, part_name: str):
    registry = MetadataTableRegistry()
    table = registry.get_latest_version(cur, part_name)
    return Maybe(table).map(lambda t: t.version)
