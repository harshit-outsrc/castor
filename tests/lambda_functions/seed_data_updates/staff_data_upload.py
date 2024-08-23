import unittest
from unittest.mock import MagicMock, patch, call


from lambda_functions.seed_data_updates.tasks.staff_data_upload import staff_data_upload


class TestStaffDataUpload(unittest.TestCase):

    def setUp(self):
        self.s3_client = MagicMock()
        self.mock_s3 = MagicMock()
        self.mock_s3.s3_client = self.s3_client
        self.mock_stage_session = MagicMock()
        self.mock_prod_session = MagicMock()

    @patch("lambda_functions.seed_data_updates.tasks.staff_data_upload.ingest_staff_data")
    @patch("lambda_functions.seed_data_updates.tasks.staff_data_upload.read_s3_csv")
    def test_staff_data_upload(self, mock_read_s3_csv, ingest_staff_data):
        mock_key = "path/to/csv"
        mock_data = [
            {
                "calbright_email": "staff1@example.com",
                "active_staff": "TRUE",
                "title": "Instructor",
                "primary_instructor": "COURSE-101,COURSE-102",
                "adjunct_instructor": None,
            },
            {
                "calbright_email": "staff2@example.com",
                "active_staff": "FALSE",
                "title": "Counselor",
                "primary_instructor": None,
                "adjunct_instructor": "COURSE-103,COURSE-104",
                "canvas_instructor": "TRUE",
            },
        ]
        mock_read_s3_csv.return_value = mock_data
        staff_data_upload(self.mock_s3, mock_key, self.mock_stage_session, self.mock_prod_session)
        mock_read_s3_csv.assert_called_once_with(self.s3_client, mock_key)
        expected_data = [
            {
                "calbright_email": "staff1@example.com",
                "active_staff": True,
                "title": "Instructor",
                "primary_instructor": ["COURSE-101", "COURSE-102"],
                "adjunct_instructor": None,
                "canvas_instructor": False,
            },
            {
                "calbright_email": "staff2@example.com",
                "active_staff": False,
                "title": "Counselor",
                "primary_instructor": None,
                "adjunct_instructor": ["COURSE-103", "COURSE-104"],
                "canvas_instructor": True,
            },
        ]
        expected_calls = [
            call(expected_data, self.mock_stage_session),
            call(expected_data, self.mock_prod_session),
        ]
        ingest_staff_data.assert_has_calls(expected_calls)


if __name__ == "__main__":
    unittest.main()
