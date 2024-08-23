import unittest
from unittest.mock import MagicMock, Mock

from unittest.mock import patch
from sqlalchemy.exc import NoResultFound
from propus.calbright_sql.expressed_interest import LeadSource

from events.hubspot_form_submitted import HubspotFormSubmitted
from exceptions import MissingRequiredField


class TestEventHubspotFormSubmission(unittest.TestCase):
    def setUp(self):
        hubspot = MagicMock()
        hubspot.send_transactional_email = Mock()
        self.salesforce = MagicMock()

        session = MagicMock()
        session.execute = Mock(side_effect=self.session_execute)
        session.add = Mock(side_effect=self.session_add)
        session.flush = Mock()
        session.commit = Mock()
        self.calbright = MagicMock()
        self.calbright.session = session

        self.program_interest = Mock()
        self.program_interest.short_name = "Cybersecurity"

        self.hubspot_form_submitted = HubspotFormSubmitted(
            configs={}, ssm=None, salesforce=self.salesforce, hubspot=hubspot, calbright=self.calbright
        )
        self.user_id = "USER_1234_ABC"
        self.test_data = {
            "properties": {
                "email": {"value": "sergio.renhe@calbright.org"},
                "program_of_interest": {"value": "Data Analysis"},
                "state_dropdown": {"value": "DROP_DOWN_CA"},
                "user_agent": {"value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7"},
                "I agree to receive text updates from Calbright College.": {"value": False},
                "browser_type": "Mobile",
                "handl_landing_page": {"value": "http://google.com"},
                "hs_latest_source": {"value": "Radio"},
                "utm_medium": {"value": "UTM_MEDIUM"},
                "utm_term": {"value": "UTM_TERM"},
                "utm_source": {"value": "UTM_SOURCE"},
                "utm_content": {"value": "UTM_CONTENT"},
                "utm_campaign": {"value": "UTM_CAMPAIGN"},
                "handl_original_url": {"value": "http://calbright.org"},
                "ip__c": {"value": "123.456.7890"},
                "phone": {"value": "1234567"},
                "firstname": {"value": "testerson"},
                "lastname": {"value": "mctest"},
                "hs_calculated_form_submissions": {"value": "f0842358-1fe4-45c0-a823-769157308c95::1719936831107"},
            },
        }
        self.session_added = False
        self.session_executed = False

    def test_required_fields(self):
        payload = {}
        for field in self.hubspot_form_submitted._required_fields:
            with self.assertRaises(MissingRequiredField) as err:
                self.hubspot_form_submitted.run(payload)
            self.assertEqual(
                str(err.exception),
                f'Event type "hubspot_forms_submission" is missing or size is 0 for the required field: {field}',
            )
            payload[field] = None
        props = {}
        for p in self.hubspot_form_submitted._required_properties:
            with self.assertRaises(MissingRequiredField) as err:
                self.hubspot_form_submitted._check_required_properties(props)
            self.assertEqual(
                str(err.exception),
                f'Event type "hubspot_forms_submission" is missing or size is 0 for the required field: {p}',
            )
            props[p] = {"value": p}

    def test_get_browser_type(self):
        self.test_name = "get_browser_type"
        mobile_platforms = [
            "/Mobile",
            "iPhone",
            "iPod",
            "iPad",
            "Android",
            "BlackBerry",
            "IEMobile",
            "Kindle",
            "NetFront",
            "Silk-Accelerated",
            "hpwOS",
            "webOS",
            "Fennec",
            "Minimo",
            "Opera Mobi",
            "Opera Mini",
            "Blazer",
            "Dolfin",
            "Dolphin",
            "Skyfire",
            "Zune/",
        ]
        for p in mobile_platforms:
            self.assertEqual(self.hubspot_form_submitted.get_browser_type(p), "Mobile")

        self.assertEqual(self.hubspot_form_submitted.get_browser_type("Desktop"), "Desktop")

    def test_create_expressed_interest_record(self):
        self.test_name = "create_expressed_interest"
        self.express_interest_patcher = patch("events.hubspot_form_submitted.ExpressInterest")
        self.program_patcher = patch("events.hubspot_form_submitted.Program")
        self.select_patcher = patch("events.hubspot_form_submitted.select")
        self.ExpressInterest = self.express_interest_patcher.start()
        self.Program = self.program_patcher.start()
        self.select = self.select_patcher.start()
        properties = self.test_data.get("properties")
        expressed_interest_args = {
            "user_id": self.user_id,
            "state_declared": properties.get("state_dropdown", {}).get("value"),
            "browser_type": properties.get("browser_type"),
            "landing_page": properties.get("handl_landing_page", {}).get("value"),
            "lead_source": LeadSource(properties.get("hs_latest_source", {}).get("value")),
            "utm_medium": properties.get("utm_medium", {}).get("value"),
            "utm_term": properties.get("utm_term", {}).get("value"),
            "utm_source": properties.get("utm_source", {}).get("value"),
            "utm_content": properties.get("utm_content", {}).get("value"),
            "utm_campaign": properties.get("utm_campaign", {}).get("value"),
            "referrer_url": properties.get("handl_original_url", {}).get("value"),
            "ip_address": properties.get("ip__c", {}).get("value"),
            "program_name": "Cybersecurity",
            "program_interest": self.program_interest,
        }
        expressed_interest = MagicMock()
        for key, value in expressed_interest_args.items():
            setattr(expressed_interest, key, value)
        expressed_interest.args = [expressed_interest]
        self.ExpressInterest.return_value = expressed_interest
        self.hubspot_form_submitted.create_expressed_interest_record(
            user_id=self.user_id, properties=self.test_data.get("properties")
        )
        self.assertTrue(self.session_added)
        self.express_interest_patcher.stop()
        self.program_patcher.stop()
        self.select_patcher.stop()

    def test_sms_opt_in(self):
        self.test_name = "sms_opt_in"
        # Applicant didn't check SMS Opt-in: Set Opt-out to True
        self.test_data["properties"]["sms_opt_in"] = {"value": "false"}
        self.hubspot_form_submitted.run(self.test_data)
        self.hubspot_form_submitted.salesforce.client.update_contact_record.assert_called()

    def test_sms_opt_out(self):
        self.test_name = "sms_opt_out"
        # Applicant checked SMS Opt-in: Set Opt-out to False
        self.test_data["properties"]["sms_opt_in"] = {"value": "true"}
        self.hubspot_form_submitted.run(self.test_data)
        self.assertTrue(
            self.hubspot_form_submitted.salesforce.client.update_contact_record.call_args.kwargs["SMS_Opt_Out__c"]
        )

    def test_update_learner_status_to_app_submitted(self):
        self.test_name = "update_learner_status_to_app_submitted"
        # Expected outcome: Learner status is updated to "App Submitted"
        self.hubspot_form_submitted.run(self.test_data)
        self.hubspot_form_submitted.salesforce.client.update_contact_record.assert_called_once()

    def test_send_email_ready_for_onboarding(self):
        self.test_name = "send_email_ready_for_onboarding"
        # Expected outcome: Email is sent to contact
        self.hubspot_form_submitted.run(self.test_data)
        self.hubspot_form_submitted.hubspot.send_transactional_email.assert_called_once()

    def test_create_new_learner_contact(self):
        self.test_name = "create_new_learner_contact"
        # Simulate learner contact does not exist
        # Expected outcome: New learner contact is created
        self.hubspot_form_submitted.run(self.test_data)
        self.hubspot_form_submitted.salesforce.client.create_contact_record.assert_called_once()
        self.patcher.stop()

    def test_update_program_of_interest(self):
        self.test_name = "update_program_of_interest"
        # Simulate learner contact exists with different program of interest
        # Expected outcome: Program of interest is updated
        self.hubspot_form_submitted.run(self.test_data)
        self.hubspot_form_submitted.salesforce.client.update_contact_record.assert_called_once()

    def test_skip_email_sending(self):
        self.test_name = "skip_email_sending"
        # Simulate learner contact exists with the same program of interest
        # Expected outcome: Email sending is skipped
        self.hubspot_form_submitted.run(self.test_data)
        self.hubspot_form_submitted.hubspot.send_transactional_email.assert_not_called()

    def session_add(self, *args, **kwargs):
        if self.test_name == "create_expressed_interest":
            self.assertEqual(args[0].ip_address, self.test_data.get("properties").get("ip__c").get("value"))
            self.assertEqual(
                args[0].landing_page, self.test_data.get("properties").get("handl_landing_page").get("value")
            )
            self.assertEqual(
                args[0].lead_source, LeadSource(self.test_data.get("properties").get("hs_latest_source").get("value"))
            )
            self.assertEqual(args[0].program_interest, self.program_interest)
            self.assertEqual(
                args[0].referrer_url, self.test_data.get("properties").get("handl_original_url").get("value")
            )
            self.assertEqual(
                args[0].state_declared, self.test_data.get("properties").get("state_dropdown").get("value")
            )
            self.assertEqual(args[0].user_id, self.user_id)
            self.assertEqual(args[0].utm_campaign, self.test_data.get("properties").get("utm_campaign").get("value"))
            self.assertEqual(args[0].utm_content, self.test_data.get("properties").get("utm_content").get("value"))
            self.assertEqual(args[0].utm_source, self.test_data.get("properties").get("utm_source").get("value"))
            self.assertEqual(args[0].utm_medium, self.test_data.get("properties").get("utm_medium").get("value"))
            self.assertEqual(args[0].utm_source, self.test_data.get("properties").get("utm_source").get("value"))
            self.assertEqual(args[0].utm_term, self.test_data.get("properties").get("utm_term").get("value"))
            self.session_added = True
        if self.test_name == "create_new_contact_record":
            return Mock()

    def session_execute(self, *args, **kwargs):
        scalar_one = MagicMock()
        if self.test_name == "sms_opt_in" or self.test_name == "sms_opt_out":
            contact = Mock()
            expressed_interest_user_mock = Mock()
            expressed_interest_user_mock.program_interest.short_name = "Cybersecurity"
            contact.learner_status.status = "App Submitted"
            contact.id = self.user_id
            contact.program_of_interest = "Data Analysis"
            contact.expressed_interest_user = [expressed_interest_user_mock]
            scalar_one.scalar_one.return_value = contact
        if self.test_name == "send_email_ready_for_onboarding":
            contact = Mock()
            expressed_interest_user_mock = Mock()
            expressed_interest_user_mock.program_interest.short_name = "Cybersecurity"
            contact.learner_status.status = "Ready for Onboarding"
            contact.id = self.user_id
            contact.program_of_interest = "Data Analysis"
            contact.expressed_interest_user = [expressed_interest_user_mock]
            scalar_one.scalar_one.return_value = contact
        if self.test_name == "create_new_learner_contact":
            if args[0].columns_clause_froms[0].name == "user":
                scalar_one.scalar_one.side_effect = NoResultFound
            if args[0].columns_clause_froms[0].name == "learner_status":
                self.patcher = patch("events.hubspot_form_submitted.User")
                self.User = self.patcher.start()
                l_status_mock = Mock()
                l_status_mock.id = "learner_status_id_123"
                scalar_one.scalar_one.side_effect = l_status_mock
                self.hubspot_form_submitted.create_expressed_interest_record = Mock()
        if self.test_name == "update_learner_status_to_app_submitted":
            contact = Mock()
            expressed_interest_user_mock = Mock()
            expressed_interest_user_mock.program_interest.short_name = "Cybersecurity"
            contact.learner_status.status = "Dropped"
            contact.id = self.user_id
            contact.program_of_interest = "Data Analysis"
            contact.expressed_interest_user = [expressed_interest_user_mock]
            scalar_one.scalar_one.return_value = contact
        if self.test_name == "skip_email_sending":
            contact = Mock()
            expressed_interest_user_mock = Mock()
            expressed_interest_user_mock.program_interest.short_name = "Data Analysis"
            contact.learner_status.status = "Ready for Onboarding"
            contact.id = self.user_id
            contact.program_of_interest = "Data Analysis"
            contact.expressed_interest_user = [expressed_interest_user_mock]
            scalar_one.scalar_one.return_value = contact
        if self.test_name == "update_program_of_interest":
            contact = Mock()
            expressed_interest_user_mock = Mock()
            expressed_interest_user_mock.program_interest.short_name = "Cybersecurity"
            contact.learner_status.status = "Expressed Interest"
            contact.id = self.user_id
            contact.program_of_interest = "Cybersecurity"
            contact.expressed_interest_user = [expressed_interest_user_mock]
            scalar_one.scalar_one.return_value = contact
        return scalar_one
