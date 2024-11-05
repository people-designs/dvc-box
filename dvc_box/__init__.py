import json
import logging
import threading
from typing import ClassVar

from funcy import wrap_prop

from dvc.utils.objects import cached_property
from dvc_objects.fs.base import FileSystem
from dvc_objects.fs.errors import ConfigError
from boxsdk import Client, user
from boxsdk.auth.oauth2 import OAuth2
from boxsdk.auth.jwt_auth import JWTAuth
from boxsdk.object.user import User
from boxsdk.session.session import Session

logger = logging.getLogger(__name__)

class BoxFileSystem(FileSystem):  # pylint:disable=abstract-method
    protocol = "box"
    PARAM_CHECKSUM = "checksum"
    REQUIRES: ClassVar[dict[str, str]] = {"boxfs": "boxfs"}
    # Always prefer traverse for GDrive since API usage quotas are a concern.
    TRAVERSE_WEIGHT_MULTIPLIER = 1

    def __init__(self, **config):
        from fsspec.utils import infer_storage_options

        super().__init__(**config)

        self.url = config["url"]
        opts = infer_storage_options(self.url)

        if not opts["host"]:
            raise ConfigError("Empty Box root_id '{}'.".format(config["url"]))

        self._path = opts["host"] + opts["path"]

        config_file_path = config.get('config_file_path', '')
        user_id = config.get('user_id', '')


        auth = JWTAuth.from_settings_file(settings_file_sys_path=config_file_path)
        client = Client(oauth=auth)
        access_token = auth.authenticate_user(user=user_id)

        auth = JWTAuth.from_settings_file(settings_file_sys_path=config_file_path, access_token=access_token)
        client = Client(oauth=auth, )

        self._settings = {
            "client": client,
            "root_id": '290432082372',
        }

    @classmethod
    def _strip_protocol(cls, path):
        return '/'

    def unstrip_protocol(self, path):
        return f"box://{path}"

    @staticmethod
    def _get_kwargs_from_urls(urlpath):
        return {"url": urlpath}

    @wrap_prop(threading.RLock())
    @cached_property
    def fs(self):
        from boxfs import BoxFileSystem as _BoxFileSystem
        fs = _BoxFileSystem(**self._settings)
        return fs
