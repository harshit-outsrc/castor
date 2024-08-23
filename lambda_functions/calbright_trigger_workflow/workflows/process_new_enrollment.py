import asyncio
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import AnyStr

from propus.calbright_sql.calbright import Calbright
from propus.anthology import Anthology
from propus.logging_utility import Logging

from configuration.constants import CITIZEN_STATUS_CCCAPPLY_TO_SIS
from src.trigger_process_helpers import format_grade_level


class NewEnrollment:
    def __init__(self, configs, psql_engine: Calbright, anthology: Anthology):
        self.configs = configs
        self.logger = Logging.get_logger(
            "castor/lambda_functions/calbright_trigger_workflow/workflows/process_new_enrollment"
        )
        self.psql_engine = psql_engine
        self.anthology = anthology
        self.student_record = Calbright.Student
        self.user_record = Calbright.User
        self.enrollment_record = Calbright.Enrollment
        self.ccc_application = Calbright.CCCApplication
        self.new_enrollment = True

    @staticmethod
    def build(configs, ssm):
        from configuration.config import setup_anthology, setup_postgres_engine

        return NewEnrollment(
            configs=configs,
            psql_engine=setup_postgres_engine(configs.get("psql_ssm"), ssm),
            anthology=setup_anthology(configs.get("anthology_ssm"), ssm),
        )

    def process(self, record_id: AnyStr, trigger_op: AnyStr):
        """ingestion process for new student enrollment that need to be processed and inserted into SIS (Anthology).

        Args:
            record_id (AnyStr): record id that needs to be ingested
            trigger_op (AnyStr): operation that fired trigger

        Raises:
            err: Log and raise error if new enrollments workflow failed
        """
        try:
            if trigger_op == "INSERT":
                self.get_enrollment_based_on_id(record_id)
                self.create_sis_student()
                self.create_sis_enrollment()

        except Exception as err:
            self.logger.error(f"Error during new_enrollment inserted: {err}")
            self.psql_engine.session.rollback()
            raise err

    def get_enrollment_based_on_id(self, record_id):
        """Gets the information of the record that triggered the workflow so it can be checked against and create new
            SIS (Anthology) records.

        Args:
            record_id (str): record id that triggered workflow to grab all the information needed
        """
        self.enrollment_record = self.psql_engine.session.query(Calbright.Enrollment).filter_by(id=record_id).first()
        self.student_record = self.enrollment_record.student
        self.user_record = self.student_record.user

        self.ccc_application = (
            self.psql_engine.session.query(Calbright.CCCApplication)
            .filter_by(ccc_id=self.enrollment_record.ccc_id)
            .first()
        )

        return

    def get_required_data(self, enrollment):
        """Gathers required data for an enrollment record to be created in Anthology

        Args:
            enrollment (Dict): Enrollment information required for Anthology create enrollment calls

        Raises:
            err: Error raised if there are problems during gathering data for enrollment
        """
        try:
            enrollment["student_id"] = self.user_record.anthology_id
            enrollment["program_id"] = self.enrollment_record.program_version.program.anthology_program_id
            enrollment["program_version_id"] = (
                self.enrollment_record.program_version.program.anthology_program_version_id
            )

            enrollment["grade_level_id"] = format_grade_level(self.ccc_application.highest_edu_level[0])
            enrollment["start_date"] = self.enrollment_record.first_term.start_date
            enrollment["grad_date"] = self.enrollment_record.enrollment_date + relativedelta(months=12)

            catalog_year_list = asyncio.run(
                self.anthology.fetch_configurations(
                    "catalog_year", **{"program_version_id": enrollment.get("program_version_id")}
                )
            )
            for year in catalog_year_list.get("value"):
                endDate = datetime.strptime(year.get("EffectiveEndDate").split("T")[0], "%Y-%m-%d")
                startDate = datetime.strptime(year.get("EffectiveStartDate").split("T")[0], "%Y-%m-%d")
                if endDate > self.enrollment_record.enrollment_date >= startDate:
                    catalog_year = year
                    break

            enrollment["catalog_year_id"] = catalog_year.get("Id")
            version_start_year_list = asyncio.run(
                self.anthology.fetch_configurations(
                    "start_date", **{"program_version_id": enrollment.get("program_version_id")}
                )
            )

            for version_date in version_start_year_list.get("value"):
                start_date = datetime.strptime(version_date.get("StartDate").split("T")[0], "%Y-%m-%d")
                if start_date.date() == self.enrollment_record.first_term.start_date:
                    version_start_date = version_date.get("Id")
                    break

            enrollment["version_start_date"] = version_start_date
            enrollment["application_received_date"] = datetime.strftime(
                self.ccc_application.tstmp_submit, "%Y/%m/%d %H:%M:%S"
            )
            enrollment["enrollment_date"] = datetime.strftime(
                self.enrollment_record.enrollment_date, "%Y/%m/%d %H:%M:%S"
            )

        except Exception as err:
            self.logger.error(f"Error during gathering data: {err}")
            raise err

        return

    def create_sis_student(self):
        """Creates a student in Anthology based on an enrollment record existing in the PSQL database

        Raises:
            err: Error raised if there are problems during creation of student in SIS (Anthology)
        """
        student = {
            "first_name": self.user_record.first_name,
            "last_name": self.user_record.last_name,
            "student_number": self.student_record.ccc_id,
            "phone_number": "({}) {}-{}".format(
                self.user_record.phone_number[0:3],
                self.user_record.phone_number[3:6],
                self.user_record.phone_number[6:],
            ),  # Has to be (NNN) NNN-NNNN or Anthology throws an error
            "dob": datetime.strftime(
                self.student_record.date_of_birth, "%Y/%m/%d"
            ),  # Has to be YYYY/MM/DD or Anthology throws an error
            "email": self.user_record.calbright_email,
        }

        try:
            if self.user_record.anthology_id:
                response = asyncio.run(self.anthology.student_by_id(self.user_record.anthology_id))
            else:
                self.setup_sis_student_payload(student)
                response = asyncio.run(self.anthology.create_student(**student))
                self.logger.info(
                    f"Student created successfully: {self.anthology.base_url}/#/students/{response.get('id')}"  # noqa: E501
                )
                self.user_record.anthology_id = response.get("id")
                self.psql_engine.session.commit()

        except Exception as err:
            self.logger.error(f"Error during creation of student in Anthology: {err}")
            raise err

        return

    def setup_sis_student_payload(self, student: dict = {}):
        student["citizenId"] = (CITIZEN_STATUS_CCCAPPLY_TO_SIS.get(self.ccc_application.citizenship_status),)
        student["genderId"] = self.user_record.gender.anthology_id if self.user_record.gender else None
        student["maidenName"] = self.user_record.maiden_name
        student["middleName"] = self.user_record.middle_name
        student["preferredName"] = f"{self.user_record.preferred_first_name} {self.user_record.preferred_last_name}"
        student["ssn"] = self.student_record.ssn
        student["suffixId"] = self.user_record.suffix.anthology_id if self.user_record.suffix else None
        student["veteran"] = self.ccc_application.background_military_veteran

        if self.student_record.student_ethnicity:
            student["ethnicitiesList"] = [
                student_ethnicity.ethnicity.anthology_id for student_ethnicity in self.student_record.student_ethnicity
            ]

        if self.user_record.pronoun:
            student["genderPronounList"] = [self.user_record.pronoun.anthology_id]

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
            student["postalCode"] = current_address.address.zip
            student["state"] = current_address.address.state
            student["streetAddress"] = current_address.address.address1
            student["streetAddress2"] = current_address.address.address2 if current_address.address.address2 else ""

    def create_sis_enrollment(self):
        """Creates enrollment in the SIS (Anthology) based on gathered data from PSQL database

        Raises:
            err: Error raised if there are problems during creation of enrollment and courses in SIS (Anthology)
        """
        enrollment = {
            "student_id": "",
            "program_id": "",
            "program_version_id": "",
            "grade_level_id": "",
            "start_date": "",
            "grad_date": "",
            "catalog_year_id": "",
            "version_start_date": "",
            "application_received_date": "",
            "enrollment_date": "",
        }

        self.get_required_data(enrollment)
        try:
            if not self.enrollment_record.sis_enrollment_id:
                sis_enrollment = asyncio.run(self.anthology.create_enrollment(**enrollment))
                self.enrollment_record.sis_enrollment_id = sis_enrollment.get("id")
                self.psql_engine.session.commit()

        except Exception as err:
            self.logger.error(f"Error during creation of enrollment in Anthology: {err}")
            raise err

        return
