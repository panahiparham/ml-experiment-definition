import os

def get_experiment_name():
    import __main__
    return __main__.__file__.split('/')[-2]

def get_results_path(base_path: str) -> str:
    return os.path.join(
        base_path,
        'results',
        get_experiment_name(),
    )
