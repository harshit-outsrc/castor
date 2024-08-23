from datetime import datetime, timedelta
import unittest

from jobs.pace_progress_automation.configurations.dev import dev_configs
from jobs.pace_progress_automation.pace_pipeline import PacePipeline


class TestPacePipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.pace_progress = PacePipeline(
            configs=dev_configs, gsheet=None, salesforce_service=None, pdf_service=None, email_service=None
        )

        self.timeline_data = "365 Day"
        self.contact_record = {
            "first_name": "John",
            "last_name": "Doe",
            "enrollment_date": datetime(2023, 8, 16),
        }

    def test_fetch_pdf_args(self):
        expected_resp = {
            "full_name": "John Doe",
            "enrollment_date": "August 16, 2023",
            "timeline": "365 Day",
            "week_1": "August 23, 2023",
            "first_completion_date": "August 23, 2023",
            "week_2": "August 30, 2023",
            "week_3": "September 6, 2023",
            "week_5": "September 20, 2023",
            "week_6": "September 27, 2023",
            "week_9": "October 18, 2023",
            "week_10": "October 25, 2023",
            "week_12": "November 8, 2023",
            "week_13": "November 15, 2023",
            "week_14": "November 22, 2023",
            "week_15": "November 29, 2023",
            "week_16": "December 6, 2023",
            "week_17": "December 13, 2023",
            "week_18": "December 20, 2023",
            "week_19": "December 27, 2023",
            "week_34": "April 10, 2024",
            "week_52": "August 14, 2024",
        }
        args = self.pace_progress.fetch_pdf_args(self.timeline_data, self.contact_record)
        for key, val in args.items():
            self.assertEqual(expected_resp.get(key), val)
            del expected_resp[key]
        self.assertEqual(len(expected_resp), 0)

    def test_fetch_competencies_needed_for_completion(self):
        w_num = 3
        response = self.pace_progress.fetch_competencies_needed_for_completion(
            week_number=w_num,
            weekly_competencies={
                "week1": ["c1", "c2"],
                "week3": ["c3"],
                "week4": ["c5", "c6", "c7"],
            },
        )
        self.assertEqual(w_num + 1, response.get("week_number"))
        self.assertEqual(response.get("prev_competencies"), ["c1", "c2", "c3"])
        self.assertEqual(response.get("prev_competencies_by_week"), {1: ["c1", "c2"], 3: ["c3"]})
        self.assertEqual(response.get("future_comp"), ["c5", "c6", "c7"])
        self.assertEqual(response.get("future_comp_by_week"), {4: ["c5", "c6", "c7"]})

    def test_fetch_badge_statuses(self):
        response = self.pace_progress.fetch_badge_statuses(
            comp_data={
                "week_number": 6,
                "prev_competencies_by_week": {3: ["completed_2_weeks_ago"], 4: ["incomplete_comp"]},
                "prev_competencies": ["completed_2_weeks_ago", "completed_last_week", "incomplete_comp"],
                "future_comp": ["needs_to_be_completed"],
            },
            completed_badges=[
                {
                    "badge_name": "should_not_show_up",
                },
                {
                    "badge_name": "completed_2_weeks_ago",
                    "completion_datetime": self.pace_progress.run_date - timedelta(days=8),
                },
                {
                    "badge_name": "completed_last_week",
                    "completion_datetime": self.pace_progress.run_date - timedelta(days=2),
                },
            ],
            completed_week_num=5,
        )
        self.assertEqual(response.get("incomplete_competencies"), ["incomplete_comp"])
        self.assertEqual(response.get("all_completions"), ["completed_2_weeks_ago", "completed_last_week"])
        self.assertEqual(response.get("weeks_behind"), 2)
        self.assertEqual(response.get("latest_completion"), self.pace_progress.run_date - timedelta(days=2))

    def test_fetch_week_number(self):
        week_num = 6
        self.pace_progress.run_date = self.contact_record.get("enrollment_date") + timedelta(days=week_num * 7)
        week, milestone_date = self.pace_progress.fetch_week_number(
            enrollment_date=self.contact_record.get("enrollment_date"), timeline_weeks=[1, 3, 4, 10]
        )
        self.assertEqual(week, week_num)
        self.assertEqual(milestone_date, datetime(2023, 10, 25))


if __name__ == "__main__":
    unittest.main()
