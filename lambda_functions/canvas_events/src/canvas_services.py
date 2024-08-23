import asyncio

from propus.canvas import Canvas
from propus.helpers.canvas import create_subsequent_course_enrollment
from propus.logging_utility import Logging


class CanvasServices:
    """
    This class is responsible for handling all the canvas related services, e.g. creating a new course enrollment
    """

    def __init__(self, canvas_engine: Canvas, postgres_engine):
        """
        Initialize the canvas services object
        Args:
            canvas_engine: The Propus Canvas object
            postgres_engine: The Propus Calbright Postgres object
        """
        self.logger = Logging.get_logger(
            "castor/lambda_functions/canvas_events/canvas_event_system/canvas_services", debug=True
        )
        self.canvas_engine = canvas_engine
        self.postgres_engine = postgres_engine

    @staticmethod
    def _get_first_result(results):
        """
        Get the first result from a list of results. Just a helper function.
        Args:
            results: The list of results

        Returns: The first result if it exists, otherwise None

        """
        return results[0] if results else None

    def create_next_course_enrollment(self, current_course_id: str, ccc_id: str, canvas_user_id: str):
        """
        Create a subsequent course enrollment for a user.
        - This is a wrapper around the create_subsequent_course_enrollment function in the propus.helpers.canvas module
        Args:
            current_course_id: The current course id, for example the course from the Canvas event
            ccc_id: The ccc_id of the user
            canvas_user_id: The canvas user id

        Returns: a boolean indicating if the student was enrolled in a next course

        """
        self.logger.info(
            f"Attempting to create subsequent course enrollment for user {canvas_user_id} after "
            f"course {current_course_id}"
        )
        return create_subsequent_course_enrollment(
            current_course_id, ccc_id, canvas_user_id, self.postgres_engine.session, self.canvas_engine
        )

    def get_first_assignment_submission(self, assignment_id: str, user_id: str, course_id: str):
        """
        Get the first submission attempt for an assignment from the Canvas REST API
        Args:
            assignment_id: The Canvas assignment id
            user_id: The Canvas user id
            course_id: The Canvas course id

        Returns: The first submission attempt if it exists, otherwise None

        """
        self.logger.info(
            f"Getting first submission attempt for assignment {assignment_id} for user {user_id}"
            f" in course {course_id}"
        )
        assignment = self._get_first_result(
            asyncio.run(
                self.canvas_engine.get_single_submission(
                    object_type="course",
                    object_id=course_id,
                    assignment_id=assignment_id,
                    user_id=user_id,
                    include=["submission_history"],
                )
            )
        )
        for submission in assignment.get("submission_history", []):
            if submission.get("attempt") == 1:
                return submission
        # TODO: There is something happening with skillways where it's wiping out the first attempt.
        #   SO here I'm gonna re-loop through it and just grab ANY attempt that exists if we don't have an attempt 1
        #   we could also refactor to look through and grab the lowest attempt...
        for submission in assignment.get("submission_history", []):
            return submission
