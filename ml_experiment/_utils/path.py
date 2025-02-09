import os

def get_experiment_name():
    import __main__
    return __main__.__file__.split(os.path.sep)[-2]

def get_results_path(base_path: str, experiment: str | None = None) -> str:
    exp = experiment or get_experiment_name()
    return os.path.join(
        base_path,
        'results',
        exp,
    )
