from services.base_client import fetch_ssm
from propus.tangoe.tangoe import TangoeMobile
from propus.tangoe.people import TangoePeople


class TangoeMobileClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            cls._client = TangoeMobile.build(fetch_ssm(ssm, param_name, is_json=True))
        return cls._client


class TangoePeopleClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            cls._client = TangoePeople.build(fetch_ssm(ssm, param_name, is_json=True))
            cls._client.generate_token()
        return cls._client
