import os
import pytest

from ml_experiment.definition_part import DefinitionPart
from ml_experiment.experiment_definition import ExperimentDefinition
from ml_experiment.scheduler import LocalRunConfig, Scheduler


@pytest.fixture
def base_path(request):
    """Overwrite the __main__.__file__ to be the path to the current file. This allows _utils.get_experiment_name to look at ./tests/acceptance/this_file.py rather than ./.venv/bin/pytest."""
    import __main__
    __main__.__file__ = request.path.__fspath__()

def write_database(tmp_path, alphas: list[float], taus: list[float]):
    # make table writer
    softmaxAC = DefinitionPart("softmaxAC", base=str(tmp_path))

    # add properties to sweep
    softmaxAC.add_sweepable_property("alpha", alphas)
    softmaxAC.add_sweepable_property("tau", taus)

    # add properties that are static
    softmaxAC.add_property("n_step", 1)
    softmaxAC.add_property("tiles", 4)
    softmaxAC.add_property("tilings", 16)
    softmaxAC.add_property("total_steps", 100000)
    softmaxAC.add_property("episode_cutoff", 5000)
    softmaxAC.add_property("seed", 10)

    # write the properties to the database
    softmaxAC.commit()

    return softmaxAC

def test_read_database(tmp_path, base_path):
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
            "seed": 10,
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
    write_database(tmp_path, alphas, taus)

    # make Experiment object (versions start at 0)
    softmaxAC_mc = ExperimentDefinition(
        part_name="softmaxAC", version=0, base=str(tmp_path)
    )

    # get the configuration ids
    num_configs = len(alphas) * len(taus)
    config_ids = list(range(num_configs))

    for cid, expected_config in zip(config_ids, expected_configs, strict=True):
        config = softmaxAC_mc.get_config(cid)
        assert config == expected_config


def test_run_tasks(tmp_path):
    """Make sure that the scheduler runs all the tasks, and that they return the correct results."""
    # setup
    alphas = [0.05, 0.01]
    taus = [10.0, 20.0, 5.0]
    seed_num = 10
    version_num = 0
    exp_name = "acceptance"

    # expected outputs
    partial_configs = (
        {
            "alpha": a,
            "tau": t,
            "n_step": 1,
            "tiles": 4,
            "tilings": 16,
            "total_steps": 100000,
            "episode_cutoff": 5000,
            "seed": 10,
        }
        for a in alphas
        for t in taus
    )
    expected_configs = {i : config for i, config in enumerate(partial_configs)}

    # set experiment file name
    experiment_file_name = f"tests/{exp_name}/my_experiment.py"

    # set results path
    results_path = os.path.join(tmp_path, "results", f"{exp_name}")

    # write experiment definition to table
    db = write_database(tmp_path, alphas, taus)

    assert db.name == "softmaxAC"
    assert os.path.exists(os.path.join(results_path, "metadata.db"))

    # get number of tasks to run in parallel
    try:
        import multiprocessing

        ntasks = multiprocessing.cpu_count() - 1
    except (ImportError, NotImplementedError):
        ntasks = 1

    # initialize run config
    run_conf = LocalRunConfig(tasks_in_parallel=ntasks, log_path=".logs/")

    # set up scheduler
    sched = Scheduler(
        exp_name=exp_name,
        entry=experiment_file_name,
        seeds=[seed_num],
        version=version_num,
        base = str(tmp_path),
    )

    # run all the tasks
    sched = sched.get_all_runs()
    sched.run(run_conf)

    # make sure there are the correct amount of runs
    assert len(sched.all_runs) == len(expected_configs.keys())

    # check that the output files were created
    for runspec in sched.all_runs:

        # sanity check: make sure the runspec uses the hardcoded part, version, and seed
        assert runspec.part_name == "softmaxAC"
        assert runspec.version == version_num
        assert runspec.seed == seed_num

        # get the expected output
        expected_config = expected_configs[runspec.config_id]
        expected_output = f"SoftmaxAC({expected_config['alpha']}, {expected_config['tau']}, {expected_config['n_step']}, {expected_config['tiles']}, {expected_config['tilings']})"

        # check that the output file was created
        output_path = os.path.join(results_path, f"output_{runspec.config_id}.txt")
        with open(output_path, "r") as f:
            output = f.read()
            assert output.strip() == expected_output




