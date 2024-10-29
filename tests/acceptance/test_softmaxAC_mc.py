import os
import subprocess

from ml_experiment.ExperimentDefinition import ExperimentDefinition
from ml_experiment.DefinitionPart import DefinitionPart
from ml_experiment.Scheduler import LocalRunConfig, RunSpec, Scheduler


def write_database(results_path, alphas: list[float], taus: list[float]):
    # make table writer
    softmaxAC = DefinitionPart("softmaxAC")

    # overwrite the results path to be in the temp directory
    softmaxAC.get_results_path = lambda *args, **kwargs: results_path

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


# overwrite the run_single function
class StubScheduler(Scheduler):

    # allows us to force the results path to be in a specific spot
    def __init__(self, results_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results_path = results_path

    # adding the results path to the command
    def _run_single(self: Scheduler, r: RunSpec) -> None:
        subprocess.run(['python', self.entry, '--part', r.part_name, '--config-id', str(r.config_id), '--seed', str(r.seed), '--version', str(r.version), '--results_path', self.results_path])


def test_read_database(tmp_path):
    """
    Test that we can retrieve the configurations from the experiment definition.
    """

    # expected outputs
    results_path = os.path.join(tmp_path, "results", "temp")
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
    write_database(results_path, alphas, taus)

    # make Experiment object (versions start at 0)
    softmaxAC_mc = ExperimentDefinition(
        part_name="softmaxAC", version=0
    )

    # overwrite the results path to be in the temp directory
    softmaxAC_mc.get_results_path = lambda *args, **kwargs: results_path

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

    # write experiment definition to table
    results_path = os.path.join(tmp_path, "results", "temp")
    db = write_database(results_path, alphas, taus)

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

    # set up experiment file
    experiment_file_name = "tests/acceptance/my_experiment.py"

    # set up scheduler
    sched = StubScheduler(
        exp_name="temp",
        entry=experiment_file_name,
        seeds=[seed_num],
        version=version_num,
        results_path=results_path,
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




