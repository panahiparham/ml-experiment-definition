from ml_experiment import DefinitionPart as dp


def init_esarsa_mc(tmp_path, alphas: list[float], epsilons: list[float], n_steps: list[int]):

    esarsa = dp.DefinitionPart("esarsa-mc", base=str(tmp_path))
    esarsa.add_sweepable_property("alpha", alphas)
    esarsa.add_sweepable_property("epsilon", epsilons)
    esarsa.add_sweepable_property("n_step", n_steps)
    esarsa.add_property("tiles", 4)
    esarsa.add_property("tilings", 16)
    esarsa.add_property("total_steps", 100000)
    esarsa.add_property("episode_cutoff", 5000)
    esarsa.commit()

    return esarsa


def test_generate_configurations(tmp_path):
    """
    Tests that the dp.generate_configurations function returns the same configurations as the ones written by the dp.DefinitionPart.commit function.

    Note: configs do not have ID numbers
    """

    # expected outputs
    alphas = [0.5, 0.25, 0.125]
    epsilons = [0.1, 0.05, 0.15]
    n_steps = [2, 3]
    expected_configs = (
        {
            "alpha": a,
            "epsilon": e,
            "n_step": n,
            "tiles": 4,
            "tilings": 16,
            "total_steps": 100000,
            "episode_cutoff": 5000,
        }
        for a in alphas
        for e in epsilons
        for n in n_steps
    )

    # write experiment definition to table
    esarsa_mc = init_esarsa_mc(tmp_path, alphas, epsilons, n_steps)

    # get all the hyperparameter configurations
    configs = dp.generate_configurations(esarsa_mc._properties)

    for config, expected_config in zip(configs, expected_configs, strict=True):
        assert config == expected_config
