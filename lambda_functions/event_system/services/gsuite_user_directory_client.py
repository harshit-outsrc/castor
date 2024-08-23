from services.base_client import fetch_ssm


class GoogleSuiteUserDirectoryClient:
    _client = None

    def __new__(cls, param_name, ssm, readonly):
        if not cls._client:
            from propus.gsuite.user_directory import UserDirectory

            param = fetch_ssm(ssm, param_name, True)

            cls._client = UserDirectory.build(param, readonly=readonly)
        return cls._client


class GoogleSuiteUserDirectoryService:
    def __init__(self, param_name, ssm, readonly=True):
        self.client = GoogleSuiteUserDirectoryClient(param_name, ssm, readonly=readonly)

    def suspend_student(self, calbright_email, org_unit_path="/Suspended", suspended=True):
        self.client.update_user_org_unit(calbright_email, org_unit_path, suspended)
