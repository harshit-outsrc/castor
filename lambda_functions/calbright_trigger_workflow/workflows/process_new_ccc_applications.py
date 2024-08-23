from sqlalchemy import or_, and_
from typing import AnyStr

from propus.calbright_sql.calbright import Calbright
from propus.logging_utility import Logging

from src.trigger_process_helpers import filter_check, format_ethnicity, format_gender
from src.record_validations import RecordValidations


class NewCCCApplications:
    def __init__(self, configs, psql_engine: Calbright):
        self.configs = configs
        self.logger = Logging.get_logger(
            "castor/lambda_functions/calbright_trigger_workflow/workflows/process_new_ccc_applications"
        )
        self.psql_engine = psql_engine
        self.new_student = True
        self.user_record = None

    @staticmethod
    def build(configs, ssm):
        from configuration.config import setup_postgres_engine

        return NewCCCApplications(
            configs=configs,
            psql_engine=setup_postgres_engine(configs.get("psql_ssm"), ssm),
        )

    def process(self, record_id: AnyStr, trigger_op: AnyStr):
        """ingestion process for new student applications that need to be processed for security validation and
           deduplication before a new student record can be created.

        Args:
            record_id (AnyStr): record id that needs to be ingested
            trigger_op (AnyStr): operation that fired trigger

        Raises:
            err: Log and raise error if new ccc_applications workflow failed
        """
        try:
            if trigger_op == "INSERT":
                new_ccc_application = self.get_ccc_application_based_on_id(record_id)
                RecordValidations(self.psql_engine).validate_application(new_ccc_application)
                self.check_for_existing_records(new_ccc_application)
                new_ccc_application.processed_application = True

                if self.new_student and not new_ccc_application.blocked_application:
                    student_records = self.create_student_record(new_ccc_application, self.user_record)
                    # Add all newly created records and commit any adjustments to existing records
                    self.psql_engine.add_all(student_records)
                else:
                    # Need to commit updates to ccc_application and existing expressed interest records
                    self.psql_engine.session.commit()
                    self.logger.info(f"Processed, but did not create Student Record for: {new_ccc_application.id}.")

        except Exception as err:
            self.logger.error(f"Error during ingest_new_ccc_applications: {err}")
            self.psql_engine.session.rollback()
            raise err

    def get_ccc_application_based_on_id(self, record_id):
        """Gets the information of the record that triggered the workflow so it can be checked against and create new
           student record with foreign key relationships.

        Args:
            record_id (str): record id that triggered workflow to grab all the information needed
        """
        ccc_application = (
            self.psql_engine.session.query(Calbright.CCCApplication)
            .where(Calbright.CCCApplication.id == record_id)
            .first()
        )
        return ccc_application

    def check_for_existing_records(self, student_application: Calbright.CCCApplication):
        """Checks for existing records and handles the deduplication check processes

        Args:
            student_application (Calbright.CCCApplication): CCCApplication just received that needs to be used for
            checking existing records in PSQL database.
        """
        student_rows = (
            self.psql_engine.session.query(Calbright.Student)
            .where(Calbright.Student.ccc_id.ilike(student_application.ccc_id))
            .all()
        )

        if student_rows:
            self.new_student = False
            self.logger.info(
                f"Duplication Found, {len(student_rows)} Student Records exist for {student_application.ccc_id}"
            )
            return

        user_rows = (
            self.psql_engine.session.query(Calbright.User)
            .where(
                or_(
                    and_(
                        Calbright.User.first_name.ilike(student_application.firstname),
                        Calbright.User.last_name.ilike(student_application.lastname),
                        or_(
                            Calbright.User.student.has(date_of_birth=student_application.birthdate),
                            filter_check(Calbright.User.phone_number, student_application.mainphone),
                        ),
                    ),
                    Calbright.User.personal_email.ilike(student_application.email),
                )
            )
            .all()
        )

        if user_rows:
            if (user["student"] for user in user_rows):
                self.new_student = False
                self.logger.info(
                    f"""Duplication Found, {len(user_rows)} User Records exist with atleast one reference to a
                        Student record for {student_application.ccc_id}"""
                )
                return
            else:
                self.user_record = user_rows[0]
                self.logger.info(
                    f"""Duplication Found, {len(user_rows)} User Records exist without a Student record for
                        {student_application.ccc_id}"""
                )
        else:
            self.user_record = Calbright.User()

    def create_student_record(self, student_applicant: Calbright.CCCApplication, user_record: Calbright.User):
        """applying student application to sqlalchemy models

        Args:
            student_applicant (obj): model obj of student application
        """
        student_records_list = []
        student_record = Calbright.Student()
        preferred_name = (
            str(student_applicant.preferred_firstname).split(" ", 1)
            if student_applicant.preferred_firstname
            else ["", ""]
        )

        # User record information
        user_record.ccc_id = student_applicant.ccc_id
        user_record.first_name = student_applicant.firstname
        user_record.middle_name = student_applicant.middlename
        user_record.last_name = student_applicant.lastname
        user_record.phone_number = student_applicant.mainphone
        user_record.preferred_first_name = preferred_name[0]
        user_record.preferred_last_name = preferred_name[1]
        user_record.personal_email = student_applicant.email

        if student_applicant.suffix:
            user_record.suffix = (
                self.psql_engine.session.query(Calbright.Suffix)
                .where(Calbright.Suffix.suffix == student_applicant.suffix)
                .first()
            )

        user_record.gender = (
            self.psql_engine.session.query(Calbright.Gender)
            .where(Calbright.Gender.gender.ilike(format_gender(student_applicant.gender)))
            .first()
        )

        # Student record information

        student_record.ccc_id = student_applicant.ccc_id
        student_record.date_of_birth = student_applicant.birthdate
        student_record.mobile_number = student_applicant.mainphone
        student_record.home_phone_number = student_applicant.mainphone

        # ssn_type 0: SSN, 1: TIN, None/Null: no response. Just need to specify if TIN or Not
        if student_applicant.ssn_type == 1:
            student_record.tax_id = student_applicant.ssn
        else:
            student_record.ssn = student_applicant.ssn

        user_record.learner_status = (
            self.psql_engine.session.query(Calbright.LearnerStatus)
            .where(Calbright.LearnerStatus.status == "App Submitted")
            .first()
        )

        ethnicity_rows = (
            self.psql_engine.session.query(Calbright.Ethnicity)
            .where(Calbright.Ethnicity.ethnicity.in_(format_ethnicity(student_applicant.race_ethnic)))
            .all()
        )
        for ethnicity in ethnicity_rows:
            student_ethnicity = Calbright.StudentEthnicity()
            student_ethnicity.student = student_record
            student_ethnicity.ethnicity = ethnicity
            student_records_list.append(student_ethnicity)

        # Student Address
        student_address = Calbright.StudentAddress()
        student_address.current = True
        student_address.valid = student_applicant.address_val_override
        student_address.student = student_record

        # Permanent Address (need to add if exists)
        if not student_applicant.no_perm_address_homeless:
            permanent_address = Calbright.Address()
            permanent_address.address1 = student_applicant.perm_streetaddress1
            permanent_address.address2 = student_applicant.perm_streetaddress2
            permanent_address.city = student_applicant.perm_city
            permanent_address.state = student_applicant.perm_state
            permanent_address.zip = student_applicant.perm_postalcode
            permanent_address.country = student_applicant.perm_country

            student_address.address_type = "Permanent"
            student_address.address = permanent_address
            student_records_list.append(student_address)

        if not student_applicant.no_mailing_address_homeless:
            # Mailing Address
            mailing_address = Calbright.Address()
            mailing_address.address1 = student_applicant.streetaddress1
            mailing_address.address2 = student_applicant.streetaddress2
            mailing_address.city = student_applicant.city
            mailing_address.state = student_applicant.state
            mailing_address.zip = student_applicant.postalcode
            mailing_address.country = student_applicant.country

            student_address.address_type = "Mailing"
            student_address.address = mailing_address
            student_records_list.append(student_address)

        # Contact Times
        availablility_dict = {
            "available_mornings": "Weekday Mornings (8am - 12pm)",
            "available_afternoons": "Weekday Afternoons (12pm - 5pm)",
            "available_evenings": "Weekday Evenings (5pm - 8pm)",
            "available_weekends": "Weekends (10am - 4pm)",
        }
        for availability, value in availablility_dict.items():
            if student_applicant.__getattribute__(availability):
                # Student Contact Time
                student_contact_time = Calbright.StudentContactTime()
                student_contact_time.student = student_record
                student_contact_time.preferred_contact_time = (
                    self.psql_engine.session.query(Calbright.PreferredContactTime)
                    .where(Calbright.PreferredContactTime.preferred_contact_time.ilike(value))
                    .first()
                )
                student_records_list.append(student_contact_time)

        # Contact Methods
        contact_dict = {
            "contact_email": "email",
            "contact_phone_call": "phone call",
            "contact_text_message": "text method",
        }
        for contact, value in contact_dict.items():
            if student_applicant.__getattribute__(contact):
                # Student Contact Method
                student_contact_method = Calbright.StudentContactMethod()
                student_contact_method.student = student_record
                student_contact_method.preferred_contact_method = (
                    self.psql_engine.session.query(Calbright.PreferredContactMethod)
                    .where(Calbright.PreferredContactMethod.preferred_contact_method.ilike(value))
                    .first()
                )
                student_records_list.append(student_contact_method)

        student_records_list.append(student_record)

        user_record.student = student_record
        student_records_list.append(user_record)

        return student_records_list
