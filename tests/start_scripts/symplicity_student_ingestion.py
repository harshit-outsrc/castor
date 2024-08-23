import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append("/".join(current_path.split("/")[:-2] + "jobs/symplicity_student_ingestion".split("/")))
from tests.jobs.symplicity_student_ingestion.salesforce_service_test import TestSalesforceService
from tests.jobs.symplicity_student_ingestion.csm_service_test import TestCsmService

from tests.start_scripts.base import BaseTestClass


class SymplicityStudentIngestion(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [TestSalesforceService, TestCsmService]


if __name__ == "__main__":
    SymplicityStudentIngestion("symplicity_student_ingestion").run()
