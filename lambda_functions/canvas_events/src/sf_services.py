import datetime
from propus.logging_utility import Logging
from propus.salesforce import Salesforce

from src.exceptions import InvalidFinalGrade


class SFServices:
    """
    This class provides methods to interact with Salesforce.
    """

    def __init__(self, sf_client: Salesforce):
        """
        Initialize the Salesforce services object
        Args:
            sf_client: The Propus Salesforce object
        """
        self.logger = Logging.get_logger("castor/lambda_functions/canvas_events/src/sf_services", debug=True)
        self.sf_client = sf_client

    def _convert_sf_datetime(self, sf_datetime: str):
        """
        Convert a Salesforce datetime string to a Python datetime object
        Args:
            sf_datetime: The Salesforce datetime string, for example '2021-09-01T00:00:00.000Z'

        Returns: datetime: The Python datetime object

        """
        self.logger.debug(f"Converting Salesforce datetime {sf_datetime} to Python datetime")
        if not sf_datetime:
            return None
        sf_datetime_adjusted = sf_datetime[:-2] + ":" + sf_datetime[-2:]
        return datetime.datetime.fromisoformat(sf_datetime_adjusted)

    def get_contact_id(self, email: str):
        """
        Get the Salesforce contact ID for a given email address
        Args:
            email: str: The Calbright email address of the contact

        Returns: str: The Salesforce contact ID if it exists, otherwise None

        """
        self.logger.debug(f"Getting Salesforce contact ID for {email}")
        query = f"""SELECT id FROM Contact WHERE cfg_Calbright_Email__c = '{email}' AND LMS__c ='Canvas'"""
        response = self.sf_client.custom_query(query)
        return None if response.get("totalSize") == 0 else response.get("records")[0].get("Id")

    def get_contact_field(self, email: str, sf_field: str):
        """
        Get a single contact field for a given email address
        Args:
            email: str: The Calbright email address of the contact
            sf_field: str: The Salesforce field to retrieve, for example 'Last_Strut_SAA_Timestamp__c'

        Returns: datetime: The field if it exists, otherwise None

        """
        # self.logger.debug(f"Getting {sf_field} for {email}")
        # contact_id = self.get_contact_id(email)
        # if contact_id:
        #     query = f"""SELECT {sf_field} FROM Contact WHERE Id = '{contact_id}'"""
        #     response = self.sf_client.custom_query(query)
        #     if response.get("totalSize") != 0:
        #         timestamp = response.get("records")[0].get(f"{sf_field}")
        #         return self._convert_sf_datetime(timestamp)
        # return None
        # TODO: verify this works after updating...
        self.logger.debug(f"Getting {sf_field} for {email}")
        query = f"""SELECT {sf_field} FROM Contact WHERE cfg_Calbright_Email__c = '{email}' AND LMS__c ='Canvas'"""
        response = self.sf_client.custom_query(query)
        if response.get("totalSize") != 0:
            timestamp = response.get("records")[0].get(f"{sf_field}")
            return self._convert_sf_datetime(timestamp)
        return None

    def convert_event_timestamp_to_sf_datetime(self, event_timestamp: datetime.datetime):
        """
        Convert a Python datetime object to a Salesforce datetime string
        Args:
            event_timestamp: datetime.datetime: The Python datetime object

        Returns: str: The Salesforce datetime string, for example '2021-09-01T00:00:00.000Z'

        """
        self.logger.debug(f"Converting Python datetime {event_timestamp} to Salesforce datetime")
        return event_timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def update_contact_saa_timestamp(self, email: str, timestamp: datetime.datetime):
        """
        Update the Last_Strut_SAA_Timestamp__c for a given email address
        Args:
            email: str: The Calbright email address of the contact
            timestamp: datetime.datetime: The timestamp to update

        Returns: bool: True if the timestamp was updated successfully, False otherwise

        """
        self.logger.info(f"Updating Last_Strut_SAA_Timestamp__c for {email} to {timestamp}")
        contact_id = self.get_contact_id(email)
        if not contact_id:
            return False
        formatted_date = self.convert_event_timestamp_to_sf_datetime(timestamp)
        self.sf_client.update_contact_record(salesforce_id=contact_id, Last_Strut_SAA_Timestamp__c=formatted_date)
        return True

    def get_courses(self, contact_id: str):
        """
        This function returns a dictionary of the courses from the SF contact object.
        Args:
            contact_id: The Salesforce contact ID

        Returns: dict: A dictionary of the courses from the SF contact object, with the course number as the key and
            the course code as the value. For example, {1: 'BUS500', 2: 'BUS501', 3: None}
        """
        self.logger.debug(f"Getting courses for {contact_id}")
        query = f"""SELECT Course_1__c, Course_2__c, Course_3__c FROM Contact WHERE Id = '{contact_id}'"""
        response = self.sf_client.custom_query(query)
        return (
            {
                1: response.get("records")[0].get("Course_1__c"),
                2: response.get("records")[0].get("Course_2__c"),
                3: response.get("records")[0].get("Course_3__c"),
            }
            if response.get("totalSize") != 0
            else None
        )

    def update_course_progress(self, email: str, course_code: str, progress: float):
        """
        This function updates the course progress in Salesforce for a given course code and student.
        Args:
            email: str: the email address of the student
            course_code: str: The course code of the course, for example 'BUS500' or 'BUS501'
            progress: float: The progress of the student in the course, for example 0.5 for 50%

        Returns: bool: True if the course progress was updated successfully, False otherwise
        """
        contact_id = self.get_contact_id(email)
        courses_from_sf = self.get_courses(contact_id=contact_id)

        for k, v in courses_from_sf.items():
            if v == course_code:
                course_field = f"Course_{k}_Progress__c"
                formatted_progress = int(progress * 100)
                self.logger.info(f"Updating course progress for {email} in {course_code} to {progress}")
                self.sf_client.update_contact_record(salesforce_id=contact_id, **{course_field: formatted_progress})
                return True
        return False

    def update_course_completed(self, email: str, course_code: str):
        """
        This function updates the course completion status in Salesforce for a given course code and student.
        Args:
            email: str: the email address of the student
            course_code: str: The course code of the course, for example 'BUS500' or 'BUS501'

        Returns: bool: True if the course completion status was updated successfully, False otherwise

        """

        contact_id = self.get_contact_id(email)
        courses_from_sf = self.get_courses(contact_id=contact_id)

        for k, v in courses_from_sf.items():
            if v == course_code:
                course_field = f"Completed_Course_{k}__c"
                self.logger.debug(f"Updating course completion status for {email} in {course_code} | {course_field}")
                self.sf_client.update_contact_record(salesforce_id=contact_id, **{course_field: True})
                return True
        return False

    def update_last_lms_timestamp(self, email: str, timestamp: datetime.datetime):
        """
        Update the Last_LMS_Timestamp__c for a given email address
        Args:
            email: str: The Calbright email address of the contact
            timestamp: datetime.datetime: The timestamp to update

        Returns: bool: True if the timestamp was updated successfully, False otherwise

        """
        self.logger.debug(f"Checking Last_Strut_Activity_Timestamp__c for {email} to {timestamp}")
        contact_id = self.get_contact_id(email)
        formatted_date = self.convert_event_timestamp_to_sf_datetime(timestamp)

        if contact_id:
            last_lms_timestamp = self.get_contact_field(email=email, sf_field="Last_Strut_Activity_Timestamp__c")
            if last_lms_timestamp is None or timestamp > last_lms_timestamp:
                self.logger.info(f"Updating Last_Strut_Activity_Timestamp__c for {email} to {timestamp}")
                self.sf_client.update_contact_record(
                    salesforce_id=contact_id, Last_Strut_Activity_Timestamp__c=formatted_date
                )
            return True
        return False

    def update_eotg(self, grade_id, grade, grade_timestamp):
        """
        Update an end of term grade record on Salesforce.
        Args:
            grade_id (str): The ID of the grade record to update.
            grade (str): The grade to update
            grade_date (datetime): The grade date to update

        Returns:
            None
        """

        if grade not in ("P", "NP"):
            raise InvalidFinalGrade(grade)

        self.logger.info(f"Updating end of term grade {grade_id} to {grade} on {grade_timestamp}")
        formatted_timestamp = self.convert_event_timestamp_to_sf_datetime(grade_timestamp)
        self.sf_client.update_end_of_term_grade(
            grade_id,
            Grade__c=grade,
            Date_Grade_Submitted__c=formatted_timestamp,
            Status__c="SUBMITTED",
        )
        return True

    def update_learner_status(self, email, status):
        """
        Update the learner status on Salesforce.
        Args:
            email (str): The email address of the learner
            status (str): The status to update

        Returns:
            None
        """
        self.logger.info(f"Updating Salesforce learner status for {email} to {status}")
        contact_id = self.get_contact_id(email)
        self.sf_client.update_contact_record(salesforce_id=contact_id, cfg_Learner_Status__c=status)
        return True
