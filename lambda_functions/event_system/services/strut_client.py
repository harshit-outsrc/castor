from services.base_client import fetch_ssm


class StrutClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            from propus.strut import Strut

            cls._client = Strut.build(**fetch_ssm(ssm, param_name, is_json=True))
        return cls._client


class StrutService:
    def __init__(self, param_name, ssm):
        self.client = StrutClient(param_name, ssm)

    def lock_student_enrollments(self, student_id):
        enrollments = self.client.fetch_enrollments(student_id=student_id)
        for e in enrollments:
            enrollment_id = e.get("id")
            self.client.update_enrollment(student_id, enrollment_id, state="locked")

    def withdraw_student(self, student_id):
        self.client.assign_student_state(student_id, "withdrawn")
