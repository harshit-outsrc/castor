import json
import os
import requests
from typing import AnyStr, Dict

from propus.aws.s3 import AWS_S3
from propus.gsuite import Drive
from propus import Logging


class PdfService:
    _static_bucket = "static.calbrightcollege.org"
    _key_prefix = "student_support/pace_progress/"

    def __init__(self, pdf_url, request_service, s3, gdrive):
        self.s3 = s3
        self.request_service = request_service
        self.pdf_url = pdf_url
        self.gdrive = gdrive
        self.logger = Logging.get_logger("services/pdf_service.py")

    @staticmethod
    def build(configs, gdrive_ssm):
        fname = f"{os.getcwd()}/gsuite_token_from_ssm.json"
        with open(fname, "w", encoding="utf-8") as drive_creds:
            drive_creds.write(gdrive_ssm)

        return PdfService(configs.get("pdf_url"), requests, AWS_S3.build(), Drive.build("file", fname))

    def generate_and_upload_pdf(self, ccc_id: AnyStr, args: Dict) -> AnyStr:
        """
        This function issues an API request to trigger Google AppScript to generate a google doc which can then
        be downloaded into PDF Format. Once downloaded that file is then uploaded to S3 (in our static bucket)
        and can be downloaded by our students. Then we delete the google drive file and return the url to the
        file on static.calbrightcollege.org

        Args:
            ccc_id (AnyStr): Student's CCCID
            args (Dict): Dictionary of arguments we use to send as API Query Parameters to Google's AppScript
                which will create the Google Document

        Returns:
            AnyStr: Link to the PDF document which is hosted on S3
        """
        file_name = f"{ccc_id}_{args.get('full_name').replace(' ', '_')}_progress_timeline.pdf"
        args["file_name"] = file_name
        create_document_req = self.request_service.get(url=f"{self.pdf_url}?args={json.dumps(args)}")
        if not create_document_req.ok or "Exception" in create_document_req.text:
            self.logger.error(f"failed creating PDF for {ccc_id}. Error {create_document_req.text}")
            return ""

        pdf_request = self.request_service.get(create_document_req.content)
        self.s3.write_to_s3(
            bucket=self._static_bucket,
            key=f"{self._key_prefix}{file_name}",
            body=pdf_request.content,
        )

        document_id = create_document_req.text.split("/")[5]
        self.gdrive.delete_file(document_id)

        return f"https://{self._static_bucket}/{self._key_prefix}{file_name}"
