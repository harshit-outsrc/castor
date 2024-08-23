from services.base_client import fetch_ssm
from propus.calendly import Calendly


class CalendlyClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            cls._client = Calendly.build(fetch_ssm(ssm, param_name))
        return cls._client
