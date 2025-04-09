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

To run the API, change directory to the app folder, set your secret key env var, optionally make the docs accessible and start:

```
cd app
SECRET_KEY="your-very-secret-key" SHOW_DOCS=1 python main.py
```

## New Release
To create a new release:

1. Tag: `git tag v0.0.0`
2. Push: `git push --tags` to trigger build CI/CD
3. Create release on GH
