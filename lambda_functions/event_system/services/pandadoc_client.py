from services.base_client import fetch_ssm


class PandaDocClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            from propus.panda_doc import PandaDoc

            cls._client = PandaDoc.build(fetch_ssm(ssm, param_name))
        return cls._client
