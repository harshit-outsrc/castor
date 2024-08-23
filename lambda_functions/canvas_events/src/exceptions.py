class UnknownCanvasEventType(Exception):
    def __init__(self, event_type):
        super().__init__(f'Canvas event type "{event_type}" unrecognized')


class AssigmentNotFoundInDatabase(Exception):
    def __init__(self, canvas_id):
        super().__init__(f'Assignment with canvas_id "{canvas_id}" not found in database')


class UserNotFoundInDatabase(Exception):
    def __init__(self, user_id):
        super().__init__(f'User with canvas or ccd_id "{user_id}" not found in database')


class EnrollmentNotFoundInDatabase(Exception):
    def __init__(self, canvas_id):
        super().__init__(f'Active enrollment for user with canvas_id "{canvas_id}" not found in database')


class InvalidFinalGrade(Exception):
    def __init__(self, final_grade):
        super().__init__(f'Invalid final grade "{final_grade}"')


class MissingGraderId(Exception):
    def __init__(self):
        super().__init__("Grader ID is missing")


class NoUserInfoInEvent(Exception):
    def __init__(self):
        super().__init__("No user info in event")


class NoSubmissionFound(Exception):
    def __init__(self):
        super().__init__("No submission found")


class NoSubmissionTimestamp(Exception):
    def __init__(self):
        super().__init__("No submission timestamp found")


class CourseNotFoundInDatabase(Exception):
    def __init__(self, course_id):
        super().__init__(f'Course with canvas_id "{course_id}" not found in database')
