from datetime import datetime, timezone
from unittest.mock import MagicMock


class MockEnrollment:
    def __init__(self, ccc_id, last_saa, first_saa, first_lms_login):
        self.ccc_id = ccc_id
        self.last_saa = last_saa
        self.first_saa = first_saa
        self.first_lms_login = first_lms_login


def create_mock_psql_services():
    mock_psql_services = MagicMock()

    mock_psql_services.get_student_enrollment.return_value = MockEnrollment(
        ccc_id="12345",
        last_saa=datetime(2021, 5, 1, 12, 0, tzinfo=timezone.utc),
        first_saa=datetime(2021, 1, 1, 12, 0, tzinfo=timezone.utc),
        first_lms_login=datetime(2021, 1, 1, 11, 0, tzinfo=timezone.utc),
    )
    mock_psql_services.update_object.return_value = True
    mock_psql_services.get_assignment_by_canvas_id.return_value = MagicMock()
    mock_psql_services.get_submission_by_submission_id.return_value = MagicMock(attempt=1)
    # mock_psql_services.get_user_info_by_canvas_id.return_value = MagicMock()
    mock_psql_services.get_user_info_by_canvas_id.side_effect = lambda canvas_id, user_type="student": (
        {"ccc_id": "12345", "email": "student@example.com"}
        if user_type == "student"
        else {"staff_id": "67890", "email": "staff@example.com"}
    )
    mock_psql_services.update_ect_progress.return_value = True
    mock_psql_services.update_ect_final_grade.return_value = True
    mock_psql_services.calculate_progress.return_value = 100
    mock_psql_services.update_program_progress.return_value = True
    mock_psql_services.get_course_code_by_lms_id.return_value = "COURSE123"

    return mock_psql_services
