import unittest
from unittest.mock import MagicMock, Mock

from propus.calbright_sql.user import User

from propus.calbright_sql.staff import Staff  # noqa:F401
from propus.calbright_sql.student import Student
from propus.calbright_sql.learner_status import LearnerStatus

from exceptions import MissingRequiredField, UnknownCalendlyEventType, CalbrightEmailNotInDatabase
from events.calendly_event import CalendlyEvent, EventTypeUUID


class TestCalendlyEvents(unittest.TestCase):
    def setUp(self):
        self.calendly_event_name = "EVENT NAME"
        calendly = MagicMock()
        calendly.fetch_event_type = Mock(
            return_value={
                "resource": {"pooling_type": "Round Robin", "name": self.calendly_event_name, "slug": "Banana"}
            }
        )

        calbright = MagicMock()
        calbright.session.execute = Mock(side_effect=self.session_execute)

        salesforce = MagicMock()
        salesforce.client.update_contact_record = Mock(side_effect=self.sf_update_contact_record)
        salesforce.client.create_event = Mock(side_effect=self.sf_create_event)
        salesforce.get_calbright_user_by_email = Mock(return_value=None)

        self.calendly_event = CalendlyEvent(configs={}, salesforce=salesforce, calendly=calendly, calbright=calbright)
        logger = MagicMock()
        logger.warning = Mock(side_effect=self.logger_warn)
        self.calendly_event.logger = logger

        self.return_learner_status_id = "NEW LEARNER STATUS"
        self.user_email = "prof@calbright.org"
        self.user_id = "fc6e51473b30"
        self.crm_event = f"https://api.calendly.com/event_types/{EventTypeUUID.CRM.value}"
        self.c_event_type = f"https://api.calendly.com/event_types/{EventTypeUUID.DATA_ANALYSIS.value}"
        self.student_email = "testy.tersterson@calbrightcollege.org"
        self.salesforce_id = "sf_123155"
        self.start_time = "2023-07-21T00:30:00.000000Z"
        self.student_record = User(
            id="UUID_LONG_ID",
            calbright_email=self.student_email,
            student=Student(ccc_id="CCC1234"),
            learner_status=LearnerStatus(status="App Submitted"),
            salesforce_id=self.salesforce_id,
        )
        self.invitee_created_event = {
            "event": "invitee.created",
            "payload": {
                "email": self.student_email,
                "scheduled_event": {
                    "event_type": self.c_event_type,
                    "start_time": self.start_time,
                    "location": {"location": "Online!"},
                    "event_memberships": [{"user": self.c_event_type, "user_email": self.user_email}],
                },
                "text_reminder_number": "123-456-7890",
                "created_at": "2023-07-18T20:16:16.000000Z",
                "questions_and_answers": [{"question": "What is your name", "answer": "Castor"}],
            },
        }
        self.invitee_canceled_event = {
            "event": "invitee.canceled",
            "payload": {
                "email": self.student_email,
                "scheduled_event": {
                    "event_type": self.c_event_type,
                    "start_time": self.start_time,
                    "location": {"location": "Online!"},
                    "event_memberships": [{"user": self.c_event_type, "user_email": self.user_email}],
                },
                "text_reminder_number": "123-456-7890",
                "created_at": "2023-07-18T20:16:16.000000Z",
                "questions_and_answers": [{"question": "What is your name", "answer": "Castor"}],
            },
        }
        self.warn_logged = False
        self.sf_updated = False
        self.ef_event_created = False

    def test_required_fields(self):
        event = {"event": "invitee.created"}
        payload = {}
        for field in self.calendly_event._invitee_created_required_fields:
            with self.assertRaises(MissingRequiredField) as err:
                self.calendly_event.run(event | {"payload": payload})
            self.assertEqual(
                str(err.exception),
                f'Event type "calendly_event" is missing or size is 0 for the required field: {field}',
            )
            payload[field] = field

        payload["scheduled_event"] = {"a": "b"}
        for field in self.calendly_event._scheduled_event_required_fields:
            with self.assertRaises(MissingRequiredField) as err:
                self.calendly_event.run(event | {"payload": payload})
            self.assertEqual(
                str(err.exception),
                f'Event type "calendly_event" is missing or size is 0 for the required field: {field}',
            )
            payload["scheduled_event"][field] = field

        payload = {"event": "invitee.canceled"}
        for field in self.calendly_event._invitee_canceled_required_fields:
            with self.assertRaises(MissingRequiredField) as err:
                self.calendly_event.run(event | {"payload": payload})
            self.assertEqual(
                str(err.exception),
                f'Event type "calendly_event" is missing or size is 0 for the required field: {field}',
            )
            payload[field] = field

        with self.assertRaises(UnknownCalendlyEventType) as err:
            self.calendly_event.run({"event": "unknown_event"})
        self.assertEqual(str(err.exception), 'Calendly Event type "unknown_event" unrecognized')

        self.assertIsNone(self.calendly_event.run({"event": "routing_form_submission.created"}))

    def logger_warn(self, stmt):
        if self.test_name == "unknown_event_type":
            self.assertEqual(stmt, "calandly/invitee_created https://blash/bjaksd.com/BLAHBLHABKHAJS not recognized")
            self.warn_logged = True
        elif self.test_name == "_incorrect_ccc_id_is_none":
            self.assertEqual(
                stmt,
                "Invalid Data: learner_status=App Submitted, ccc_id=None email=testy.tersterson@calbrightcollege.org",
            )
            self.warn_logged = True
        elif self.test_name == "_incorrect_learner_status":
            self.assertEqual(
                stmt, "Invalid Data: learner_status=EPP, ccc_id=CCC1234 email=testy.tersterson@calbrightcollege.org"
            )
            self.warn_logged = True

    def test_invitee_created_errors(self):
        self.test_name = "unknown_event_type"
        err_uuid = "https://blash/bjaksd.com/BLAHBLHABKHAJS"
        payload = {
            "event": "invitee.created",
            "payload": {
                "email": "you@calbrightcollege.org",
                "scheduled_event": {
                    "event_type": err_uuid,
                    "start_time": "2023-07-21T00:30:00.000000Z",
                    "location": {"location": "Online!"},
                },
            },
        }
        self.calendly_event.run(payload)
        self.assertTrue(self.warn_logged)

        self.test_name = "invalid_calbright_email"
        payload["payload"]["scheduled_event"]["event_type"] = self.c_event_type
        with self.assertRaises(CalbrightEmailNotInDatabase) as err:
            self.calendly_event.run(payload)
        self.assertEqual(str(err.exception), "Calbright Email you@calbrightcollege.org was not found in database")

        self.calendly_event.store_event_in_salesforce = Mock(return_value=True)
        self.warn_logged = False
        self.test_name = "student_only_incorrect_ccc_id_is_none"
        self.student_record.student.ccc_id = None
        self.calendly_event.run(self.invitee_created_event)
        self.assertTrue(self.warn_logged)

        self.warn_logged = False
        self.test_name = "student_only_incorrect_learner_status"
        self.student_record.student.ccc_id = "CCC1234"
        self.student_record.learner_status.status = "EPP"
        self.calendly_event.run(self.invitee_created_event)
        self.assertTrue(self.warn_logged)

    def test_invitee_crm_created_flow(self):
        self.test_name = "student_only_crm_event_created"
        self.invitee_created_event["payload"]["scheduled_event"]["event_type"] = self.crm_event
        self.calendly_event.run(self.invitee_created_event)
        self.assertTrue(self.sf_updated)
        self.assertEqual(self.calendly_event.student_record.learner_status.id, self.return_learner_status_id)

    def test_invitee_created_flow(self):
        self.test_name = "student_only_app_submitted"
        self.invitee_created_event["payload"]["scheduled_event"]["event_type"] = self.c_event_type
        self.calendly_event.run(self.invitee_created_event)
        self.assertTrue(self.sf_updated)
        self.assertEqual(self.calendly_event.student_record.learner_status.id, self.return_learner_status_id)

    def test_invitee_canceled_flow(self):
        self.test_name = "student_only_invitee.canceled"
        self.calendly_event.run(self.invitee_canceled_event)
        self.assertTrue(self.ef_event_created)

    def session_execute(self, *args, **kwargs):
        resp = MagicMock()
        self.session_executed = True
        if "student_only" in self.test_name:
            resp.scalars().all = Mock(return_value=[self.student_record])
            self.test_name = self.test_name.replace("student_only", "")
        else:
            resp.scalar_one.return_value = LearnerStatus(id=self.return_learner_status_id)
        return resp

    def sf_update_contact_record(self, sf_id, Cfg_Learner_Status__c):
        self.assertEqual(sf_id, self.salesforce_id)
        if self.test_name == "_crm_event_created":
            self.assertEqual("Ready for Onboarding", Cfg_Learner_Status__c)
            self.sf_updated = True
        elif self.test_name == "_app_submitted":
            self.assertEqual("Started Orientation", Cfg_Learner_Status__c)
            self.test_name = "_app_submitted1"
        elif self.test_name == "_app_submitted1":
            self.assertEqual("Completed Orientation", Cfg_Learner_Status__c)
            self.sf_updated = True

    def sf_create_event(self, **kwargs):
        self.assertEqual(kwargs.get("salesforce_id"), self.salesforce_id)
        if "created" in self.test_name:
            self.assertEqual(kwargs.get("start_time"), self.start_time)
            self.assertEqual(kwargs.get("type"), "One-on-One")
            self.assertEqual(kwargs.get("subject"), f"Scheduled: {self.calendly_event_name}")
            self.assertEqual(
                kwargs.get("description"),
                "EVENT NAME (Banana)\n---\nQ&A:\nWhat is your name\n - Castor\n---\nScheduled at: 2023-07-18T13:16:16.0"
                "00000Z\nText Reminder: 123-456-7890\nLocation: Online!\nEvent Kind: Round robin",
            )
        self.ef_event_created = True
        return {"id": "event_id"}


if __name__ == "__main__":
    unittest.main()
