from typing import AnyStr
from services.base_client import fetch_ssm


class WPWebhookClient:
    _client = None

    def __new__(
        cls,
        param_name,
        ssm,
        base_url: AnyStr = "https://beta.calbrightcollege.org/",
        wh_name: AnyStr = "beta-student-portal",
    ):
        if cls._client is None:
            from propus.wp_webhooks import WPWebhook

            param = fetch_ssm(ssm, param_name)

            cls._client = WPWebhook.build(param, base_url, wh_name)
        return cls._client
