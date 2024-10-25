from ml_experiment.DefinitionPart import DefinitionPart
from ml_experiment.ExperimentDefinition import ExperimentDefinition


def test_ExperimentDefinition(tmp_path):
    # build dummy experiment
    exp_name = "dummy_experiment"
    part_name = "qrc"

    part = DefinitionPart(exp_name, part_name, base=str(tmp_path))
    part.add_sweepable_property("alpha", (2**-i for i in range(3, 8)))
    part.add_sweepable_property("beta", [0.5, 1.0, 2.0])
    part.commit()

    # load experiment definition
    version = 0
    config_ids = [1, 2, 3]
    seeds = [1, 2]

    exp = ExperimentDefinition(exp_name, part_name, version, base=str(tmp_path))

    config = exp.get_config(0)
    assert config == {"alpha": 0.125, "beta": 0.5, "id": 0}

    configs = exp.get_configs(config_ids)
    assert configs == [
        {"alpha": 0.125, "beta": 1.0, "id": 1},
        {"alpha": 0.125, "beta": 2.0, "id": 2},
        {"alpha": 0.0625, "beta": 0.5, "id": 3},
    ]

    configs_and_seeds = exp.get_configs(config_ids, product_seeds=seeds)
    assert configs_and_seeds == [
        {"alpha": 0.125, "beta": 1.0, "id": 1, "seed": 1},
        {"alpha": 0.125, "beta": 1.0, "id": 1, "seed": 2},
        {"alpha": 0.125, "beta": 2.0, "id": 2, "seed": 1},
        {"alpha": 0.125, "beta": 2.0, "id": 2, "seed": 2},
        {"alpha": 0.0625, "beta": 0.5, "id": 3, "seed": 1},
        {"alpha": 0.0625, "beta": 0.5, "id": 3, "seed": 2},
    ]
