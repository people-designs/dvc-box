import pytest

from dvc.testing.api_tests import (  # noqa: F401
    TestAPI,
)
from dvc.testing.remote_tests import (  # noqa: F401
    TestRemote,
)

# from dvc.testing.workspace_tests import TestGetUrl as _TestGetUrl
# from dvc.testing.workspace_tests import TestImport as _TestImport
# from dvc.testing.workspace_tests import TestLsUrl as _TestLsUrl


@pytest.fixture
def cloud(make_cloud):
    # Use typ="box" to invoke your Box cloud class instead of GDrive
    return make_cloud(typ="box")


@pytest.fixture
def remote(make_remote):
    # Same here, “box” remote
    return make_remote(name="upstream", typ="box")


@pytest.fixture
def workspace(make_workspace):
    # Same here, “box” workspace
    return make_workspace(name="workspace", typ="box")


# @pytest.mark.xfail
# class TestImport(_TestImport):
#     """
#     Once you've implemented/verified that imports work for Box,
#     remove the @pytest.mark.xfail to see if it passes.
#     """


# @pytest.mark.xfail
# class TestLsUrl(_TestLsUrl):
#     pass


# @pytest.mark.xfail
# class TestGetUrl(_TestGetUrl):
#     pass
