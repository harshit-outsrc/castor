from datetime import datetime
import unittest
from unittest.mock import MagicMock, Mock, patch

from propus.calbright_sql.staff import Staff
from propus.calbright_sql.course_version import CourseVersion
from propus.calbright_sql.course import Course
from propus.calbright_sql.user import User
from propus.calbright_sql.enrollment import Enrollment
from propus.calbright_sql.student import Student
from propus.calbright_sql.term import Term
from propus.calbright_sql.enrollment_course_term import EnrollmentCourseTerm

from exceptions import MissingRequiredField
from events.sp_term_certified import SpTermGradeCertified, MissingEnrollmentCourseTermInDB, MissingTermInDB
from sqlalchemy.exc import NoResultFound


class TestSpTermCertified(unittest.TestCase):
    def setUp(self):
        self.calbright = MagicMock()
        self.calbright.session.execute = Mock(side_effect=self.session_execute)

        self.salesforce = MagicMock()

        self.sp_term_event = SpTermGradeCertified(configs={}, salesforce=self.salesforce, calbright=self.calbright)
        self.ect_id = "ECT_1235"
        self.sf_id = "TEST_12343"
        self.course_code = "CS101"
        self.ccc_id = "CC1243"
        self.instructor_id = "asnjdkasnjkn123124123"
        self.end_date = datetime(2024, 7, 1)
        self.progress = 97.897
        self.enrollment_course_term = EnrollmentCourseTerm(
            id=self.ect_id,
            grade_salesforce_id=self.sf_id,
            term=Term(end_date=self.end_date),
            enrollment=Enrollment(ccc_id=self.ccc_id, student=Student(user=User(salesforce_id=self.sf_id))),
            course_version=CourseVersion(course=Course(course_code=self.course_code)),
            instructor=Staff(user=User(salesforce_id=self.instructor_id)),
            progress=self.progress,
        )
        self.test_payload = {"salesforce_grade_id": self.sf_id, "enrollment_course_term_id": self.ect_id}
        self.term_name = "TERM_NAME_2024"
        self.term_id = "TERM_ID_1234"
        self.term_sf_response = {"Name": self.term_name, "Id": self.term_id}
        self.test_name = None
        self.sf_updated = False
        self.eotg_created = False
        self.dp_upsert_eotg = False

    def test_required_fields(self):
        payload = {}
        for field in self.sp_term_event._required_fields:
            with self.assertRaises(MissingRequiredField) as err:
                self.sp_term_event.run(payload)
            self.assertEqual(
                str(err.exception),
                f'Event type "sp_term_grade_certified" is missing or size is 0 for the required field: {field}',
            )
            payload[field] = field

    def test_run_errors(self):
        self.test_name = "missing_grade"
        with self.assertRaises(MissingEnrollmentCourseTermInDB) as err:
            self.sp_term_event.run(self.test_payload)
        self.assertEqual(
            str(err.exception),
            "grade not found in database {'salesforce_grade_id': 'TEST_12343', 'enrollment_course_term_id': 'ECT_1235'}",  # noqa: E501
        )

        self.test_name = "missing_term"
        with self.assertRaises(MissingTermInDB) as err:
            self.sp_term_event.run(self.test_payload)
        self.assertEqual(
            str(err.exception),
            "term not found in database {'salesforce_grade_id': 'TEST_12343', 'enrollment_course_term_id': 'ECT_1235'}",
        )

    @patch("events.sp_term_certified.upsert_eotg_records")
    def test_successful_run(self, mock_upsert_eotg_records):
        enrollment_course_term = EnrollmentCourseTerm(progress=0)
        mock_upsert_eotg_records.return_value = [enrollment_course_term, None]
        self.salesforce.get_next_term = Mock(side_effect=self.sf_term_req)
        self.salesforce.client.update_contact_record = Mock(side_effect=self.sf_update_contact_record)
        self.salesforce.client.create_end_of_term_grade = Mock(side_effect=self.sf_create_end_of_term_grade)
        self.sp_term_event.run(self.test_payload)

        mock_upsert_eotg_records.assert_called_once()
        self.assertTrue(self.sf_updated)
        self.assertTrue(self.eotg_created)
        self.assertEqual(enrollment_course_term.progress, self.progress)
        self.calbright.session.commit.assert_called_once()

    def sf_term_req(self, term_date):
        self.assertEqual(term_date, "2024-07-02T00:00:00.000000Z")
        return self.term_sf_response

    def sf_update_contact_record(self, sf_id, Current_Term__c):
        self.assertEqual(sf_id, self.sf_id)
        self.assertEqual(Current_Term__c, self.term_id)
        self.sf_updated = True

    def sf_create_end_of_term_grade(self, course, ccc_id, sf_id, term_id, term_name, instructor_id):
        self.assertEqual(course, self.course_code)
        self.assertEqual(ccc_id, self.ccc_id)
        self.assertEqual(sf_id, self.sf_id)
        self.assertEqual(term_id, self.term_id)
        self.assertEqual(term_name, self.term_name)
        self.assertEqual(instructor_id, self.instructor_id)
        self.eotg_created = True
        return {"id": "new_grade"}

    def session_execute(self, *args, **kwargs):
        scalar_one = MagicMock()
        self.session_executed = True
        if self.test_name == "missing_grade" or self.test_name == "missing_term_1":
            scalar_one.scalar_one.side_effect = Mock(side_effect=NoResultFound("Test"))
        else:
            if self.test_name == "missing_term":
                self.test_name = "missing_term" + "_1"
            scalar_one.scalar_one.return_value = self.enrollment_course_term
        return scalar_one


if __name__ == "__main__":
    unittest.main()
