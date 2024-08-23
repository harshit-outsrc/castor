from services.base_client import fetch_ssm


class GoogleSuiteLicensingClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if not cls._client:
            from propus.gsuite import Licensing

            cls._client = Licensing.build(fetch_ssm(ssm, param_name, True))
        return cls._client


class GoogleSuiteLicensingService:
    def __init__(self, param_name, ssm):
        self.client = GoogleSuiteLicensingClient(param_name, ssm)

    def delete_license(self, calbright_email):
        license = self.client.get_license(calbright_email)
        if license:
            self.client.delete_license(calbright_email)
