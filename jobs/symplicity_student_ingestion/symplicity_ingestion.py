from propus.aws.ssm import AWS_SSM
from propus.symplicity.csm import CSM
from propus import Logging
from propus.salesforce import Salesforce

from csm_service import CsmService
from salesforce_service import SalesforceService


class SymplicityIngestion:
    def __init__(self, sforce_service, csm_service):
        self.sforce_service = sforce_service
        self.csm_service = csm_service

        self.logger = Logging.get_logger("symplicity_ingestion.py")

    @staticmethod
    def build(env):
        ssm = AWS_SSM.build()
        csm = CSM.build(ssm.get_param(parameter_name="symplicity.csm"))
        return SymplicityIngestion(
            sforce_service=SalesforceService.build(Salesforce.build_v2("prod" if env == "prod" else "stage", ssm), csm),
            csm_service=CsmService(csm),
        )

    def run(self):
        csm_students = self.csm_service.fetch_csm_students()
        salesforce_students = self.sforce_service.fetch_csm_eligible_students()

        csm_students = self.csm_service.update_merged_students(csm_students, salesforce_students)

        # Create New Students
        students_to_create = set(salesforce_students.keys()) - set(csm_students.keys())
        self.csm_service.create_new_students([salesforce_students.get(ccc_id) for ccc_id in students_to_create])

        # Disable students that are not longer in the matching statuses
        active_students_to_disable = set()
        students_to_disable = set(csm_students.keys()) - set(salesforce_students.keys())
        for ccc_id in students_to_disable:
            if csm_students.get(ccc_id).get("accountBlocked") != 1 and not csm_students.get(ccc_id).get(
                "accountDisabled"
            ):
                active_students_to_disable.add(ccc_id)

        self.logger.info(f"Disabling {len(active_students_to_disable)} students")

        # Update any students who've had their data changed and newly disabled students
        salesforce_students |= self.sforce_service.fetch_csm_eligible_students(
            ccc_ids=active_students_to_disable, disabled=True
        )

        students_to_update = set(salesforce_students.keys()).intersection(set(csm_students.keys()))
        total_updates = students_to_update | active_students_to_disable
        self.csm_service.update_students(
            salesforce_students={
                ccc_id: salesforce_students.get(ccc_id) for ccc_id in total_updates if salesforce_students.get(ccc_id)
            },
            csm_students={ccc_id: csm_students.get(ccc_id) for ccc_id in total_updates if csm_students.get(ccc_id)},
        )
