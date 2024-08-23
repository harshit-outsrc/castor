from services.base_client import fetch_ssm


class HubspotClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            from propus.hubspot import Hubspot

            cls._client = Hubspot.build(fetch_ssm(ssm, param_name))
        return cls._client

    def send_transactional_email(self, **kwargs):
        self._client.send_transactional_email(**kwargs)
