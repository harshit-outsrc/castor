import datetime
import re
from zoneinfo import ZoneInfo

# import pytz

from typing import Literal


from propus.calbright_sql.calbright import Calbright
from propus.calbright_sql.assessment import AssessmentType
from propus.calbright_sql.assessment_submission import AssessmentSubmission, AssessmentSubmissionStatus
from propus.calbright_sql.enrollment import LMS
from propus.logging_utility import Logging
from propus.salesforce import Salesforce
from propus.canvas import Canvas

from src.canvas_services import CanvasServices
from src.exceptions import (
    AssigmentNotFoundInDatabase,
    MissingGraderId,
    NoUserInfoInEvent,
    NoSubmissionFound,
    EnrollmentNotFoundInDatabase,
    NoSubmissionTimestamp,
)
from src.psql_services import PSQLServices
from src.sf_services import SFServices


class BaseEvent:
    """
    This class is used to process events from Canvas. All other handlers inherit from this class.

    - It will take an event from the Canvas event stream > SQS, and process it based on the event type.
    - It will update the database and Salesforce as needed based on the event type.
    - The events having varying structures, so this class will parse the event and get the relevant information from it
    in a consistent way. For example - fetching the user_id from a few different places in the event.
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        """
        Initialize the BaseEvent class with the event, and the PSQL / Salesforce / Canvas clients
        Args:
            event: The event from the Canvas event stream
            psql_engine: The Propus Calbright PSQL engine
            sf_client: The Propus Salesforce client
            canvas_client: The Propus Canvas client
        """
        self.logger = Logging.get_logger(
            "castor/lambda_functions/canvas_events/canvas_event_system/base_event", debug=True
        )
        self.metadata = self._get_metadata(event)
        self.body = self._get_body(event)
        self.user_info = self._get_user_info(event, PSQLServices(psql_engine))
        self.event_info = self._get_event_info()
        self.psql_services = PSQLServices(psql_engine)
        self.sf_services = SFServices(sf_client)
        self.canvas_services = CanvasServices(canvas_client, psql_engine)

    def _convert_pst_to_utc(self, date_obj: datetime):
        """
        Convert a date object from PST to UTC
        Args:
            date_obj: The date object to convert. If the date object has no timezone info, it will assume it is in PST.

        Returns: datetime: The date object converted to UTC

        """
        # self.logger.debug(f"Converting datetime {date_obj} from PST to UTC | Current TZ: {date_obj.tzinfo}")

        pst = ZoneInfo("America/Los_Angeles")

        if date_obj.tzinfo is not None:
            return date_obj.astimezone(ZoneInfo("UTC"))
        return date_obj.replace(tzinfo=pst).astimezone(ZoneInfo("UTC"))

    def _parse_isoformat(self, date_string):
        if date_string.endswith("Z"):
            date_string = date_string[:-1] + "+00:00"
        return datetime.datetime.fromisoformat(date_string)

    def _get_body(self, event):
        # self.logger.debug("Getting event body...")
        """
        Get the body of the event, for convenience and to change global > local IDs + convert timestamps to UTC
        Args:
            event: The event from the Canvas event stream

        Returns: dict: the body of the event, with local IDs and UTC timestamps

        """
        body = event.get("body")
        if body.get("student_id"):
            body["student_id_local"] = self._convert_global_to_local_id(body.get("student_id"))
        if body.get("submitted_at"):
            event_time = self._parse_isoformat(body.get("submitted_at"))
            body["submitted_at"] = self._convert_pst_to_utc(event_time)
        if body.get("created_at"):
            event_time = self._parse_isoformat(body.get("created_at"))
            body["created_at"] = self._convert_pst_to_utc(event_time)
        return body

    def _get_metadata(self, event):
        """
        Get the metadata of the event, for convenience, and parse the context_id and user_id to local IDs
        Args:
            event: The event from the Canvas event stream

        Returns: dict: the metadata of the event, with local IDs and UTC timestamps

        """
        # self.logger.debug("Getting event metadata...")
        metadata = event.get("metadata")
        if metadata.get("context_id"):
            metadata["context_id_local"] = self._convert_global_to_local_id(metadata.get("context_id"))
        if metadata.get("user_id"):
            metadata["user_id_local"] = self._convert_global_to_local_id(metadata.get("user_id"))
        if metadata.get("event_time"):
            event_time = self._parse_isoformat(metadata.get("event_time"))
            metadata["event_time"] = self._convert_pst_to_utc(event_time)
        return event.get("metadata")

    def _get_user_info(self, event, psql_services: PSQLServices):
        """
        Get the user info from the event - different event types present the user info in different ways, so this
        will get the user info from the event in a consistent way.

        Args:
            event: The event from the Canvas event stream
            psql_services: The Calbright PSQL services object

        Returns: dict: user_info including the user_id, user_id_local, user_sis_id, and user_login

        """
        # self.logger.debug("Getting user info from event...")
        meta = event.get("metadata")
        body = event.get("body")

        user_info = {"user_id": None}
        # Try to get the user_id from body, if it's not there get the student_id, if it's not there get meta user_id
        if body.get("user_id"):
            user_info["user_id"] = body.get("user_id")
        elif body.get("student_id"):
            user_info["user_id"] = body.get("student_id")
        elif meta.get("user_id"):
            user_info["user_id"] = meta.get("user_id")

        if user_info["user_id"]:
            user_info["user_id_local"] = self._convert_global_to_local_id(user_info["user_id"])

        if body.get("user", {}).get("id"):
            user_info["user_id"] = body.get("user").get("id")
            user_info["user_id_local"] = body.get("user").get("id")

        if not user_info.get("user_id_local"):
            raise NoUserInfoInEvent()
        # Try to get the sis_id/cc_id and email from the event, if not there, get it from the database
        if body.get("student_sis_id") and meta.get("user_login"):
            # TODO: I'm getting the user here from the DB bc for the final grade events the user comes in as
            #   the instructor instead of the student... Can figure out a different way to do this prob...
            user_info_from_db = psql_services.get_user_info_by_canvas_id(canvas_id=user_info["user_id_local"])
        else:
            user_info_from_db = psql_services.get_user_info_by_canvas_id(canvas_id=user_info["user_id_local"])
        user_info["user_sis_id"] = user_info_from_db.get("ccc_id")
        user_info["user_login"] = user_info_from_db.get("email")
        return user_info

    def _get_event_info(self):
        """
        Get the event info from the event, for convenience
        Args:
            event: The event from the Canvas event stream

        Returns: dict: the event info including event name, time, context_type, and context_id

        """
        # self.logger.debug("Getting event info from event...")
        event_info = {
            "event_name": self.metadata.get("event_name"),
            "event_time": self.metadata.get("event_time"),
            "context_type": self.metadata.get("context_type"),
            "context_id": self.metadata.get("context_id"),
            "context_account_id": self.metadata.get("context_account_id"),
        }
        if self.metadata.get("context_id"):
            event_info["context_id_local"] = self._convert_global_to_local_id(self.metadata.get("context_id"))
        return event_info

    def _convert_global_to_local_id(self, id_string):
        """
        A helper function to convert a global ID to a local ID (which is the main ID used across Canvas and in the UI)
        Note: Instructure has noted that they are going to be moving away from global IDs in the future, so this
        function may not be needed in the future.
        Reference here: https://canvas.instructure.com/doc/api/file.data_service_canvas_event_metadata.html
        Args:
            id_string: The global ID string. For example '21070000000000123'

        Returns: str: the local ID string. For example '123'

        """

        if len(id_string) < 16:
            return id_string
        match = re.compile(r"0+(\d+)$").search(id_string)
        if match:
            # self.logger.debug(f"Converted global ID {id_string} to local ID {match.group(1)}")
            return match.group(1)
        # self.logger.warning(f"Could not convert global ID {id_string} to local ID")

    def check_and_update_saa_timestamp(self):
        """
        This function is used to update the SAA information in the database and Salesforce.
        It will check to see if it needs to update the SAA timestamp in the database and Salesforce, and if so, it will.
        It will also set the first_saa in the database if that is currently not set.

        Returns: None
        """
        self.logger.info(f"Checking and updating SAA timestamp for user {self.user_info['user_id_local']}...")
        student_enrollment = self.psql_services.get_student_enrollment(lms_id=self.user_info["user_id_local"])
        if not student_enrollment:
            self.logger.error(f"Student with lms_id {self.user_info['user_id_local']} not found.")
            raise EnrollmentNotFoundInDatabase

        # * POSTGRES UPDATES *
        # update postgres with the latest SAA timestamp
        try:
            pg_last_saa = student_enrollment.last_saa.replace(tzinfo=datetime.timezone.utc)
        except AttributeError:
            pg_last_saa = None

        event_timestamp = self.event_info["event_time"]
        email = self.user_info["user_login"]

        # If they don't have a first SAA timestamp, set it and attempt to update the enrollment/learner status
        if not student_enrollment.first_saa:
            self.logger.info(f"Setting first SAA in database for user {self.user_info['user_id_local']}")
            student_enrollment.first_saa = event_timestamp.isoformat()
            if student_enrollment.student.user.learner_status.status == "Enrolled in Program Pathway":
                student_enrollment = self.psql_services.update_enrollment_status_at_first_saa(student_enrollment)
                self.sf_services.update_learner_status(email=email, status="Started Program Pathway")

            self.psql_services.update_object(student_enrollment)

        # If the event timestamp is greater than the last SAA timestamp, or there is no last SAA timestamp, update it
        if pg_last_saa is None or event_timestamp > pg_last_saa:
            self.logger.info(
                f"Setting last SAA in database for user {self.user_info['user_id_local']} | {event_timestamp}"
            )
            student_enrollment.last_saa = event_timestamp.isoformat()
            self.psql_services.update_object(student_enrollment)

        # * SALESFORCE UPDATES *
        # update salesforce with the latest SAA timestamp
        sf_saa_timestamp = self.sf_services.get_contact_field(email=email, sf_field="Last_Strut_SAA_Timestamp__c")
        if sf_saa_timestamp is None or event_timestamp > sf_saa_timestamp:
            self.logger.info(
                f"Setting SAA in Salesforce for user {self.user_info['user_id_local']} | {event_timestamp}"
            )
            self.sf_services.update_contact_saa_timestamp(email=email, timestamp=event_timestamp)

    def process_grade_change_event(self):
        """
        This function is used to process a grade change event from Canvas. It will:
        - Update the grade for a submission in the database (assessment_submission table)
        - For summative and pre-assessments, it will also calculate if the student has passed/failed
        - For summative assessments, it will calculate and update the course progress in the database and Salesforce
        - For final_grade assignments, it will update the final grade in the database (enrollment_course_term), and the
            course as completed in Salesforce (if a 'P' grade is assigned)
        Returns: None

        """
        # Get the assignment ID from the event > convert to local ID > fetch from the database
        assignment_id = self._convert_global_to_local_id(self.body["assignment_id"])
        assignment_from_db = self.psql_services.get_assignment_by_canvas_id(canvas_id=assignment_id)
        ccc_id = self.user_info.get("user_sis_id")

        if not assignment_from_db:
            raise AssigmentNotFoundInDatabase(assignment_id)

        if not self.body.get("grading_complete"):
            # TODO: what to do if grading is not complete? Just return? I don't think we'd want to update anything...
            self.logger.warning(f"Grading not complete for submission {self.body['submission_id']}, returning...")

        # * FINAL GRADES *
        # Check if this is the 'final grade assignment' being graded by an instructor (i.e. "P" Grade...)
        if assignment_from_db.assessment_type == AssessmentType("Final Grade"):
            self.logger.info(f"Processing final grade for user {self.user_info['user_id_local']}...")
            if self.body.get("grading_complete"):
                grade = self.body["grade"]

                # Get course and instructor info from payload, we'll need this to update the final grade in the DB
                course_id = self.event_info.get("context_id_local")
                grader_id = self.body.get("grader_id")
                if not grader_id:
                    raise MissingGraderId()
                grader_id_local = self._convert_global_to_local_id(grader_id)

                # Update the grade in the database (enrollment_course_term table)
                try:
                    enrollment_course_term = self.psql_services.update_ect_final_grade(
                        ccc_id=ccc_id,
                        course_id=course_id,
                        grade=grade,
                        grade_timestamp=self.event_info.get("event_time"),
                        instructor_lms_id=grader_id_local,
                    )
                except Exception as e:
                    self.logger.error(f"Error updating final grade for user {self.user_info['user_id_local']} {e}")
                    enrollment_course_term = None

                # Update the course as completed in Salesforce
                email = self.user_info.get("user_login")
                course_id = self.event_info.get("context_id_local")
                course_code = self.psql_services.get_course_code_by_lms_id(course_id)
                if enrollment_course_term:
                    # This updates the EOTG in Salesforce using the SF_ID from the enrollment_course_term record
                    self.sf_services.update_eotg(
                        grade_id=enrollment_course_term.grade_salesforce_id,
                        grade=grade,
                        grade_timestamp=self.event_info.get("event_time"),
                    )

                # Update the checkbox of 'Completed Course #...' in Salesforce
                self.sf_services.update_course_completed(email=email, course_code=course_code)
            # TODO: what happens if the instructor has an oopsie doodles and grades the wrong student and then is
            #   like "oh no, I didn't mean to do that" and changes the grade back to null or something?
            return None

        # Fetch the student's submission from the database. This is done on the submission_id, not the assignment_id.
        submission_id_local = self._convert_global_to_local_id(self.body["submission_id"])
        submission_from_db = self.psql_services.get_submission_by_submission_id(submission_id=submission_id_local)

        if not submission_from_db:
            self.logger.warning(
                f"Submission {submission_id_local} not found in database, attempting to fetch from REST API..."
            )
            # This creates the submission if it doesn't already exist by fetching it from the REST API (instead of
            #   the events), since we need to have the submission in order to update the grade.
            # FYI This is mainly to handle Skillways sending the events out of order... :|
            first_submission = self.canvas_services.get_first_assignment_submission(
                assignment_id=assignment_id,
                user_id=self.user_info.get("user_id_local"),
                course_id=self.event_info.get("context_id"),
            )
            if not first_submission:
                self.logger.error(f"No submission found in REST API for user {self.user_info['user_id_local']}")
                raise NoSubmissionFound()

            # Get the student enrollment from the database - we need this ID to create the submission record
            student_enrollment = self.psql_services.get_student_enrollment(lms_id=self.user_info.get("user_id_local"))

            # TODO: should we add 'graded' as an enum status to the DB?
            submission_status = first_submission.get("workflow_state", "submitted")
            if submission_status == "graded" or submission_status == "pending_review":
                submission_status = "submitted"

            new_submission = AssessmentSubmission(
                enrollment_id=student_enrollment.id,
                assessment_id=assignment_from_db.id,
                attempt=first_submission.get("attempt", 1),
                score=first_submission.get("score"),
                grade=first_submission.get("grade"),
                submission_timestamp=first_submission.get("submitted_at"),
                lms=LMS("Canvas"),
                lms_id=first_submission.get("id"),
                status=submission_status,
            )
            self.logger.info(
                f"Inserting submission record {submission_id_local} into database for user "
                f"{self.user_info.get('user_id_local')}"
            )
            self.psql_services.psql_engine.session.add(new_submission)
            # self.psql_services.psql_engine.session.flush()  # TODO: verify swapping this commit/flush works...
            self.psql_services.psql_engine.session.commit()
            # This sets our submission_from_db used in the next steps to the new submission record we just created
            submission_from_db = new_submission
        else:

            self.logger.info(
                f"Updating submission record {submission_id_local} with score and grade for user "
                f"{self.user_info.get('user_id_local')}"
            )
            submission_from_db.score = self.body.get("score")
            submission_from_db.grade = self.body.get("grade")

        # Check if this is a summative or pre-assessment, and if so, calculate if the student has passed
        if assignment_from_db.assessment_type in {AssessmentType("Summative"), AssessmentType("Pre-Assessment")}:
            self.logger.info("Calculating if student has passed summative or pre-assessment...")
            minimum_required_percentage = assignment_from_db.required_percentage_to_pass
            # TODO: Add a check to make sure the points_possible isn't 0 before dividing...
            scored_percentage = self.body.get("score", 0) / self.body.get("points_possible", 0)
            submission_from_db.status = AssessmentSubmissionStatus(
                "Passed" if scored_percentage >= minimum_required_percentage else "Failed"
            )

            self.logger.info(
                f"Updating submission record {submission_id_local} with grade in database for user "
                f"{self.user_info['user_id_local']}"
            )
            self.psql_services.psql_engine.session.commit()

            if assignment_from_db.assessment_type == AssessmentType("Summative"):
                # At this point - recalculate their progress from the DB and then go and update both their enrollment
                # record in the database and Salesforce with the progress percentage
                self.update_progress()

        else:
            # If this is NOT a summative or pre-assessment, just update the submission with the grade
            # For these types of assignments, we don't need to check if they passed or failed so the status
            #   will just be 'submitted'
            self.logger.info(
                f"Updating submission record {submission_id_local} with grade in database for user "
                f"{self.user_info['user_id_local']}"
            )
            submission_from_db.status = AssessmentSubmissionStatus("Submitted")
            self.psql_services.psql_engine.session.commit()

    def process_submission_event(self, lms_type: Literal["assignment", "discussion", "quiz"] = "assignment"):
        """
        This function is used to process a submission event from Canvas. It will:
        - Create or update the submission record in the database (assessment_submission table)
        - If the summative is identified from the db as being the last summative of the course, it will enroll the
            student in their next course
        Args:
            lms_type: The type of LMS object the submission is for. Can be 'assignment', 'discussion', or 'quiz'
                This is important as it provides the context for the asset ID.
        Returns: None

        """
        self.logger.info(f"Processing submission event for user {self.user_info['user_id_local']}...")
        # Get the 'assignment' ID from the event. This is the ID of the assignment, discussion, or quiz.
        if lms_type == "discussion":
            # Note: we are creating multiple submission records for each discussion entry in the
            #  assessment_submission table, cause they have unique discussion_entry_id's.

            # Note: So when it's a graded discussion, I'm getting the assignment ID, and then resetting the context
            #    of the lms_type to be an assignment so we fetch the assignment ID from the DB....
            assignment_id = self._convert_global_to_local_id(self.body.get("discussion_topic_id"))
            if self.body.get("assignment_id"):
                assignment_id = self._convert_global_to_local_id(self.body.get("assignment_id"))
                lms_type = "assignment"

            submission_id_local = self._convert_global_to_local_id(self.body.get("discussion_entry_id"))
            submission_timestamp = self.body.get("created_at")
        elif lms_type == "quiz":
            # TODO: for quizzes, the score doesn't come in with the quiz_submitted event. So we may need to
            #   fetch from the API. Or maybe it's a separate 'grade_change' event for the actual assignment
            #   We're not using quizzes right now in Canvas so revisit this later...
            assignment_id = self._convert_global_to_local_id(self.body.get("quiz_id"))
            submission_id_local = self._convert_global_to_local_id(self.body.get("submission_id"))
            submission_timestamp = self.event_info.get("event_time")
        else:
            assignment_id = self._convert_global_to_local_id(self.body.get("assignment_id"))
            submission_id_local = self._convert_global_to_local_id(self.body.get("submission_id"))
            submission_timestamp = self.body.get("submitted_at")

        if not submission_timestamp:
            self.logger.error("No submission timestamp found in event...")
            raise NoSubmissionTimestamp()

        # Fetch the assignment from the database using the assignment ID and LMS type
        assignment_from_db = self.psql_services.get_assignment_by_canvas_id(canvas_id=assignment_id, lms_type=lms_type)
        if not assignment_from_db:
            self.logger.error(f"Assignment {assignment_id} not found in database...")
            raise AssigmentNotFoundInDatabase(assignment_id)

        self.logger.info(f"Fetched assignment ID {assignment_id} from database...")

        # Get the student enrollment from the database
        student_enrollment = self.psql_services.get_student_enrollment(lms_id=self.user_info.get("user_id_local"))

        # Try to fetch the submission from the database to see if it exists / needs to be updated
        submission_from_db = self.psql_services.get_submission_by_submission_id(submission_id=submission_id_local)
        submission_status = self.body.get("workflow_state", "submitted")

        # TODO: should we add 'graded' as an enum status to the DB?
        if submission_status == "graded" or submission_status == "pending_review":
            submission_status = "submitted"

        # If the submission doesn't exist in the database, create a new one
        if not submission_from_db:
            self.logger.info(
                f"Inserting submission record {submission_id_local} into database for user"
                f' {self.user_info["user_id_local"]}...'
            )
            new_submission = AssessmentSubmission(
                enrollment_id=student_enrollment.id,
                assessment_id=assignment_from_db.id,
                attempt=self.body.get("attempt", 0),
                score=self.body.get("score"),
                grade=self.body.get("grade"),
                submission_timestamp=submission_timestamp,
                lms=LMS("Canvas"),
                lms_id=submission_id_local,  # This lms_id can either be the submission_id OR the discussion_entry_id.
                #    To know which it is, check the 'lms_type' on the assessment
                status=submission_status,
            )
            self.psql_services.psql_engine.session.add(new_submission)
            self.psql_services.psql_engine.session.commit()
            # self.psql_services.psql_engine.session.flush()  # TODO: verify swapping this commit/flush works...
        else:
            self.logger.debug("submission found in database...")
            # TODO: - if the student has already PASSED the summative, and then resubmits, this would set the status
            #   back to submitted. Should we check if the status is already passed, and if so, don't update?
            #   In this - perhaps we ONLY update the score IF it is higher than a previously passed attempt
            #   This is probably an edge case, but worth considering...

            # if the submission exists, check if the attempt is greater than the existing attempt, and update if so
            if self.body.get("attempt", 0) > submission_from_db.attempt:

                self.logger.info(
                    f"Updating submission record {submission_id_local} with new attempt for user"
                    f' {self.user_info["user_id_local"]}...'
                )
                submission_from_db.attempt = self.body.get("attempt")
                # TODO: I'm turning off the grade updating for the submission here, since with Skillways extra attempts
                #   it's overwriting already graded attempts. Leaving for now to revisit after fixed...
                # submission_from_db.score = self.body.get("score")
                # submission_from_db.grade = self.body.get("grade")
                submission_from_db.submission_timestamp = self.body.get("submitted_at")

                # TODO: Note - if the existing submission status = passed then we aren't going to change it...
                #    This means that if the student submits a later attempt, and then fails, we won't update the status
                #    it also means that if an instructor accidentally grades a student as passing and then changes
                #    it back to failing, we won't update the status...

                # TODO: commenting this out to work around SKillways sending submission-events after the grade_change
                # submission_from_db.status = (
                #     submission_status
                #     if not submission_from_db.status == AssessmentSubmissionStatus("Passed")
                #     else submission_from_db.status
                # )
                # self.psql_services.psql_engine.session.flush()  # TODO: verify swapping this commit/flush works...
                self.psql_services.psql_engine.session.commit()

        # self.psql_services.psql_engine.session.commit()

        # Check if this is the last summative assignment of the course, if so, enroll in next course, if exists
        if assignment_from_db.is_last_summative_of_course:
            self.logger.info(f"Attempting to enroll in next course for user {self.user_info['user_id_local']}...")
            current_course_id = self._convert_global_to_local_id(self.metadata["context_id"])
            ccc_id = self.user_info["user_sis_id"]
            canvas_user_id = self.user_info["user_id_local"]
            self.canvas_services.create_next_course_enrollment(
                current_course_id=current_course_id, ccc_id=ccc_id, canvas_user_id=canvas_user_id
            )

    def update_progress(self):
        """
        This function is used to update the course progress in both the Database and Salesforce for a student.
        - It will calculate the course progress from the database, and update the enrollment table with the progress
        - It will also go to Salesforce and update the progress of the current course from the event.
        Returns: None

        """
        program_progress = self.psql_services.update_program_progress(lms_id=self.user_info["user_id_local"])
        course_progress = self.psql_services.calculate_progress(
            lms_id=self.user_info["user_id_local"],
            progress_type="course",
            course_lms_id=self.event_info["context_id_local"],
        )

        self.logger.debug(f"Course progress for user: {course_progress}")
        self.logger.debug(f"Program progress for user: {program_progress}")
        if course_progress and course_progress.get("percentage"):
            self.logger.info(f"Updating course progress in Salesforce for user {self.user_info['user_id_local']}...")
            email = self.user_info.get("user_login")
            course_id = self.event_info.get("context_id_local")
            course_code = self.psql_services.get_course_code_by_lms_id(course_id)
            self.sf_services.update_course_progress(
                email=email, course_code=course_code, progress=course_progress.get("percentage")
            )

            course_id = self.event_info.get("context_id_local")
            ccc_id = self.user_info.get("user_sis_id")
            self.psql_services.update_ect_progress(
                ccc_id=ccc_id, course_id=course_id, progress=course_progress.get("percentage")
            )

    def process_login_event(self):
        """
        This function is used to process a login event from Canvas. It will:
        - Set the first login timestamp in the database (enrollment table) if it is not already set
        - Update the last login timestamp in the database (enrollment table) if the event time is greater than
            the current last login
        -
        Returns: dict: A dictionary with the keys 'first_lms_login_updated' and 'last_lms_login_updated' with boolean

        """
        first_lms_login_updated = False
        last_lms_login_updated = False
        student_enrollment = self.psql_services.get_student_enrollment(lms_id=self.user_info["user_id_local"])
        if student_enrollment.first_lms_login is None:
            self.logger.info(f"Setting first LMS login in database for user {self.user_info['user_id_local']}")
            student_enrollment.first_lms_login = self.event_info["event_time"]
            first_lms_login_updated = True
        try:
            last_lms_login = student_enrollment.last_lms_login.replace(tzinfo=datetime.timezone.utc)
        except AttributeError:
            last_lms_login = None
        if not last_lms_login or self.event_info["event_time"] > last_lms_login:
            self.logger.info(f"Setting last LMS login in database for user {self.user_info['user_id_local']}")
            student_enrollment.last_lms_login = self.event_info["event_time"]
            last_lms_login_updated = True
        self.psql_services.psql_engine.session.commit()

        return {"first_lms_login_updated": first_lms_login_updated, "last_lms_login_updated": last_lms_login_updated}

    def process_non_saa_activity_event(self, activity_type: Literal["login", "asset", "conversation"]):
        # TODO: Need to implement more of this function still.
        #  This will be used to process non-SAA activities like logins, asset access, and conversations.
        #  It will write them to the 'event' table.
        #  The login updates to the enrollment table are already handled in the process_login_event function.
        if activity_type == "login":
            self.process_login_event()
            return self.sf_services.update_last_lms_timestamp(
                email=self.user_info["user_login"], timestamp=self.event_info["event_time"]
            )
        elif activity_type == "asset":
            return True
        elif activity_type == "conversation":
            return True
