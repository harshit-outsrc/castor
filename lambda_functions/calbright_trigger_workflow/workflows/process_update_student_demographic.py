import asyncio
from typing import AnyStr

from propus.calbright_sql.calbright import Calbright
from propus.anthology import Anthology
from propus.logging_utility import Logging


class UpdateStudentDemographic:
    def __init__(self, configs, psql_engine: Calbright, anthology: Anthology):
        self.configs = configs
        self.logger = Logging.get_logger(
            "castor/lambda_functions/calbright_trigger_workflow/workflows/process_update_student_demographic"
        )
        self.psql_engine = psql_engine
        self.anthology = anthology
        self.student_record = Calbright.Student
        self.user_record = Calbright.User
        self.ccc_application = Calbright.CCCApplication

    @staticmethod
    def build(configs, ssm):
        from configuration.config import setup_anthology, setup_postgres_engine

        return UpdateStudentDemographic(
            configs=configs,
            psql_engine=setup_postgres_engine(configs.get("psql_ssm"), ssm),
            anthology=setup_anthology(configs.get("anthology_ssm"), ssm),
        )

    def process(self, record_id: AnyStr, trigger_op: AnyStr):
        """ingestion process for updating student records into SIS (Anthology).

        Args:
            record_id (AnyStr): record id that needs to be ingested
            trigger_op (AnyStr): operation that fired trigger

        Raises:
            err: Log and raise error if student demographics workflow failed
        """
        try:
            if trigger_op == "UPDATE":
                self.get_student_data(record_id)
                self.update_sis_student()

        except Exception as err:
            self.logger.error(f"Error during update_student_demographic inserted: {err}")
            raise err

    def get_student_data(self, record_id):

        try:
            self.user_record = self.psql_engine.session.query(Calbright.User).filter_by(id=record_id).first()
            self.student_record = self.user_record.student

            self.ccc_application = (
                self.psql_engine.session.query(Calbright.CCCApplication)
                .filter_by(ccc_id=self.user_record.ccc_id)
                .first()
            )

        except Exception as err:
            self.logger.error(f"Error during gathering data: {err}")
            raise err

        return

    def create_student_payload(self):
        """Generates payload for student demographic update on the Anthology profile

        Returns:
            dict: Student payload object for Anthology updates.
        """

        student = {
            "first_name": self.user_record.first_name,
            "genderId": self.user_record.gender.anthology_id if self.user_record.gender else None,
            "last_name": self.user_record.last_name,
            "maidenName": self.user_record.maiden_name,
            "middle_name": self.user_record.middle_name,
            "phone_number": (
                "({}) {}-{}".format(
                    self.user_record.phone_number[0:3],
                    self.user_record.phone_number[3:6],
                    self.user_record.phone_number[6:],
                )
                if self.user_record.phone_number
                else None
            ),  # Has to be (NNN) NNN-NNNN or Anthology throws an error,
            "preferredName": f"{self.user_record.preferred_first_name} {self.user_record.preferred_last_name}",
            "ssn": self.student_record.ssn,
            "suffixId": self.user_record.suffix.anthology_id if self.user_record.suffix else None,
        }

        if self.user_record.pronoun:
            student["genderPronounList"] = [self.user_record.pronoun.anthology_id]

        if self.student_record.student_ethnicity:
            student["ethnicitiesList"] = [
                student_ethnicity.ethnicity.anthology_id for student_ethnicity in self.student_record.student_ethnicity
            ]

        current_address = next(
            (
                student_address
                for student_address in self.student_record.student_address
                if student_address.current is True
            ),
            None,
        )

        if current_address:
            student["city"] = current_address.address.city
            student["postal_code"] = current_address.address.zip
            student["state"] = current_address.address.state
            student["street_address"] = current_address.address.address1
            student["streetAddress2"] = current_address.address.address2 if current_address.address.address2 else ""

        return student

    def update_sis_student(self):
        """Updates Student Demographics on profile in the SIS (Anthology) based on gathered data from PSQL database

        Raises:
            Exception: Exception raised if anthology id doesn't exist on triggering user record
            err: Exception raised if anthology could not update student information
        """
        try:
            student_payload = self.create_student_payload()

            if self.user_record.anthology_id:
                response = asyncio.run(self.anthology.update_student(self.user_record.anthology_id, **student_payload))
                self.logger.info(
                    f"Student updated successfully: {self.anthology.base_url}/#/students/{response.get('id')}"  # noqa: E501
                )
            else:
                raise Exception(
                    f"Error updating student, anthology id doesn't exist for user_record: {self.user_record.id}"
                )

        except Exception as err:
            self.logger.error(f"Error during updating of student in Anthology: {err}")
            raise err

        return
