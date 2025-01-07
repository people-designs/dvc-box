import logging
import os
import threading
from typing import ClassVar

from funcy import wrap_prop

from dvc.utils.objects import cached_property
from dvc_objects.fs.base import FileSystem
from dvc_objects.fs.errors import ConfigError

logger = logging.getLogger(__name__)


class BoxFileSystem(FileSystem):  # pylint:disable=abstract-method
    """
    Thin wrapper around boxfs.BoxFileSystem for use as a DVC remote.
    """

    protocol = "box"
    PARAM_CHECKSUM = "checksum"
    # DVC uses REQUIRES to check for required PyPI dependencies.
    # Key is the import name, Value is the package name to install.
    REQUIRES: ClassVar[dict[str, str]] = {"boxfs": "boxfs"}

    # Since Box requests can be slower for large folder traversals,
    # you can tune this if needed. The default is 1.
    TRAVERSE_WEIGHT_MULTIPLIER = 1

    def __init__(self, **config):
        """
        Args:
            config (dict):
                DVC config dictionary. Typically includes:
                  - url: Remote URL, like "box://some-folder" or "box://0/path..."
                  - box_credentials_file: Path to a JWT or OAuth config JSON file
                  - other optional config keys...
        """
        from fsspec.utils import infer_storage_options

        super().__init__(**config)

        # DVC requires that we have a "url" key, which might look like "box://0/mydata"
        if "url" not in config:
            raise ConfigError("Box remote config missing 'url'.")

        self.url = config["url"]
        opts = infer_storage_options(self.url)  # scheme="box", host="0", path="/mydata"

        # Combine the host + path to figure out your root folder or path
        # For example, if you had "box://12345/abc", you might store "/abc" as _path
        # and "12345" as a root folder ID if you want to treat it that way.
        self._host = opts.get("host", "")  # e.g. "12345"
        self._path = (opts.get("path") or "").lstrip("/")  # e.g. "abc"

        # If there is no Box folder ID or path, treat it as an error.
        if not self._host and not self._path:
            raise ConfigError(f"Empty Box URL '{self.url}'")

        # Additional config from DVC (optional)
        # e.g. "box_credentials_file" or "box_oauth_type" (JWT vs OAuth2)
        self._credentials_file = config.get("box_credentials_file")
        self._oauth_type = config.get("box_oauth_type", "jwt")  # or "oauth2", etc.

        # We might store everything needed into a single dictionary
        # to pass down to BoxFileSystem. (You can rename or rearrange as you wish.)
        self._settings = {}
        if self._credentials_file:
            self._settings["oauth"] = self._credentials_file
        else:
            # You might allow environment-based config or raise an error
            logger.warning(
                "No 'box_credentials_file' found in config. "
                "BoxFileSystem may fail if it cannot authenticate."
            )

        # root_id or root_path logic:
        # If the user put something like "box://0/some/path", we might treat "0" as root
        # or if it's a custom folder ID, we store it in _settings as "root_id".
        # Then use self._path for the subfolder path inside that root.
        if self._host:  # e.g. "12345"
            # We treat host as a folder ID
            self._settings["root_id"] = self._host
            self._settings["root_path"] = None  # or we can omit
        else:
            # If there's no numeric host, but there's a path, you might do:
            self._settings["root_id"] = None
            self._settings["root_path"] = self._path

        # Done with config parsing

    @classmethod
    def _strip_protocol(cls, path):
        """
        For a path like 'box://12345/myfolder', remove the 'box://' part
        and return '12345/myfolder'.
        """
        from fsspec.utils import infer_storage_options

        opts = infer_storage_options(path)
        # Return host + path without leading slashes
        host = opts.get("host") or ""
        subpath = opts.get("path") or ""
        if subpath.startswith("/"):
            subpath = subpath.lstrip("/")
        return f"{host}/{subpath}".rstrip("/")

    def unstrip_protocol(self, path):
        """
        If we have '12345/myfolder', convert back to 'box://12345/myfolder'.
        """
        return f"{self.protocol}://{path}"

    @staticmethod
    def _get_kwargs_from_urls(urlpath):
        """
        DVC uses this to pass the URL to __init__ as kwargs.
        """
        return {"url": urlpath}

    @wrap_prop(threading.RLock())
    @cached_property
    def fs(self):
        """
        The actual fsspec-based BoxFileSystem instance, lazily created.
        """
        from boxfs import BoxFileSystem

        # We might want to refine how we compute root_id vs root_path based on
        # _host, _path, etc.
        # For example:
        #   self._settings["root_id"] = self._host   (if you interpret that as
        # the folder ID)
        #   self._settings["root_path"] = self._path (the subfolder)
        #
        # (The example in __init__ does this, but you can adjust as needed.)

        return BoxFileSystem(**self._settings)

    def upload_fobj(self, fobj, to_info, **kwargs):
        """
        Called by DVC when pushing a file-like object to the remote.
        We just need to ensure the parent directory exists, then write.
        """
        # Make sure the parent folder exists
        parent_dir = os.path.dirname(to_info)
        self.makedirs(parent_dir, exist_ok=True)

        # The simplest approach is to open the remote file in write-binary mode and copy
        # the data from the file object we were given:
        with self.fs.open(to_info, "wb") as out_stream:
            out_stream.write(fobj.read())

    def makedirs(self, path, exist_ok=False):
        """
        Proxy to the underlying boxfs makedirs, if it exists.
        """
        return self.fs.makedirs(path, exist_ok=exist_ok)
