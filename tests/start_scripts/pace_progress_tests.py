import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append("/".join(current_path.split("/")[:-2] + "jobs/pace_progress_automation".split("/")))
from tests.jobs.pace_progress_automation.pace_pipeline_test import TestPacePipeline
from tests.jobs.pace_progress_automation.services.email_service_test import TestEmailService
from tests.jobs.pace_progress_automation.services.pdf_service_test import TestPdfService
from tests.jobs.pace_progress_automation.services.salesforce_service_test import TestSalesforceService

from tests.start_scripts.base import BaseTestClass


class PaceProgressTests(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [
            TestEmailService,
            TestPacePipeline,
            TestPdfService,
            TestSalesforceService,
        ]


if __name__ == "__main__":
    PaceProgressTests("pace_progress_tests").run()
