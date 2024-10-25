import os
import subprocess

from ml_experiment.ExperimentDefinition import ExperimentDefinition
from ml_experiment.DefinitionPart import DefinitionPart
from ml_experiment.Scheduler import LocalRunConfig, RunSpec, Scheduler


def write_database(results_path, alphas: list[float], taus: list[float]):
    # make table writer
    softmaxAC = DefinitionPart("softmaxAC")
    # TODO: don't overwrite this
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


## TODO: remove this and use the actual scheduler
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
    # TODO: don't overwrite this
    softmaxAC_mc.get_results_path = lambda *args, **kwargs: results_path

    # TODO: This can't be the intended way to get the configurations?
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
        seeds=[10],
        version=0,
        results_path=results_path,
        base = str(tmp_path),
    )

    # run all the tasks
    (
        sched
        .get_all_runs()
        .run(run_conf)
    )
