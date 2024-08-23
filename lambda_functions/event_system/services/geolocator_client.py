from services.base_client import fetch_ssm


class GeolocatorClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            from propus.geolocator import Geolocator

            config = fetch_ssm(ssm, param_name, True)
            cls._client = Geolocator.build(config=config)
        return cls._client
