import asyncio
from datetime import datetime
from typing import AnyStr

from propus.anthology import Anthology
from propus.calbright_sql.calbright import Calbright
from propus.logging_utility import Logging

from src.exceptions import (
    UnrecognizedGrade,
    MissingAnthologyInformation,
    UnrecognizedAnthologyData,
    FailedAnthologyRegistration,
)


class UpdateCreateGrades:
    def __init__(self, configs, psql_engine: Calbright, anthology: Anthology):
        self.configs = configs
        self.logger = Logging.get_logger(
            "castor/lambda_functions/calbright_trigger_workflow/workflows/process_update_create_grades"
        )
        self.psql_engine = psql_engine
        self.anthology = anthology
        self.user_record = Calbright.User
        self.enrollment_record = Calbright.Enrollment
        self.enrollment_course_term_record = Calbright.EnrollmentCourseTerm

    @staticmethod
    def build(configs, ssm):
        from configuration.config import setup_anthology, setup_postgres_engine

        return UpdateCreateGrades(
            configs=configs,
            psql_engine=setup_postgres_engine(configs.get("psql_ssm"), ssm),
            anthology=setup_anthology(configs.get("anthology_ssm"), ssm),
        )

    def process(self, record_id: AnyStr, trigger_op: AnyStr):
        """ingestion process for new and existing grades that need to be processed and inserted into SIS (Anthology).

        Args:
            record_id (AnyStr): record id that needs to be ingested
            trigger_op (AnyStr): operation that fired trigger

        Raises:
            err: Log and raise error if update and creation of grades workflow failed
        """
        try:
            self.get_enrollment_course_term_based_on_id(record_id)

            if trigger_op == "UPDATE":
                self.update_or_create_sis_grades()
            elif trigger_op == "INSERT":
                if self.user_record.anthology_id and self.enrollment_record.sis_enrollment_id:
                    created_course = self.create_sis_courses(
                        self.user_record.anthology_id, self.enrollment_record.sis_enrollment_id
                    )

                    if self.enrollment_course_term_record.grade_status.value == "Certified" and created_course:
                        self.update_or_create_sis_grades()
                    elif not created_course:
                        self.logger.warn(f"Course was not created in Anthology for record: {record_id}")
                    else:
                        self.logger.info(
                            "Course was created, but final grade not posted due to status "
                            f"{self.enrollment_course_term_record.grade_status.value} for record: {record_id}"
                        )
                else:
                    raise MissingAnthologyInformation(record_id)

        except Exception as err:
            self.logger.error(f"Error during processing of grades: {err}")
            raise err

    def update_or_create_sis_grades(self):
        """Update and Creation process for grades in Anthology

        Args:
            record_id (str): record id that needs to be ingested

        Raises:
            UnrecognizedGrade: Raises an exception if grade being passed failed the required checks
            err: Error raised if there are problems during the grade process in SIS (Anthology)
        """
        bypass_mapping = {"I": "Incomplete", "": ""}

        final_grade_mapping = ["SP", "P"]

        reason_code_mapping = {
            "D": "DROP",
            "W": "W",
            "EW": "EW",
            "MW": "MW",
            "NP": "PW",
        }

        try:
            if reason_code_mapping.get(self.enrollment_course_term_record.grade.grade):
                drop_codes = asyncio.run(self.anthology.fetch_drop_reason())
                reason_code = next(
                    reason
                    for reason in drop_codes.get("value")
                    if reason.get("Code") == reason_code_mapping.get(self.enrollment_course_term_record.grade.grade)
                )
                asyncio.run(
                    self.anthology.drop_course(
                        self.enrollment_course_term_record.anthology_course_id,
                        self.enrollment_course_term_record.drop_date,
                        reason_code.get("Id"),
                        self.enrollment_course_term_record.grade.grade,
                    )
                )
            elif self.enrollment_course_term_record.grade.grade in final_grade_mapping:
                asyncio.run(
                    self.anthology.post_final_grade(
                        course_id=self.enrollment_course_term_record.anthology_course_id,
                        letter_grade=self.enrollment_course_term_record.grade.grade,
                    )
                )
            elif bypass_mapping.get(self.enrollment_course_term_record.grade.grade):
                self.logger.warn(
                    f"Skipping Anthology updates for grade provided: {self.enrollment_course_term_record.grade.grade}"
                )
            else:
                raise UnrecognizedGrade(self.enrollment_course_term_record.grade.grade)

        except Exception as err:
            self.logger.error(f"Error during updating of student grades in Anthology: {err}")
            raise err

        return

    def get_enrollment_course_term_based_on_id(self, record_id):
        """Gets the information of the record that triggered the workflow so it can be checked against and create new
            SIS (Anthology) records.

        Args:
            record_id (str): record id that triggered workflow to grab all the information needed
        """
        self.enrollment_course_term_record = (
            self.psql_engine.session.query(Calbright.EnrollmentCourseTerm).filter_by(id=record_id).first()
        )

        self.enrollment_record = self.enrollment_course_term_record.enrollment
        self.user_record = self.enrollment_record.student.user

        return

    def create_sis_courses(self, student_id: int, enrollment_id: int):
        """Sets up and registers courses in the SIS (Anthology)

        Args:
            student_id (int): Student ID in the SIS (Anthology)
            enrollment_id (int): Enrollment ID in the SIS (Anthology)

        Raises:
            err: Raise error if problems exist during registration of courses on an enrollment in SIS (Anthology)
        """
        try:
            courses = asyncio.run(self.anthology.fetch_course_for_enrollment(student_id, enrollment_id))
            for course in courses.get("Items"):
                if not course.get("Entity"):
                    raise UnrecognizedAnthologyData(enrollment_id, "Course")

                course_id = course.get("Entity").get("CourseId")
                course_name = course.get("Entity").get("CourseName")
                if course_id is not self.enrollment_course_term_record.course_version.course.anthology_course_id:
                    continue

                student_course_id = course.get("Entity").get("Id")
                student_enrollment_period = course.get("Entity").get("StudentEnrollmentPeriodId")
                hours = course.get("Entity").get("ClockHours")
                terms = asyncio.run(self.anthology.fetch_term_for_courses([course_id]))

                for term in terms.get("value"):
                    start_date = datetime.strptime(term.get("TermStartDate").split("T")[0], "%Y-%m-%d")
                    if start_date.date() == self.enrollment_course_term_record.term.start_date:
                        enrollment_term = term
                        break

                term_id = enrollment_term.get("Id")
                start_date = enrollment_term.get("TermStartDate")
                end_date = enrollment_term.get("TermEndDate")
                course_data = asyncio.run(
                    self.anthology.fetch_classes_for_courses(student_id, term_id, course_ids=[course_id])
                )
                class_section_id = course_data.get("value")[0].get("Id")

                if (
                    self.enrollment_record.first_term_id != self.enrollment_course_term_record.term_id
                    and not self.enrollment_course_term_record.anthology_course_id
                ):
                    new_sis_course = asyncio.run(
                        self.anthology.add_new_course(
                            student_id,
                            student_enrollment_period,
                            class_section_id,
                            course_id,
                            course_name,
                            term_id,
                            start_date,
                            end_date,
                        )
                    )
                    student_course_id = new_sis_course.get("id")

                sis_course = asyncio.run(
                    self.anthology.register_course(
                        (
                            self.enrollment_course_term_record.anthology_course_id
                            if self.enrollment_course_term_record.anthology_course_id
                            else student_course_id
                        ),
                        student_enrollment_period,
                        class_section_id,
                        course_id,
                        term_id,
                        hours,
                        start_date,
                        end_date,
                    )
                )
                self.enrollment_course_term_record.anthology_course_id = student_course_id
                self.psql_engine.session.commit()
                if not sis_course.get("entity"):
                    raise FailedAnthologyRegistration(self.enrollment_course_term_record.id)
                return True
        except Exception as err:
            self.logger.error(f"Error during creation of course registration in Anthology: {err}")
            raise err

        return False
