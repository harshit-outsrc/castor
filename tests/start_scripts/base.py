import unittest
from pprint import pformat

from propus import Logging


class BaseTestClass:
    def __init__(self, test_name):
        self.logger = Logging.get_logger(f"base_test_class/{test_name}", debug=True)

    def run(self):
        results = unittest.TestResult()
        loaded_tests = map(lambda test: unittest.TestLoader().loadTestsFromTestCase(test), self.tests)

        unittest.TestSuite(loaded_tests).run(results)

        was_successful = results.wasSuccessful()
        tests_run = results.testsRun
        failures = results.failures
        errors = results.errors

        for error in results.errors:
            self.logger.error(error)

        if was_successful:
            self.logger.info(f"Success running {tests_run} tests")
        else:
            self.logger.error(f"Failure {len(failures)}/{tests_run} tests failed")
            for failure in failures:
                self.describe_failure(failure)

        if len(failures) or len(errors):
            raise Exception("Tests Failed")

    def describe_failure(self, test):
        if len(test) == 2 and hasattr(test[0], "_testMethodName"):
            test = "Failed Test: {}".format(test[0]._testMethodName)
        self.logger.error(pformat(test))
