from datetime import datetime, timedelta
import unittest
from unittest.mock import MagicMock, Mock

from jobs.pace_progress_automation.configurations.dev import dev_configs
from jobs.pace_progress_automation.services.email_service import EmailService
from jobs.pace_progress_automation.const.email_constants import SIGNATURES, EMAIL_OPENINGS, EMAIL_CLOSINGS


class TestEmailService(unittest.TestCase):
    def setUp(self) -> None:
        hubspot = MagicMock()
        hubspot.send_transactional_email = Mock(side_effect=self.send_transactional_email)

        self.email_service = EmailService(hubspot, dev_configs)
        self.email_service.in_test_mode = False

        self.contact_record = {
            "email": "you@me_Test.com",
            "academic_counselor_email": "asc@calbright.org",
            "first_name": "Daniel-Pierre",
            "enrollment_date": datetime(2023, 8, 16),
        }
        self.comp_data = {
            "week_number": 8,
            "prev_competencies": ["comp_1", "comp_2", "comp3"],
            "future_comp_by_week": {9: ["comp_4", "comp_5"]},
        }
        self.next_milestone_date = self.contact_record.get("enrollment_date") + timedelta(days=21)
        self.test_timeline = "180 Day"
        self.timeline_data = {"Timeline": self.test_timeline, "Auto Grace Period": "FALSE"}
        self.doc_url = "http://Hello.com/123789123789"
        self.completion_date = "yesterday or next week!"
        self.send_email_success = False

    def test_fetch_signatures(self):
        uniq_sigs = set()
        sig_map = {}
        for _ in range(len(SIGNATURES) * 2):
            sig = self.email_service.fetch_signature()
            uniq_sigs.add(sig)
            sig_map[sig] = sig_map.get(sig, 0) + 1
        self.assertEqual(len(uniq_sigs), len(SIGNATURES))
        self.assertEqual(len(set(list(sig_map.values()))), 1)

    def test_fetch_next_competencies_html(self):
        list_html = self.email_service.fetch_next_competencies_html(["1", "2", "3"])
        self.assertEqual(list_html, "<ul><li>1</li><li>2</li><li>3</li></ul>")

    def test_fetch_next_milestone_actions(self):
        rem_comp = {5: ["comp_1", "comp_2", "comp_3"], 6: ["comp_4", "comp_5"]}
        comp_to_complete, week_number = self.email_service.fetch_next_milestone_actions(
            rem_comp_by_week=rem_comp,
            user_completions=["comp_1", "comp_2", "comp_3", "comp_4", "comp_5"],
        )
        self.assertIsNone(comp_to_complete)
        self.assertIsNone(week_number)
        comp_to_complete, week_number = self.email_service.fetch_next_milestone_actions(
            rem_comp_by_week=rem_comp,
            user_completions=["comp_1"],
        )
        self.assertEqual(comp_to_complete, {"comp_2", "comp_3"})
        self.assertEqual(week_number, 5)
        comp_to_complete, week_number = self.email_service.fetch_next_milestone_actions(
            rem_comp_by_week=rem_comp,
            user_completions=[
                "comp_1",
                "comp_2",
                "comp_3",
            ],
        )
        self.assertEqual(comp_to_complete, {"comp_4", "comp_5"})
        self.assertEqual(week_number, 6)

    def test_fetch_behind_badge_list(self):
        html = self.email_service.fetch_behind_badge_list(prev_comps=["1", "2"], current_comps=["3", "4"])
        self.assertEqual(
            html,
            "Remaining Badges:<br /><ul><li>1</li><li>2</li></ul><br />Current Badges:<br /><ul><li>3</li><li>4</li></ul>",  # noqa: E501
        )
        html = self.email_service.fetch_behind_badge_list(prev_comps=["1", "2"])
        self.assertEqual(html, "Remaining Badges:<br /><ul><li>1</li><li>2</li></ul>")
        html = self.email_service.fetch_behind_badge_list(prev_comps=["1", "2"], current_comps=[])
        self.assertEqual(html, "Remaining Badges:<br /><ul><li>1</li><li>2</li></ul>")

    def test_send_prod_dev_configs(self):
        self.test_name = "prod_email_test"
        self.email_service.in_test_mode = False
        self.email_service.send_stopout_email(self.contact_record)
        self.test_name = "dev_email_test"
        self.email_service.in_test_mode = True
        self.email_service.send_stopout_email(self.contact_record)

    def test_send_stopout_email(self):
        self.send_email_success = False
        self.test_name = "stopout_email"
        self.email_service.send_stopout_email(self.contact_record)
        self.assertTrue(self.send_email_success)

    def test_send_welcome_email(self):
        self.send_email_success = False
        self.test_name = "welcome_email"
        self.email_service.send_welcome_email(
            timeline=self.test_timeline,
            contact_record=self.contact_record,
            doc_url=self.doc_url,
            completion_date=self.completion_date,
            competency_list=["comp_1", "comp_2", "comp_3"],
        )
        self.assertTrue(self.send_email_success)

    def test_send_epp_email(self):
        self.send_email_success = False
        self.test_name = "epp_email"
        self.email_service.send_epp_email(self.contact_record, self.test_timeline, self.comp_data)
        self.assertTrue(self.send_email_success)

    def test_send_weekly_updates_ahead(self):
        self.send_email_success = False
        self.test_name = "weekly_ahead"
        course_comp_data = {"future_comp_by_week": {5: ["comp_5", "comp_6"]}}
        user_comp_data = {"weeks_behind": 0, "all_completions": ["comp_4", "comp_5", "comp_6"]}
        self.assertIsNone(
            self.email_service.send_weekly_update(
                self.contact_record, self.timeline_data, None, course_comp_data, user_comp_data
            )
        )
        self.assertFalse(self.send_email_success)

        user_comp_data["all_completions"] = user_comp_data.get("all_completions")[:-1]
        course_comp_data["future_comp"] = ["comp_5", "comp_6"]
        course_comp_data["prev_competencies"] = ["comp_4"]
        self.assertIsNone(
            self.email_service.send_weekly_update(
                self.contact_record, self.timeline_data, None, course_comp_data, user_comp_data
            )
        )
        self.assertTrue(self.send_email_success)

    def test_send_weekly_updates_on_track(self):
        self.send_email_success = False
        self.test_name = "weekly_on_track"
        course_comp_data = {
            "future_comp_by_week": {5: ["comp_5", "comp_6"]},
            "future_comp": ["comp_5", "comp_6"],
            "prev_competencies": ["comp_3", "comp_4"],
        }
        user_comp_data = {"weeks_behind": 0, "all_completions": ["comp_3", "comp_4"]}

        self.assertIsNone(
            self.email_service.send_weekly_update(
                self.contact_record, self.timeline_data, self.next_milestone_date, course_comp_data, user_comp_data
            )
        )
        self.assertTrue(self.send_email_success)

    def test_send_weekly_updates_behind(self):
        self.send_email_success = False
        self.test_name = "weekly_behind"
        course_comp_data = {"future_comp_by_week": {5: ["comp_5"]}}
        user_comp_data = {"weeks_behind": 1, "incomplete_competencies": ["comp_3", "comp_4"], "all_completions": []}

        self.assertIsNone(
            self.email_service.send_weekly_update(
                self.contact_record, self.timeline_data, self.next_milestone_date, course_comp_data, user_comp_data
            )
        )
        self.assertTrue(self.send_email_success)

    def test_send_weekly_updates_way_behind(self):
        self.send_email_success = False
        self.test_name = "weekly_way_behind_first"
        course_comp_data = {"week_number": 4}
        user_comp_data = {"weeks_behind": 2, "incomplete_competencies": ["comp_3", "comp_4"], "all_completions": []}

        self.assertIsNone(
            self.email_service.send_weekly_update(
                self.contact_record, self.timeline_data, self.next_milestone_date, course_comp_data, user_comp_data
            )
        )
        self.assertTrue(self.send_email_success)

        self.send_email_success = False
        self.test_name = "weekly_way_behind_second"
        self.timeline_data["Auto Grace Period"] = "TRUE"
        course_comp_data["future_comp_by_week"] = {2: ["3"], 4: ["5", "6"]}
        self.assertIsNone(
            self.email_service.send_weekly_update(
                self.contact_record, self.timeline_data, self.next_milestone_date, course_comp_data, user_comp_data
            )
        )

    def send_transactional_email(self, email_id, to_email, cc, custom_properties, email_name):
        if self.test_name == "dev_email_test":
            self.assertIsNone(cc)
            self.assertEqual(to_email, self.email_service.test_email)
            return
        elif self.test_name == "prod_email_test":
            self.assertEqual(cc, self.email_service.prod_cc)
            self.assertEqual(to_email, self.contact_record.get("email"))
            return
        self.assertEqual(to_email, self.contact_record.get("email"))
        self.assertIn(custom_properties.get("signature"), SIGNATURES)
        self.assertEqual(custom_properties.get("first_name"), self.contact_record.get("first_name"))
        if self.test_name == "stopout_email":
            self.assertEqual(email_name, "Stopout Email")
            self.assertEqual(dev_configs.get("email_templates").get("stopout"), email_id)
            self.assertEqual(
                custom_properties.get("academic_success_counselor"),
                f'<a href="mailto:{self.contact_record.get("academic_counselor_email")}">Academic Success Counselor</a>',  # noqa: E501
            )
            self.send_email_success = True
        elif self.test_name == "welcome_email":
            self.assertEqual(email_name, "Day 1 Email (180 Day)")
            self.assertEqual(dev_configs.get("email_templates").get(self.test_timeline).get("welcome_email"), email_id)
            self.assertEqual(custom_properties.get("progress_timeline_url"), self.doc_url)
            self.assertEqual(custom_properties.get("completion_date"), self.completion_date)
            self.assertEqual(
                custom_properties.get("first_badges"), "<ul><li>comp_1</li><li>comp_2</li><li>comp_3</li></ul>"
            )
            self.send_email_success = True
        else:
            self.assertEqual(email_id, dev_configs.get("email_templates").get(self.test_timeline).get("update_email"))
            template_id = None
            index = 100
            if self.test_name == "epp_email":
                template_id = "still_enrolled_program_pathway"
                self.assertEqual(
                    custom_properties.get("badge_data"),
                    "Remaining Badges:<br /><ul><li>comp_1</li><li>comp_2</li><li>comp3</li></ul><br />Current Badges:<br /><ul><li>comp_4</li><li>comp_5</li></ul>",  # noqa: E501
                )
            elif self.test_name == "weekly_ahead":
                template_id = "ahead"
                index = 70
                self.assertEqual(custom_properties.get("badge_data"), "<ul><li>comp_6</li></ul>")
                self.assertIn("66", custom_properties.get("opening"))
            elif self.test_name == "weekly_on_track":
                template_id = "on_track"
                index = 65
                self.assertTrue(
                    custom_properties.get("badge_data")
                    in ["<ul><li>comp_5</li><li>comp_6</li></ul>", "<ul><li>comp_6</li><li>comp_5</li></ul>"]
                )
                self.assertIn("50", custom_properties.get("opening"))
            elif self.test_name == "weekly_behind":
                template_id = "behind"
                index = 275
                self.assertEqual(
                    custom_properties.get("badge_data"),
                    "Remaining Badges:<br /><ul><li>comp_3</li><li>comp_4</li></ul><br />Current Badges:<br /><ul><li>comp_5</li></ul>",  # noqa: E501
                )
            elif self.test_name == "weekly_way_behind_first":
                index = 49
                template_id = "first_way_behind"
                self.assertEqual(custom_properties.get("badge_data"), "<ul><li>comp_3</li><li>comp_4</li></ul>")
            elif self.test_name == "weekly_way_behind_second":
                template_id = "way_behind"
                index = 98
                self.assertIn(
                    "Just reply to this email letting me know if you're interested", custom_properties.get("opening")
                )

            self.assertIn(EMAIL_OPENINGS.get(template_id)[:index], custom_properties.get("opening"))
            self.assertEqual(EMAIL_CLOSINGS.get(template_id), custom_properties.get("closing"))
            self.send_email_success = True


if __name__ == "__main__":
    unittest.main()
