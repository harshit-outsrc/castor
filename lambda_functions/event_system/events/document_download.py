import os
import base64
from events.base import BaseEventSystem
from propus.logging_utility import Logging
from propus.aws.s3 import AWS_S3
from exceptions import UnknownDocumentDownloadEventType


class DownloadDocumentEvent(BaseEventSystem):
    __event_type__ = "document_download_event"

    _required_fields = [
        "document_download_event",
        "event_timestamp",
    ]

    _student_info_fields = []

    def __init__(self, configs, salesforce, pd, s3):
        super().__init__(configs)
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/download_document_event")
        self.salesforce = salesforce
        self.pd = pd
        self.s3 = s3
        self._form_bucket = configs.get("form_bucket")

    @staticmethod
    def build(configs, ssm):
        from services.salesforce_client import SalesforceService
        from services.pandadoc_client import PandaDocClient

        return DownloadDocumentEvent(
            configs=configs,
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
            pd=PandaDocClient(configs.get("pandadoc_ssm"), ssm),
            s3=AWS_S3.build(),
        )

    def download_pandadoc_request(self, event_data):
        doc_data = event_data.get("document_download_event")
        document = self.pd.download_document(doc_data.get("document_id"))
        self.s3.write_to_s3(
            bucket=self._form_bucket,
            key=(
                f"""{doc_data.get("ccc_id")}/forms/CSEP_{doc_data.get("program").replace(" ", "_")}_{event_data.get("event_timestamp")[:10]}.pdf"""  # noqa: E501
            ),
            body=document.content,
        )
        self.salesforce.client.create_attachment(
            extension="application/pdf",
            parent_id=doc_data.get("student_id"),
            file_name=f'{doc_data.get("name")}_{doc_data.get("ccc_id")}.pdf',
            base64_encoded_file=base64.b64encode(document.content).decode("utf-8"),
        )

    @staticmethod
    def check_required_fields(event_type, event, required_fields: set):
        from exceptions import MissingRequiredField

        for field in required_fields:
            if field not in event:
                raise MissingRequiredField(event_type, field)

        document_download_event = [
            "student_id",
            "name",
            "ccc_id",
            "calbright_email",
            "program",
            "document_event_type",
            "document_type",
            "document_id",
            "document_link",
        ]

        for field in document_download_event:
            if field not in event.get("document_download_event", {}):
                raise MissingRequiredField(event_type, field)

    def run(self, event_data):
        self.check_required_fields(self.__event_type__, event_data, self._required_fields)
        if os.environ.get("ENV") not in ("dev", "stage"):
            self.test_channel = None
        if event_data.get("document_download_event").get("document_type") == "PandaDocs":
            self.download_pandadoc_request(event_data)
        else:
            raise UnknownDocumentDownloadEventType(event_data.get("document_type"))
        return
