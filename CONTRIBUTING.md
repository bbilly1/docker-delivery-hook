# Contributing Guideline

## Dev Setup

Setup your environment, e.g. with venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Setup pre-commit:

```bash
pre-commit install
```

And future commits will be automatically linted.

To run the tests, simply run from the root of the repo:

```bash
pytest
```

To run the API, change directory to the app folder, set your secret key env var and start:

```
cd app
SECRET_KEY="your-very-secret-key" python main.py
```
