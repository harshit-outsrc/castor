from services.base_client import fetch_ssm


class GoogleDriveClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            from propus.gsuite import Drive

            param = fetch_ssm(ssm, param_name)
            fname = "/tmp/gsuite_token_from_ssm.json"
            f = open(fname, "w")
            f.write(param)
            f.close()

            cls._client = Drive.build("file", fname)
        return cls._client
