import importlib

import pytest

import project_d


def test_version_is_set() -> None:
    assert project_d.__version__


@pytest.mark.parametrize("module", ["agents", "environment", "simulation", "evaluation"])
def test_subpackage_imports(module: str) -> None:
    importlib.import_module(f"project_d.{module}")
