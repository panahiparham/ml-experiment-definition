# don't use this venv please, it's just for testing purposes
python -m venv .temp_venv_89232740428678165126
source .temp_venv_89232740428678165126/bin/activate
pip install uv
uv pip compile --extra=dev pyproject.toml -o requirements.txt
uv pip sync requirements.txt

pytest --cov=ml_experiment

rm -rf .temp_venv_89232740428678165126