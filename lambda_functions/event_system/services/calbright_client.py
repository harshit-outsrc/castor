import os
from services.base_client import fetch_ssm
from propus.calbright_sql.calbright import Calbright


class CalbrightClient:
    _client = None
    _dev_db_keys = ["DB", "USER", "PASSWORD", "HOST"]

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            if os.environ.get("ENV") == "dev" and all([os.environ.get(k) for k in cls._dev_db_keys]):
                cls._client = Calbright.build({k.lower(): os.environ.get(k) for k in cls._dev_db_keys}, verbose=True)
            else:
                cls._client = Calbright.build(fetch_ssm(ssm, param_name, is_json=True))
        return cls._client
