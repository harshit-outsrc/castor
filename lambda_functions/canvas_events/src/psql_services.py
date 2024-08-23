from typing import Union, Literal
from sqlalchemy import text, select
from sqlalchemy.orm.exc import NoResultFound

from src.exceptions import (
    UserNotFoundInDatabase,
    InvalidFinalGrade,
    AssigmentNotFoundInDatabase,
    EnrollmentNotFoundInDatabase,
    CourseNotFoundInDatabase,
)

from propus.calbright_sql.assessment import Assessment
from propus.calbright_sql.assessment_submission import AssessmentSubmission
from propus.calbright_sql.calbright import Calbright
from propus.calbright_sql.course_version import CourseVersion
from propus.calbright_sql.enrollment import LMS, Enrollment
from propus.calbright_sql.enrollment_course_term import EnrollmentCourseTerm, GradeStatus
from propus.calbright_sql.enrollment_status import EnrollmentStatus
from propus.calbright_sql.grade import Grade
from propus.calbright_sql.learner_status import LearnerStatus
from propus.calbright_sql.student import Student
from propus.calbright_sql.user import User
from propus.calbright_sql.user_lms import UserLms

from propus.logging_utility import Logging

all_models = tuple(Calbright.all_models)


class PSQLServices:
    """
    This class is used to interact with the Calbright Postgres database.
    """

    def __init__(self, psql_engine: Calbright):
        """
        Initialize the PSQLServices object
        Args:
            psql_engine: The Propus Calbright object
        """
        self.logger = Logging.get_logger(
            "castor/lambda_functions/canvas_events/canvas_event_system/psql_services", debug=True
        )
        self.psql_engine = psql_engine

    def get_student(self, ccc_id):
        """
        Get a student from the database by their ccc_id
        Args:
            ccc_id: The student's ccc_id

        Returns: The student object

        """
        try:
            return self.psql_engine.session.execute(select(Student).filter_by(ccc_id=ccc_id)).scalar_one()
        except NoResultFound:
            self.logger.warn(f"User with ccc_id {ccc_id} not found in the database.")
            raise UserNotFoundInDatabase(ccc_id)

    def get_student_enrollment(self, lms_id):
        """
        Get a single active enrollment for a student from the database, using their lms_id
        - This gets the first enrollment that is either Enrolled/Started where the student has 'canvas' as their lms
        Args:
            lms_id: The student's canvas_id

        Returns: The enrollment object

        """
        self.logger.debug(f"Getting student enrollment with lms_id: {lms_id}")
        try:
            data = self.psql_engine.session.execute(
                select(Enrollment)
                .join(Student, Enrollment.ccc_id == Student.ccc_id)
                .join(User, Student.ccc_id == User.ccc_id)
                .join(UserLms, User.id == UserLms.user_id)
                .join(EnrollmentStatus, Enrollment.enrollment_status_id == EnrollmentStatus.id)
                .filter(
                    UserLms.lms_id == lms_id,
                    UserLms.lms == "canvas",
                    EnrollmentStatus.status.in_(["Enrolled", "Started"]),
                )
            ).scalar_one()
            self.logger.debug(f"Fetched Enrollment: {data}")
            return data
        except NoResultFound:
            self.logger.warn(f"Enrollment for user with lms_id {lms_id} not found in the database.")
            raise EnrollmentNotFoundInDatabase(lms_id)

    def get_assignment_by_canvas_id(
        self, canvas_id, lms_type: Literal["assignment", "discussion", "quiz"] = "assignment"
    ):
        """
        Get an assignment from the database by its canvas_id
        Args:
            canvas_id: The assignment's canvas_id
            lms_type: The type of assignment, either "assignment", "discussion", or "quiz"

        Returns: The assignment object

        """
        self.logger.debug(f"Getting assignment with canvas_id: {canvas_id}, lms_type: {lms_type}")
        try:
            return self.psql_engine.session.execute(
                select(Assessment).filter_by(lms_id=canvas_id, lms_type=lms_type)
            ).scalar_one()
        except NoResultFound:
            self.logger.error(f"Assignment with canvas_id {canvas_id} not found in the database.")
            raise AssigmentNotFoundInDatabase(canvas_id)

    def get_submission_by_submission_id(self, submission_id):
        """
        Get an assessment submission from the database by its submission_id
        Args:
            submission_id: The submission's lms_id

        Returns: The assessment submission object

        """
        self.logger.debug(f"Getting submission with submission_id: {submission_id}")
        try:
            return self.psql_engine.session.execute(
                select(AssessmentSubmission).filter_by(lms_id=submission_id)
            ).scalar_one()
        except NoResultFound:
            return None

    def update_object(self, db_object: Union[all_models]):
        try:
            self.psql_engine.session.add(db_object)
            self.psql_engine.session.commit()
        except Exception as err:
            self.psql_engine.session.rollback()
            raise err

    def get_user_info_by_canvas_id(self, canvas_id, user_type: Literal["student", "staff"] = "student"):
        """
        Get user information from the database by their canvas_id, including their ccc_id/staff_id and email
        Args:
            canvas_id: The user's canvas_id
            user_type: The type of user, either "student" or "staff"

        Returns: A dictionary with the user's ccc_id/staff_id and email
        """
        self.logger.debug(f"Getting user info with canvas_id: {canvas_id}, user_type: {user_type}")
        try:
            user_lms = self.psql_engine.session.execute(
                select(UserLms).filter_by(lms_id=canvas_id, lms=LMS("Canvas"))
            ).scalar_one()
        except NoResultFound:
            self.logger.error(f"User with canvas_id {canvas_id} not found in the database.")
            raise UserNotFoundInDatabase(canvas_id)
        if user_type == "student":
            return {"ccc_id": user_lms.user.ccc_id, "email": user_lms.user.calbright_email}
        elif user_type == "staff":
            return {"staff_id": user_lms.user.staff_id, "email": user_lms.user.calbright_email}

    def update_ect_progress(self, ccc_id, course_id, progress: float):
        """
        This function is used to update the progress of an enrollment_course_term record in the database.
        Args:
            ccc_id: The student's ccc_id
            course_id: The course's lms_id
            progress: The progress to update

        Returns:

        """
        # TODO: Note - I'm getting the course that is still in the 'not_graded' status, and assuming that there is only
        #   1 course in that status. This is because the previous courses should all be graded, and there should be no
        #   future courses. This may need to be updated if that assumption is incorrect.
        self.logger.info(f"Updating ECT progress for ccc_id: {ccc_id}, course_id: {course_id}, progress: {progress}")

        current_course_enrollments = (
            self.psql_engine.session.execute(
                select(EnrollmentCourseTerm)
                .join(Enrollment, Enrollment.id == EnrollmentCourseTerm.enrollment_id)
                .filter(Enrollment.ccc_id == ccc_id)
                .filter(EnrollmentCourseTerm.grade_status == GradeStatus("Not Graded"))
            )
            .scalars()
            .all()
        )
        self.logger.debug(f"Current course enrollments: {current_course_enrollments}")
        if not current_course_enrollments:
            self.logger.error(f"No matching course enrollments found for ccc_id: {ccc_id}")
            return False
        for course in current_course_enrollments:
            self.logger.debug(f"Checking course enrollment: {course}")
            if course.course_version_section.program_version_course.course_version.lms_id == course_id:
                self.logger.info(f"Updating progress for course: {course}")
                course.progress = progress * 100
                self.psql_engine.session.commit()
                return True
        return False

    def update_ect_final_grade(self, ccc_id, course_id, grade: Literal["P", "NP"], grade_timestamp, instructor_lms_id):
        """
        Update the final grade for an enrollment_course_term in the database.
        This is used when the instructor grades the 'final grade' assignment for a course and assigns either a P/NP
        Args:
            ccc_id: The student's ccc_id
            course_id: The course's lms_id
            grade: The final grade, either "P" or "NP"
            grade_timestamp: The timestamp of when the grade was assigned
            instructor_lms_id: The instructor's canvas_id

        Returns: True if the grade was updated successfully

        """
        self.logger.info(
            f"Updating final grade for ccc_id: {ccc_id}, course_id: {course_id}, grade: {grade}, "
            f"grade_timestamp: {grade_timestamp}, instructor_lms_id: {instructor_lms_id}"
        )
        if grade not in ("P", "NP"):
            raise InvalidFinalGrade(grade)

        # Get the grade object and the instructor object from the database
        grade_object = self.psql_engine.session.execute(select(Grade).filter_by(grade=grade)).scalar_one()
        instructor = self.get_user_info_by_canvas_id(instructor_lms_id, user_type="staff")

        # Get the current course enrollments for the student
        # Note: this filters to only courses in 'not_graded' status and assumes that there is only 1 course in
        #   'not_graded' status (previous courses should all be graded, and there should be no future courses)
        current_course_enrollments = (
            self.psql_engine.session.execute(
                select(EnrollmentCourseTerm)
                .join(Enrollment, Enrollment.id == EnrollmentCourseTerm.enrollment_id)
                .filter(Enrollment.ccc_id == ccc_id)
                .filter(EnrollmentCourseTerm.grade_status == GradeStatus("Not Graded"))
            )
            .scalars()
            .all()
        )
        self.logger.debug(f"Current course enrollments: {current_course_enrollments}")
        for course in current_course_enrollments:
            if course.course_version_section.program_version_course.course_version.lms_id == course_id:
                self.logger.info(f"Updating final grade for course: {course}")
                course.grade_status = GradeStatus("Submitted")
                course.grade = grade_object
                course.grade_date = grade_timestamp
                course.instructor_id = instructor["staff_id"]
                if grade == "P":
                    course.progress = 100
                self.psql_engine.session.commit()
                return course

    def calculate_progress(
        self,
        lms_id: str,
        progress_type: Literal["course", "program"],
        course_lms_id: Union[str, None] = None,
    ):
        """
        Calculate the progress of a student in a course or program based on:
        - How many competencies are in the course/program
        - How many summative assessments have been passed
        Args:
            lms_id: The student's canvas_id
            progress_type: The type of progress to calculate, either "course" or "program"
            course_lms_id: The course's lms_id if progress_type is "course"

        Returns: A dictionary with the number of competencies, the number of competencies passed, and the percentage,
            for example: {'competencies': 7, 'completed': 3, 'percentage': 0.42857142857142855}
        """
        student_enrollment = self.get_student_enrollment(lms_id=lms_id)

        # TODO: can swap these views to SQLAlchemy views instead of raw SQL views...
        if progress_type == "program":
            query = text(f"SELECT * FROM progress_by_enrollment WHERE enrollment_id = '{student_enrollment.id}'")
            results = self.psql_engine.session.execute(query).fetchone()
            return {"competencies": results[1], "completed": results[2], "percentage": float(results[3])}
        elif progress_type == "course":
            try:
                course_version = self.psql_engine.session.execute(
                    select(CourseVersion).filter_by(lms_id=course_lms_id)
                ).scalar_one()
            except NoResultFound:
                self.logger.error(f"Course with lms_id {course_lms_id} not found in the database.")
                raise CourseNotFoundInDatabase(course_lms_id)

            query = text(
                f"SELECT * FROM progress_by_course WHERE enrollment_id = '{student_enrollment.id}' "
                f"AND course_id = '{course_version.course.id}'"
            )
            results = self.psql_engine.session.execute(query).fetchone()
            return {"competencies": results[2], "completed": results[3], "percentage": float(results[4])}

    def update_program_progress(self, lms_id: str):
        """
        Update the program progress for a student in the database (enrollment table)
        Args:
            lms_id: The student's canvas_id

        Returns: The program progress as a dictionary, or None

        """
        self.logger.info(f"Updating program progress for lms_id: {lms_id}")
        student_enrollment = self.get_student_enrollment(lms_id=lms_id)
        program_progress = self.calculate_progress(lms_id=lms_id, progress_type="program")
        if program_progress.get("percentage"):
            self.logger.info(f"Updating program progress to {program_progress.get('percentage')}")
            student_enrollment.progress = program_progress.get("percentage") * 100
            self.psql_engine.session.commit()
            return program_progress
        self.logger.info("No program progress calculated")

    def get_course_code_by_lms_id(self, lms_id):
        """
        Get the course code by the lms_id. This is used to get the course code for the course that the student is in.
        Args:
            lms_id: The lms_id of the course

        Returns: The course code

        """
        self.logger.debug(f"Getting course code for lms_id: {lms_id}")
        try:
            course_version = self.psql_engine.session.execute(
                select(CourseVersion).filter_by(lms_id=lms_id)
            ).scalar_one()
        except NoResultFound:
            self.logger.error(f"Course with lms_id {lms_id} not found in the database.")
            raise CourseNotFoundInDatabase(lms_id)
        return course_version.course.course_code

    def update_enrollment_status_at_first_saa(self, enrollment: Enrollment, commit=False):
        """
        Update the enrollment status to 'Started Program Pathway' and the learner status to 'Started' for a student
        when they submit the first SAA.
        Args:
            enrollment: The enrollment object
            commit: Whether to commit the changes to the database

        Returns: The updated enrollment object

        """
        self.logger.info(f"Updating enrollment status for enrollment: {enrollment}")
        enrollment.student.user.learner_status_id = self.psql_engine.session.execute(
            select(LearnerStatus.id).filter_by(status="Started Program Pathway")
        ).scalar_one()
        enrollment.enrollment_status_id = self.psql_engine.session.execute(
            select(EnrollmentStatus.id).filter_by(status="Started")
        ).scalar_one()
        if commit:
            self.psql_engine.session.commit()
        return enrollment
