import os

import pytest


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(os.path.dirname(__file__), "docker-compose.yml")


@pytest.fixture
def make_box():
    def _make_box():
        raise NotImplementedError

    return _make_box


@pytest.fixture
def box(make_box):
    return make_box()
