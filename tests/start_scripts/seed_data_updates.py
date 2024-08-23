import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append("/".join(current_path.split("/")[:-2] + "lambda_functions/seed_data_updates".split("/")))
from tests.lambda_functions.seed_data_updates.coci_file_upload import TestCOCIUpload
from tests.lambda_functions.seed_data_updates.staff_data_upload import TestStaffDataUpload

from tests.start_scripts.base import BaseTestClass


class SeedDataUpdates(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [TestCOCIUpload, TestStaffDataUpload]


if __name__ == "__main__":
    SeedDataUpdates("seed_data_updates").run()
