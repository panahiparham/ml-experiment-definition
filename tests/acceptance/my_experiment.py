import argparse
import random

from ml_experiment.ExperimentDefinition import ExperimentDefinition

parser = argparse.ArgumentParser()
parser.add_argument("--part", type=str, required=True)
parser.add_argument("--config-id", type=int, required=True)
parser.add_argument("--seed", type=int, required=True)
parser.add_argument("--version", type=int, required=True)

# this is an extra argument for testing
# we need to be able to find the metadata database
# TODO: remove this
parser.add_argument("--results_path", type=str, required=True)

class SoftmaxAC:
    def __init__(
        self,
        alpha: float,
        tau: float,
        nstep: float,
        tiles: int,
        tilings: int,
    ) -> None:
        self.alpha = alpha
        self.tau = tau
        self.nstep = nstep
        self.tiles = tiles
        self.tilings = tilings
        self.name = "SoftmaxAC"

    def run(self) -> str:
        return f"{self.name}({self.alpha}, {self.tau}, {self.nstep}, {self.tiles}, {self.tilings})"


def main():
    cmdline = parser.parse_args()

    # make sure we are using softmaxAC
    if cmdline.part != "softmaxAC":
        raise ValueError(f"Unknown part: {cmdline.part}")

    # do some rng control
    random.seed(cmdline.seed)

    # extract configs from the database
    exp = ExperimentDefinition("softmaxAC", cmdline.version)
    # TODO: don't overwrite this
    exp.get_results_path = lambda *args, **kwargs: cmdline.results_path # overwrite results path
    config = exp.get_config(cmdline.config_id)

    # make our dummy agent
    alpha = config["alpha"]
    tau = config["tau"]
    n_step = config["n_step"]
    tiles = config["tiles"]
    tilings = config["tilings"]
    agent = SoftmaxAC(alpha, tau, n_step, tiles, tilings)

    # run the agent
    output = agent.run()

    # test output
    assert output == f"SoftmaxAC({alpha}, {tau}, {n_step}, {tiles}, {tilings})"

if __name__ == "__main__":
    main()
