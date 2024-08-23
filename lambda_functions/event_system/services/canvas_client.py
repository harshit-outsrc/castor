from propus.canvas import Canvas
from services.base_client import fetch_ssm


class CanvasClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            # creds = ssm.get_param("canvas.dev.token", param_type="json")
            creds = fetch_ssm(ssm, param_name, True)
            cls._client = Canvas(
                base_url=creds["base_url"], application_key=creds["token"], auth_providers=creds["auth_providers"]
            )

        return cls._client
