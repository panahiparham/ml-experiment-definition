import argparse
import os
from pathlib import Path
import random

from ml_experiment.experiment_definition import ExperimentDefinition

parser = argparse.ArgumentParser()
parser.add_argument("--part", type=str, required=True)
parser.add_argument("--config-id", type=int, required=True)
parser.add_argument("--seed", type=int, required=True)
parser.add_argument("--version", type=int, required=True)
parser.add_argument("--results-path", type=str, required=True)
parser.add_argument('--silent', action='store_true', default=False, required=False)

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
    base = Path(cmdline.results_path).parents[1]
    exp = ExperimentDefinition("softmaxAC", cmdline.version, experiment='acceptance', base=str(base))
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

    # write the output to a file
    output_path = os.path.join(cmdline.results_path, f"output_{cmdline.config_id}.txt")
    with open(output_path, "w") as f:
        f.write(output)

if __name__ == "__main__":
    main()
