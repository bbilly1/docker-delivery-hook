"""config for pytest"""

import os

import pytest

os.environ.setdefault("SECRET_KEY", "1111111111111111")


@pytest.fixture(scope="session", autouse=True)
def change_test_dir(request):
    """change directory to project folder"""
    os.chdir(request.config.rootdir / "app")
