from services.base_client import fetch_ssm


class GoogleSheetsClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            from propus.gsuite import Sheets

            param = fetch_ssm(ssm, param_name, True)

            cls._client = Sheets.build(param)
        return cls._client


class GoogleSheetsService:
    def __init__(self, param_name, ssm, sheets_key_table):
        self.client = GoogleSheetsClient(param_name, ssm)
        self.sheets_key_table = sheets_key_table

    def adjust_ou_to_enrolled_student(self, time, first_name, last_name, email, status, message):
        self.client.append_row(
            self.sheets_key_table.get("adjust_ou_to_enrolled_student"),
            [time, first_name, last_name, email, status, message],
        )

    def enqueue_student_deprovision(self, time, email, sf_url, strut_id):
        self.client.append_row(
            self.sheets_key_table.get("enqueue_student_deprovision"), [time, email, sf_url, strut_id]
        )

    def enqueue_student_to_strut(
        self, username, first_name, last_name, email, role, coach_id, state, strut_id, intended_program
    ):
        self.client.append_row(
            self.sheets_key_table.get("enqueue_student_to_strut"),
            [username, first_name, last_name, email, role, coach_id, state, strut_id, intended_program],
        )

    def append_new_learner_device_request(
        self,
        timestamp,
        cccid,
        email,
        first_name,
        last_name,
        phone,
        shipping_address,
        include_chromebook,
        include_hotspot,
        policy_signed,
        sheet_tab=0
    ):
        self.client.append_row(
            self.sheets_key_table.get("loaner_device_management"),
            [
                timestamp,
                cccid,
                email,
                first_name,
                last_name,
                phone,
                shipping_address,
                include_chromebook,
                include_hotspot,
                policy_signed,
            ],
            sheet_tab=sheet_tab,
        )
