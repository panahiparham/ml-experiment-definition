from ml_experiment.ExperimentDefinition import ExperimentDefinition
from ml_experiment.DefinitionPart import DefinitionPart


def init_softmaxAC_mc(tmp_path, alphas: list[float], taus: list[float]):
    softmaxAC = DefinitionPart("softmaxAC-mc", base=str(tmp_path))
    softmaxAC.add_sweepable_property("alpha", alphas)
    softmaxAC.add_sweepable_property("tau", taus)
    softmaxAC.add_property("n_step", 1)
    softmaxAC.add_property("tiles", 4)
    softmaxAC.add_property("tilings", 16)
    softmaxAC.add_property("total_steps", 100000)
    softmaxAC.add_property("episode_cutoff", 5000)
    softmaxAC.commit()


def test_read_configs(tmp_path):
    """
    Test that we can retrieve the configurations from the experiment definition.
    """

    # expected outputs
    alphas = [0.05, 0.01]
    taus = [10.0, 20.0, 5.0]
    partial_configs = (
        {
            "alpha": a,
            "tau": t,
            "n_step": 1,
            "tiles": 4,
            "tilings": 16,
            "total_steps": 100000,
            "episode_cutoff": 5000,
        }
        for a in alphas
        for t in taus
    )
    expected_configs = (
        {
            **config,
            "id": i,
        }
        for i, config in enumerate(partial_configs)
    )

    # write experiment definition to table
    init_softmaxAC_mc(tmp_path, alphas, taus)

    # make Experiment object (versions start at 0)
    softmaxAC_mc = ExperimentDefinition(part_name="softmaxAC-mc", version=0, base=str(tmp_path))

    # TODO: This can't be the intended way to get the configurations?
    num_configs = len(alphas) * len(taus)
    config_ids = list(range(num_configs))

    for cid, expected_config in zip(config_ids, expected_configs, strict=True):
        config = softmaxAC_mc.get_config(cid)
        assert config == expected_config
