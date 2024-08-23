import unittest
from unittest.mock import MagicMock, patch, call

from propus.calbright_sql.program import Program
from propus.calbright_sql.course import Course

from lambda_functions.seed_data_updates.tasks.coci_file_upload import coci_program_upload, coci_course_upload


class TestCOCIUpload(unittest.TestCase):
    def setUp(self):
        self.s3_client = MagicMock()
        self.mock_s3 = MagicMock()
        self.mock_s3.s3_client = self.s3_client
        self.mock_stage_session = MagicMock()
        self.mock_prod_session = MagicMock()

    @patch("lambda_functions.seed_data_updates.tasks.coci_file_upload.update_or_create")
    @patch("lambda_functions.seed_data_updates.tasks.coci_file_upload.read_s3_csv")
    def test_coci_program_upload(self, mock_read_s3_csv, mock_update_or_create):
        # Arrange
        mock_key = "path/to/csv"
        mock_data = [
            {
                "TITLE": "Program 1",
                "CONTROL NUMBER": "123",
                "TOP CODE": "456",
                "CIP CODE": "789",
                "APPROVED DATE": "2023-01-01",
            },
            {
                "TITLE": "Program 2",
                "CONTROL NUMBER": "456",
                "TOP CODE": "789",
                "CIP CODE": "012",
                "APPROVED DATE": "2023-02-01",
            },
        ]
        expected_data = [
            {
                "program_name": "Program 1",
                "control_number": "123",
                "top_code": "456",
                "cip_code": "789",
                "approved_date": "2023-01-01",
            },
            {
                "program_name": "Program 2",
                "control_number": "456",
                "top_code": "789",
                "cip_code": "012",
                "approved_date": "2023-02-01",
            },
        ]
        mock_read_s3_csv.return_value = mock_data

        # Act
        coci_program_upload(self.mock_s3, mock_key, self.mock_stage_session, self.mock_prod_session)

        # Assert
        mock_read_s3_csv.assert_called_once_with(self.s3_client, mock_key)
        self.mock_stage_session.commit.assert_called_once()
        self.mock_prod_session.commit.assert_called_once()
        expected_calls = [
            call(self.mock_stage_session, Program, expected_data[0], control_number="123"),
            call(self.mock_prod_session, Program, expected_data[0], control_number="123"),
            call(self.mock_stage_session, Program, expected_data[1], control_number="456"),
            call(self.mock_prod_session, Program, expected_data[1], control_number="456"),
        ]
        mock_update_or_create.assert_has_calls(expected_calls)

    @patch("lambda_functions.seed_data_updates.tasks.coci_file_upload.update_or_create")
    @patch("lambda_functions.seed_data_updates.tasks.coci_file_upload.read_s3_csv")
    def test_coci_course_upload(self, mock_read_s3_csv, mock_update_or_create):
        # Arrange
        mock_key = "path/to/csv"
        mock_data = [
            {
                "TITLE (CB02)": "Course 1",
                "STATUS": "Active",
                "COURSE ID": "COURSE-123",
                "CONTROL NUMBER (CB00)": "456",
                "DEPARTMENT NAME (CB01A)": "DEPT",
                "DEPARTMENT NUMBER (CB01B)": "789",
                "COURSE CLASSIFICATION STATUS (CB11)": "Approved",
                "TOP CODE (CB03)": "012",
                "LAST UPDATED BY COLLEGE": "2023-01-01",
                "MINIMUM COURSE CONTACT HOURS": 10,
                "MAXIMUM COURSE CONTACT HOURS": 20,
            },
            {
                "TITLE (CB02)": "Course 2",
                "STATUS": "Inactive",
                "COURSE ID": "COURSE-456",
                "CONTROL NUMBER (CB00)": "789",
                "DEPARTMENT NAME (CB01A)": "DEPT",
                "DEPARTMENT NUMBER (CB01B)": "012",
                "COURSE CLASSIFICATION STATUS (CB11)": "Pending",
                "TOP CODE (CB03)": "345",
                "LAST UPDATED BY COLLEGE": "2023-02-01",
                "MINIMUM COURSE CONTACT HOURS": 15,
                "MAXIMUM COURSE CONTACT HOURS": 25,
            },
        ]
        expected_data = [
            {
                "course_name": "Course 1",
                "status": "Active",
                "course_id": "COURSE-123",
                "control_number": "456",
                "department_name": "DEPT",
                "department_number": "789",
                "course_code": "DEPT789",
                "course_classification_status": "Approved",
                "top_code": "012",
                "last_updated_by_college": "2023-01-01",
                "minimum_course_contact_hours": 10,
                "maximum_course_contact_hours": 20,
            },
            {
                "course_name": "Course 2",
                "status": "Inactive",
                "course_id": "COURSE-456",
                "control_number": "789",
                "department_name": "DEPT",
                "department_number": "012",
                "course_code": "DEPT012",
                "course_classification_status": "Pending",
                "top_code": "345",
                "last_updated_by_college": "2023-02-01",
                "minimum_course_contact_hours": 15,
                "maximum_course_contact_hours": 25,
            },
        ]
        mock_read_s3_csv.return_value = mock_data

        # Act
        coci_course_upload(self.mock_s3, mock_key, self.mock_stage_session, self.mock_prod_session)

        # Assert
        mock_read_s3_csv.assert_called_once_with(self.s3_client, mock_key)
        self.mock_stage_session.commit.assert_called_once()
        self.mock_prod_session.commit.assert_called_once()
        expected_calls = [
            call(self.mock_stage_session, Course, expected_data[0], course_id="COURSE-123"),
            call(self.mock_prod_session, Course, expected_data[0], course_id="COURSE-123"),
            call(self.mock_stage_session, Course, expected_data[1], course_id="COURSE-456"),
            call(self.mock_prod_session, Course, expected_data[1], course_id="COURSE-456"),
        ]
        mock_update_or_create.assert_has_calls(expected_calls)


if __name__ == "__main__":
    unittest.main()
