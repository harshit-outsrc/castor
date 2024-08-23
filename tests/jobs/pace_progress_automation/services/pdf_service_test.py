import unittest
from unittest.mock import MagicMock, Mock

from jobs.pace_progress_automation.services.pdf_service import PdfService


class TestPdfService(unittest.TestCase):
    def setUp(self) -> None:
        requests = MagicMock()
        requests.get = Mock(side_effect=self.request_get)

        s3 = MagicMock()
        s3.write_to_s3 = Mock(side_effect=self.s3_write_to_s3)

        gdrive = MagicMock()
        gdrive.delete_file = Mock(side_effect=self.delete_file)
        self.pdf_url = "https://mock_pdf.com/asda/asdasd"
        self.pdf_service = PdfService(self.pdf_url, requests, s3, gdrive)
        self.test_name = None

        self.ccc_id = "ABC98765"
        self.doc_id = "AJNSAASJKA^&*!@^*&1234"
        self.test_args = {"full_name": "jane_doe", "test_data": "testing1234"}

    def request_get(self, url):
        if self.test_name == "create_doc_success":
            self.assertEqual(url, "https://create_document.com")
        else:
            self.assertEqual(
                url,
                'https://mock_pdf.com/asda/asdasd?args={"full_name": "jane_doe", "test_data": "testing1234", "file_name": "ABC98765_jane_doe_progress_timeline.pdf"}',  # noqa: E501
            )
        response = MagicMock()
        if self.test_name == "doc_creation_failure":
            response.ok = False
            response.text = "This is the error message"
        elif self.test_name == "success_run":
            response.ok = True
            response.content = "https://create_document.com"
            response.text = f"http://abc.com/a/b/{self.doc_id}"
            self.test_name = "create_doc_success"
        elif self.test_name == "create_doc_success":
            response.content = "This is the PDF Response Content"
        return response

    def s3_write_to_s3(self, bucket, key, body):
        self.assertEqual(bucket, self.pdf_service._static_bucket)
        self.assertEqual(key, "student_support/pace_progress/ABC98765_jane_doe_progress_timeline.pdf")
        self.assertEqual(body, "This is the PDF Response Content")

    def delete_file(self, doc_id):
        self.assertEqual(doc_id, self.doc_id)

    def test_doc_creation_failure(self):
        self.test_name = "doc_creation_failure"
        self.assertEqual(self.pdf_service.generate_and_upload_pdf(self.ccc_id, self.test_args), "")

    def test_doc_creation_success(self):
        self.test_name = "success_run"
        self.assertEqual(
            self.pdf_service.generate_and_upload_pdf(self.ccc_id, self.test_args),
            "https://static.calbrightcollege.org/student_support/pace_progress/ABC98765_jane_doe_progress_timeline.pdf",  # noqa: E501
        )


if __name__ == "__main__":
    unittest.main()
