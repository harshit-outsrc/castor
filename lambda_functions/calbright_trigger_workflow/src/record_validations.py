from propus.calbright_sql.calbright import Calbright
from propus.logging_utility import Logging
from propus.security.validation import security_validation


class RecordValidations:
    def __init__(self, psql_engine: Calbright):
        self.logger = Logging.get_logger(
            "castor/lambda_functions/calbright_trigger_workflow/src/process_security_validation"
        )
        self.psql_engine = psql_engine

    def validate_application(self, student_application: Calbright.CCCApplication):
        """validation of ccc_application by checking fraud status, asn and domain

        Args:
            student_applicant (obj): model obj of student application
        """

        if self.check_fraud_status(student_application.fraud_status):
            student_application.blocked_application = True
            self.logger.info(
                f" - Marked as Fraud from CCCApply for ccc_application.id: {student_application.id}."
                " Blocked Application until further review."
            )

        try:
            validation_list = security_validation(
                self.psql_engine.session, student_application.email, student_application.ip_address
            )

            for validation in validation_list:
                if hasattr(validation, "flag") and validation.flag:
                    student_application.blocked_application = True
                    self.logger.info(
                        f" - Security Flag for ccc_application.id: {student_application.id} failed security validation."
                        " Blocked Application until further review."
                    )
        except Exception as err:
            self.logger.error(f" - Error during validate_application: {err}")
            raise err

    def check_fraud_status(key, value):
        fraud_status_options = {
            None: "Not Evaluated",
            0: False,  # "Not Evaluated",
            1: False,  # "Not Checked",
            2: False,  # "Pending",
            3: True,  # "Checked Fraud",
            4: False,  # "Checked NOT Fraud",
            5: True,  # "Confirmed Fraud",
            6: False,  # "Confirmed NOT Fraud"
        }

        return fraud_status_options[value]
