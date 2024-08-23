import unittest
from unittest.mock import MagicMock, Mock

from jobs.symplicity_student_ingestion.mock_data import (
    csm_response_1,
    expected_response_1,
    csm_response_2,
    expected_response_2,
)
from jobs.symplicity_student_ingestion.csm_service import CsmService


class TestCsmService(unittest.TestCase):
    def setUp(self) -> None:
        csm_client = MagicMock()
        csm_client.list_students = Mock(side_effect=self.list_students)
        csm_client.batch_create_students = Mock(side_effect=self.batch_create_students)
        csm_client.batch_update_students = Mock(side_effect=self.batch_update_students)
        self.csm_service = CsmService(csm_client)

        self.batch_called = 0
        self.batch_disable_called = 0

    def test_fetch_csm_students(self):
        resp = self.csm_service.fetch_csm_students()
        self.assertEqual(len(resp), 2)
        self.assertIn("STUDENT_ID", resp)
        for key, value in resp.get("STUDENT_ID").items():
            self.assertEqual(value, expected_response_1.get(key))
        self.assertIn("STUDENT_ID_2", resp)
        for key, value in resp.get("STUDENT_ID_2").items():
            self.assertEqual(value, expected_response_2.get(key))

    def list_students(self, page):
        return csm_response_1 if page == 1 else csm_response_2

    def test_create_new_students(self):
        self.assertIsNone(self.csm_service.create_new_students([]))

        self.csm_service.create_new_students([{"id": i} for i in range(539)])
        self.assertEqual(self.batch_called, 2)

    def batch_create_students(self, batch):
        self.batch_called += 1
        self.assertEqual(len(batch), 500 if self.batch_called == 1 else 39)
        return {"responses": []}

    def batch_update_students(self, batch):
        self.batch_disable_called += 1
        self.assertEqual(len(batch), 500 if self.batch_disable_called == 1 else 20)
        return {"responses": []}


if __name__ == "__main__":
    unittest.main()
