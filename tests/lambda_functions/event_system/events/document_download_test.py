import unittest
from unittest.mock import MagicMock, Mock

from datetime import datetime

from lambda_functions.event_system.events.document_download import DownloadDocumentEvent

from exceptions import MissingRequiredField


class TestEventDocumentDownload(unittest.TestCase):
    def setUp(self):
        salesforce = MagicMock()

        magic_document = Mock()
        magic_document.content = bytes("foo", "utf-8")

        pd = MagicMock()
        pd.download_document = Mock(return_value=magic_document)
        self.form_bucket = "calbright-testing"

        self.document_download_event = DownloadDocumentEvent(
            configs={
                "form_bucket": self.form_bucket,
            },
            salesforce=salesforce,
            pd=pd,
            s3=MagicMock(),
        )

        self.test_data = {
            "document_download_event": {
                "student_id": "123154315",
                "name": "Prof. TestingTon",
                "ccc_id": "TEST123",
                "calbright_email": "test@testington.calbright",
                "program": "IT Support",
                "document_event_type": "CSEP",
                "document_type": "PandaDocs",
                "document_id": "123id me",
                "document_link": "something cool",
            },
            "event_timestamp": str(datetime.now()),
        }

    def test_required_fields(self):
        for field in self.document_download_event._required_fields:
            try:
                # with self.assertRaises(MissingRequiredField):
                self.document_download_event.run(self.test_data)
            except MissingRequiredField as err:
                self.assertEqual(
                    str(err),
                    f'Event type "document_download_event" is missing or size is 0 for the required field: {field}',
                )


if __name__ == "__main__":
    unittest.main()
