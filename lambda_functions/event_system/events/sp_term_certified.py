from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from propus.calbright_sql.enrollment_course_term import EnrollmentCourseTerm
from propus.calbright_sql.term import Term
from propus.logging_utility import Logging
from propus.helpers.sql_calbright.term_grades import upsert_eotg_records


from events.base import BaseEventSystem

# Custom Exceptions for this event


class MissingEnrollmentCourseTermInDB(Exception):
    """Exception raised for missing grade in Database"""

    def __init__(self, event):
        super().__init__(f"grade not found in database {event}")


class MissingTermInDB(Exception):
    """Exception raised for missing term in Database"""

    def __init__(self, sf_term_data):
        super().__init__(f"term not found in database {sf_term_data}")


class SpTermGradeCertified(BaseEventSystem):
    __event_type__ = "sp_term_grade_certified"
    _required_fields = [
        "salesforce_grade_id",
        "enrollment_course_term_id",
    ]

    def __init__(self, configs, calbright, salesforce):
        super().__init__(configs)
        self.logger = Logging.get_logger("event/sp_term_grade_certified")
        self.salesforce = salesforce
        self.db_session = calbright.session

    @staticmethod
    def build(configs, ssm):
        from services.calbright_client import CalbrightClient
        from services.salesforce_client import SalesforceService

        return SpTermGradeCertified(
            configs=configs,
            calbright=CalbrightClient(configs.get("calbright_write_ssm"), ssm),
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
        )

    def run(self, event):
        self.check_required_fields(self.__event_type__, event, self._required_fields)

        try:
            ect = self.db_session.execute(
                select(EnrollmentCourseTerm).filter_by(id=event.get("enrollment_course_term_id"))
            ).scalar_one()
        except NoResultFound:
            raise MissingEnrollmentCourseTermInDB(event)

        # Fetch the next sequential term for student
        # TODO: Ingest Salesforce Term IDs to DB so we can just do one lookup instead of 2 (SF & DB)
        next_term = self.salesforce.get_next_term(
            (ect.term.end_date + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )

        try:
            term = self.db_session.execute(select(Term).filter_by(term_name=next_term.get("Name"))).scalar_one()
        except NoResultFound:
            raise MissingTermInDB(event)

        # Update SF current term on contact record
        self.salesforce.client.update_contact_record(
            ect.enrollment.student.user.salesforce_id, Current_Term__c=next_term.get("Id")
        )

        # Create End Of Term Records (SF & DB)
        response = self.salesforce.client.create_end_of_term_grade(
            ect.course_version.course.course_code,
            ect.enrollment.ccc_id,
            ect.enrollment.student.user.salesforce_id,
            next_term.get("Id"),
            next_term.get("Name"),
            instructor_id=ect.instructor.user.salesforce_id,
        )

        new_ect, _ = upsert_eotg_records(
            session=self.db_session,
            term_id=term.id,
            sf_grade_id=response.get("id"),
            course=ect.course_version.course,
            instructor_id=ect.instructor_id,
            enrollment=ect.enrollment,
        )

        # Transfer Progress From Previous EOTG Record to New One
        new_ect.progress = ect.progress

        # Course Version Section
        new_ect.course_version_section_id = new_ect.course_version_section_id

        self.db_session.commit()
