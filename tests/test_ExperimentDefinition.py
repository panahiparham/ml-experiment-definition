import os

from ml_experiment.definition_part import DefinitionPart
from ml_experiment.experiment_definition import ExperimentDefinition


def test_ExperimentDefinition(tmp_path):

    # build dummy experiment
    exp_name = 'dummy_experiment'
    part_name = 'qrc'

    part = stubbed_DefinitionPart(exp_name, part_name, base = str(tmp_path))
    part.add_sweepable_property('alpha', (2**-i for i in range(3, 8)))
    part.add_sweepable_property('beta', [0.5, 1.0, 2.0])
    part.commit()


    # load experiment definition
    version = 0
    config_ids = [1, 2, 3]
    seeds = [1, 2]

    exp = stubbed_ExperimentDefinition(exp_name, part_name, version, base = str(tmp_path))

    config = exp.get_config(0)
    assert config == {'alpha': 0.125, 'beta': 0.5, 'id': 0}

    configs = exp.get_configs(config_ids)
    assert configs == [
        {'alpha': 0.125, 'beta': 1.0, 'id': 1},
        {'alpha': 0.125, 'beta': 2.0, 'id': 2},
        {'alpha': 0.0625, 'beta': 0.5, 'id': 3},
    ]


    configs_and_seeds = exp.get_configs(config_ids, product_seeds=seeds)
    assert configs_and_seeds == [
        {'alpha': 0.125, 'beta': 1.0, 'id': 1, 'seed': 1},
        {'alpha': 0.125, 'beta': 1.0, 'id': 1, 'seed': 2},
        {'alpha': 0.125, 'beta': 2.0, 'id': 2, 'seed': 1},
        {'alpha': 0.125, 'beta': 2.0, 'id': 2, 'seed': 2},
        {'alpha': 0.0625, 'beta': 0.5, 'id': 3, 'seed': 1},
        {'alpha': 0.0625, 'beta': 0.5, 'id': 3, 'seed': 2},
    ]


class stubbed_DefinitionPart(DefinitionPart):
    def __init__(self, exp_name: str, name: str, base: str | None = None):
        self.exp_name = exp_name
        super().__init__(name, base)

    def get_results_path(self, base_path) -> str:
        return os.path.join(base_path, 'results', self.exp_name)

class stubbed_ExperimentDefinition(ExperimentDefinition):
    def __init__(self, exp_name: str, part_name: str, version: int, base: str | None = None):
        self.exp_name = exp_name
        super().__init__(part_name, version, base)

    def get_results_path(self, base_path) -> str:
        return os.path.join(base_path, 'results', self.exp_name)
