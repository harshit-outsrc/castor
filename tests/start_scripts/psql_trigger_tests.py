import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(
    "/".join(
        os.path.dirname(os.path.realpath(__file__)).split("/")[:-2] + "lambda_functions/psql_trigger_handler".split("/")
    )
)
from tests.lambda_functions.psql_trigger_handler.trigger_handler_system_test import TestTriggerHandlerSystem

from tests.start_scripts.base import BaseTestClass


class PsqlTriggerTests(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [TestTriggerHandlerSystem]


if __name__ == "__main__":
    PsqlTriggerTests("psql_trigger_tests").run()
