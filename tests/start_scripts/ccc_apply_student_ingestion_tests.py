import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(
    "/".join(current_path.split("/")[:-2] + "lambda_functions/cccapply_student_application_ingestion/".split("/"))
)
from tests.lambda_functions.cccapply_student_application_ingestion.cccapply_student_application_ingestion_test import (
    TestIngestCCCApplyStudentApplication,
)

from tests.start_scripts.base import BaseTestClass


class CccApplyStudentIngestion(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [TestIngestCCCApplyStudentApplication]


if __name__ == "__main__":
    CccApplyStudentIngestion("ccc_apply_student_ingestion_tests").run()
