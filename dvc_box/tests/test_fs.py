from typing import ClassVar

import pytest

# If your plugin defines a custom error, import it:
# from dvc_box.errors import BoxAuthError
#
# Or, if you raise a generic ConfigError or BoxAPIException, import whichever is appropriate:
from dvc_objects.fs.errors import ConfigError

# Import your plugin's FileSystem class (the equivalent of GDriveFileSystem).
# For example:
# from dvc_box import BoxDVCFileSystem

# Example JSON that simulates invalid credentials for Box
INVALID_BOX_CREDS_JSON = '{"invalid": true}'

# Example empty/invalid JSON to trigger a missing key error
EMPTY_CREDS_JSON = "{}"


class TestRemoteBox:
    CONFIG: ClassVar[dict[str, str]] = {
        "url": "box://0/data",
        "box_credentials_file": "fake_box_config.json",  # or similar
    }

    def test_init(self):
        """
        Check that our Box-based filesystem initializes with the given URL.
        """
        # fs = BoxDVCFileSystem(**self.CONFIG)
        # assert fs.url == self.CONFIG["url"]

        # Since we don't know your exact class name, here's a placeholder:
        fs = FakeBoxFileSystem(**self.CONFIG)  # Replace with your actual class
        assert fs.url == self.CONFIG["url"]

    def test_box_auth_errors(self, monkeypatch):
        """
        Simulate auth failures by setting environment-based credentials
        and ensuring our filesystem raises an error.
        """
        # Suppose your plugin reads from BOX_CREDENTIALS_DATA for token JSON
        env_var_name = "BOX_CREDENTIALS_DATA"

        # 1) Set env var to an invalid JSON that triggers an auth error
        monkeypatch.setenv(env_var_name, INVALID_BOX_CREDS_JSON)
        fs = FakeBoxFileSystem(**self.CONFIG)  # Replace with your actual class
        with pytest.raises(ConfigError):  # or BoxAuthError, if you define it
            # Access fs.fs or some property that forces auth logic
            _ = fs.fs

        # 2) Set env var to empty JSON, also triggers an auth error
        monkeypatch.setenv(env_var_name, EMPTY_CREDS_JSON)
        fs = FakeBoxFileSystem(**self.CONFIG)
        with pytest.raises(ConfigError):  # or BoxAuthError
            _ = fs.fs

    def test_service_account_using_env_var(self, monkeypatch):
        """
        If your plugin supports service-account usage via an env var,
        test that path. For example, if 'box_use_service_account' is the key:
        """
        env_var_name = "BOX_CREDENTIALS_DATA"
        monkeypatch.setenv(env_var_name, "some_service_account_token")
        # fs = BoxDVCFileSystem(box_use_service_account=True, **self.CONFIG)
        fs = FakeBoxFileSystem(box_use_service_account=True, **self.CONFIG)
        # If just creating doesn't throw an error, that might be enough,
        # or you can do further checks. E.g.:
        assert fs._settings.get("use_service_account") is True
        # If you require that reading fs.fs works, you could do that as well.
