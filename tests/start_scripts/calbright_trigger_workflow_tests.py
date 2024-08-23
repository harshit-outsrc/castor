import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append("/".join(current_path.split("/")[:-2] + "lambda_functions/calbright_trigger_workflow".split("/")))
from tests.lambda_functions.calbright_trigger_workflow.workflow_system_test import TestWorkflowSystem
from tests.lambda_functions.calbright_trigger_workflow.workflows.process_new_ccc_applications_test import (
    TestNewCCCApplications,
)
from tests.lambda_functions.calbright_trigger_workflow.workflows.process_new_enrollment_test import (
    TestNewEnrollment,
)
from tests.lambda_functions.calbright_trigger_workflow.workflows.process_new_certificates_test import (
    TestNewCertificates,
)
from tests.lambda_functions.calbright_trigger_workflow.workflows.process_update_create_grades_test import (
    TestUpdateCreateGrades,
)
from tests.lambda_functions.calbright_trigger_workflow.workflows.process_update_student_demographics_test import (
    TestUpdateStudentDemographic,
)

from tests.start_scripts.base import BaseTestClass


class CalbrightTriggerWorkflow(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [
            TestWorkflowSystem,
            TestNewCCCApplications,
            TestNewEnrollment,
            TestNewCertificates,
            TestUpdateCreateGrades,
            TestUpdateStudentDemographic,
        ]


if __name__ == "__main__":
    CalbrightTriggerWorkflow("calbright_trigger_workflow").run()
