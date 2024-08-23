from datetime import datetime, timedelta
from typing import List, AnyStr, Dict

from const.email_constants import EMAIL_OPENINGS, EMAIL_CLOSINGS, SIGNATURES, MIGRATION_SENTENCE

from propus.hubspot import Hubspot
from propus import Logging

DATE_STRING_FMT = "%B %-d, %Y"


class EmailService:
    def __init__(self, hubspot, configs):
        self.hubspot = hubspot
        self.configs = configs
        self.logger = Logging.get_logger("services/email_service.py")
        self.signature_idx = 0
        self.next_plan = {"60 Day": "90 Day", "90 Day": "120 Day", "120 Day": "180 Day", "180 Day": "365 Day"}
        self.in_test_mode = configs.get("use_test_email", True)
        self.test_email = "pace-testers@calbright.org"
        self.prod_cc = ["progress@calbright.org"]

    @staticmethod
    def build(configs, ssm):
        return EmailService(
            hubspot=Hubspot.build(ssm.get_param(configs.get("ssm").get("hubspot"))),
            configs=configs,
        )

    def fetch_signature(self) -> AnyStr:
        """
        This function fetches our list of possible signatures and will give a different signature on each time
        the function is called. Therefore, one signature (respondent) will not get more emails than others

        Returns:
            AnyStr: HTML String of signature
        """
        sig_index = self.signature_idx % len(SIGNATURES)
        self.signature_idx += 1
        return SIGNATURES[sig_index]

    @staticmethod
    def fetch_next_competencies_html(competencies: List[AnyStr]) -> AnyStr:
        """
        An easy function to retrieve a HTML bulleted list of competencies

        Args:
            competencies (List[AnyStr]): List of competency strings

        Returns:
            AnyStr: HTML of UL/LI HTML list
        """
        return f"<ul><li>{'</li><li>'.join(competencies)}</li></ul>"

    @staticmethod
    def fetch_next_milestone_actions(rem_comp_by_week: Dict, user_completions: List) -> (set, int):
        """
        Given a the remaining competencies by week in dictionary form {week_num: List of competencies} and the
        list of competencies the student has completed, we will loop through and see what competencies the student
        has remaining to complete and what week number they have completed through

        Args:
            rem_comp_by_week (Dict): dictionary of remaining competencies by week number to list of competencies
            user_completions (List): List of competencies the student has completed

        Returns:
            Tuple of a set and an int:
                set - competencies left to complete in the milestone the student is in
                int - week number of the milestone the student currently falls into from their completion rate
        """
        for week_number, competencies in rem_comp_by_week.items():
            comp_to_complete = set(competencies) - set(user_completions)
            if comp_to_complete:
                return comp_to_complete, week_number
        return None, None

    def fetch_behind_badge_list(self, prev_comps: List, current_comps: List = None) -> AnyStr:
        """
        Helper function to supply html that matches the following format:
           Remaining Badges
             - Badge 1
             - Badge 2
             - Badge 3
           Current Badges:
             - Badge 4
             - Badge 5
             - Badge 6

        Args:
            prev_comps (List): List of competencies that should have been completed "Previous state"
            current_comps (List): List of Competencies to complete within the next milestone

        Returns:
            AnyStr: HTML of a Remaining and Current badge list
        """
        badge_html = f"Remaining Badges:<br />{self.fetch_next_competencies_html(prev_comps)}"
        if current_comps:
            badge_html += f"<br />Current Badges:<br />{self.fetch_next_competencies_html(current_comps)}"
        return badge_html

    def fetch_recipient(self, contact_email):
        if self.in_test_mode:
            return self.test_email
        return contact_email

    def fetch_cc(self):
        if not self.in_test_mode:
            return self.prod_cc
        return None

    @staticmethod
    def format_first_name(name):
        return name if not name.isupper() and not name.islower() else name[0].capitalize() + name[1:].lower()

    def send_stopout_email(self, contact_record: Dict) -> None:
        """
        Function that send student stop out emails

        Args:
            contact_record (Dict): Dictionary of student contact record data. Requirements: email, first_name, and
                academic_counselor_email
        """
        self.hubspot.send_transactional_email(
            email_id=self.configs.get("email_templates").get("stopout"),
            to_email=self.fetch_recipient(contact_record.get("email")),
            cc=self.fetch_cc(),
            custom_properties={
                "first_name": self.format_first_name(contact_record.get("first_name")),
                "academic_success_counselor": f'<a href="mailto:{contact_record.get("academic_counselor_email", "")}">Academic Success Counselor</a>',  # noqa: E501
                "signature": self.fetch_signature(),
            },
            email_name="Stopout Email",
        )
        self.logger.info(f"Sent Stop Out Email for {contact_record.get('email')}")

    def send_welcome_email(
        self, timeline: AnyStr, contact_record: Dict, doc_url: AnyStr, completion_date: AnyStr, competency_list: List
    ):
        """
        Function that sends student welcome emails

        Args:
            timeline (AnyStr): Timeline Tract Name (i.e. 90 Day, 180 Day, etc)
            contact_record (Dict): Dictionary of student record data. Requirements(first_name, enrollment_date, email)
            doc_url (AnyStr): URl of the Pace Pipeline PDF
            completion_date (AnyStr): Date of completion of the next milestone
            competency_list (List): List of competencies to complete by next milestone
        """
        self.hubspot.send_transactional_email(
            email_id=self.configs.get("email_templates").get(timeline).get("welcome_email"),
            to_email=self.fetch_recipient(contact_record.get("email")),
            cc=self.fetch_cc(),
            custom_properties={
                "first_name": self.format_first_name(contact_record.get("first_name")),
                "progress_timeline_url": doc_url,
                "completion_date": completion_date,
                "first_badges": self.fetch_next_competencies_html(competency_list),
                "signature": self.fetch_signature(),
            },
            email_name=f"Day 1 Email ({timeline})",
        )
        self.logger.info(f"Sent Welcome Email for {contact_record.get('email')}")

    def send_epp_email(self, contact_record: Dict, timeline: AnyStr, comp_data: Dict):
        """
        Function to send an email to a student whom is still in the enrolled in program pathway learner status. In
        other words the student has not yet completed any SAA.

        Args:
            contact_record (Dict): Dictionary of student record data. Requirements(first_name, enrollment_date, email)
            timeline (AnyStr): String representation of the tract the student is on (i.e. 90 Day, 180 Day)
            comp_data (Dict): Dictionary of competency data. Requirements: (prev_competencies, week_number,
                future_comp_by_week)
        """
        template_id = self.configs.get("email_templates").get(timeline).get("update_email")
        opening = EMAIL_OPENINGS.get("still_enrolled_program_pathway").format(
            enrollment_date=contact_record.get("enrollment_date").strftime(DATE_STRING_FMT),
            timeline=timeline,
            next_milestone_date=(
                contact_record.get("enrollment_date") + timedelta(days=7 * (comp_data.get("week_number") + 1))
            ).strftime(DATE_STRING_FMT),
        )
        closing = EMAIL_CLOSINGS.get("still_enrolled_program_pathway")
        self.hubspot.send_transactional_email(
            email_id=template_id,
            to_email=self.fetch_recipient(contact_record.get("email")),
            cc=self.fetch_cc(),
            custom_properties={
                "first_name": self.format_first_name(contact_record.get("first_name")),
                "opening": opening,
                "badge_data": self.fetch_behind_badge_list(
                    prev_comps=comp_data.get("prev_competencies"),
                    current_comps=comp_data.get("future_comp_by_week").get(
                        min(comp_data.get("future_comp_by_week").keys())
                    ),
                ),
                "closing": closing,
                "week_number": comp_data.get("week_number"),
                "signature": self.fetch_signature(),
            },
            email_name=f"Update Email ({timeline})",
        )
        self.logger.info(f"Sent Stop Out Email for {contact_record.get('email')}")

    @staticmethod
    def student_is_ahead(all_completions: set, comp_data: Dict) -> bool:
        """
        This function will check if a student is ahead by the following two checks:
         - Will return False if the student has competencies in the middle of their milestone that are incomplete
            -OR-
         - Student has not completed any future competencies


        Args:
            all_completions (set): set of competency names the user has completed
            comp_data (Dict): dictionary of competency data attributed to the student

        Returns:
            Bool: True if a student is ahead on their competencies for their timeline
        """
        if set(comp_data.get("mid_comps", [])) - all_completions:
            return False
        return True if len(all_completions.intersection(comp_data.get("future_comp"))) else False

    def send_weekly_update(
        self,
        contact_record: Dict,
        timeline_data: Dict,
        next_milestone_date: datetime,
        course_comp_data: Dict,
        user_comp_data: Dict,
    ) -> None:
        """
        This function is called to send most emails. It is called on a weekly basis to send updates to the student
        on their progress through their selected pace timeline tract.
        There are 4 different statuses, which cause a different email to be sent. The are:
        - Ahead: Student has completed all necessary competencies up to their current milestone and have completed
                additional competencies from future milestones
        - On Track: Student has completed all necessary competencies up to their current milestone
        - Behind: Student has incomplete competencies from their previous milestone
        - Way Behind: Student has incomplete competencies from milestones 2 to 6 weeks in the past
            - First time in Way Back Status the student will get a special email

        Args:
            contact_record (Dict): Dictionary of student contact record details. Key Requirements: id, enrollment_date
                academic_counselor_email, email, first_name
            timeline_data (Dict): Timeline data. Key Requirements: Timeline, Auto Grace Period
            next_milestone_date (datetime): Date of the student's next milestone
            course_comp_data (Dict): Dictionary of all data regarding the course's competency data. Required keys:
                future_comp, future_comp_by_week, prev_competencies, week_number
            user_comp_data (Dict): Dictionary of all data regarding the student's completion of competency. Required
                keys: weeks_behind, all_completions, incomplete_competencies
        """
        template_id = self.configs.get("email_templates").get(timeline_data.get("Timeline")).get("update_email")
        if not user_comp_data.get("weeks_behind"):
            # "Student is either Ahead or On Track"
            comp_to_complete, deadline = self.fetch_next_milestone_actions(
                rem_comp_by_week=course_comp_data.get("future_comp_by_week"),
                user_completions=user_comp_data.get("all_completions"),
            )
            if not comp_to_complete:
                # Student already completed all competencies
                self.logger.info(f"Student {contact_record.get('id')} completed all milestone tasks. No Email Sent")
                return

            status = "on_track"
            if self.student_is_ahead(set(user_comp_data.get("all_completions")), course_comp_data):
                # No incomplete competencies and some future competencies completed
                next_milestone_date = contact_record.get("enrollment_date") + timedelta(days=7 * deadline)
                status = "ahead"

            percent_complete = int(
                (
                    len(user_comp_data.get("all_completions"))
                    / (len(course_comp_data.get("future_comp")) + len(course_comp_data.get("prev_competencies")))
                )
                * 100
            )

            opening = EMAIL_OPENINGS.get(status).format(
                percent_complete=percent_complete,
                plan_name=timeline_data.get("Timeline"),
                next_milestone_date=next_milestone_date.strftime(DATE_STRING_FMT),
            )
            competency_data = self.fetch_next_competencies_html(comp_to_complete)
        elif user_comp_data.get("weeks_behind") == 1:
            next_comps = []
            if course_comp_data.get("future_comp_by_week"):
                next_comps = course_comp_data.get("future_comp_by_week").get(
                    min(course_comp_data.get("future_comp_by_week").keys())
                )
            status = "behind"
            opening = EMAIL_OPENINGS.get(status).format(
                plan_name=timeline_data.get("Timeline"),
                next_milestone_date=next_milestone_date.strftime(DATE_STRING_FMT),
            )
            competency_data = self.fetch_behind_badge_list(
                prev_comps=user_comp_data.get("incomplete_competencies"),
                current_comps=list(set(next_comps) - set(user_comp_data.get("all_completions"))),
            )
        elif 1 < user_comp_data.get("weeks_behind") <= 6:
            if timeline_data.get("Auto Grace Period") == "TRUE":
                next_comps = []
                if course_comp_data.get("future_comp_by_week"):
                    next_comps = course_comp_data.get("future_comp_by_week").get(
                        min(course_comp_data.get("future_comp_by_week").keys())
                    )

                status = "way_behind"
                migration_sentence = ""
                if self.next_plan.get(timeline_data.get("Timeline")):
                    migration_sentence = MIGRATION_SENTENCE.format(
                        next_plan_name=self.next_plan.get(timeline_data.get("Timeline"))
                    )
                opening = EMAIL_OPENINGS.get(status).format(
                    plan_name=timeline_data.get("Timeline"),
                    migration_sentence=migration_sentence,
                    asc_email=contact_record.get("academic_counselor_email", ""),
                    next_milestone_date=next_milestone_date.strftime(DATE_STRING_FMT),
                )
                competency_data = self.fetch_behind_badge_list(
                    prev_comps=user_comp_data.get("incomplete_competencies"),
                    current_comps=list(set(next_comps) - set(user_comp_data.get("all_completions"))),
                )
            else:
                status = "first_way_behind"
                opening = EMAIL_OPENINGS.get(status).format(
                    plan_name=timeline_data.get("Timeline"),
                    next_milestone_date=next_milestone_date.strftime(DATE_STRING_FMT),
                )
                competency_data = self.fetch_next_competencies_html(user_comp_data.get("incomplete_competencies"))
        else:
            self.logger.error(f"Uncaught weeks behind: {contact_record.get('id')}, {user_comp_data} {course_comp_data}")
            return

        closing = EMAIL_CLOSINGS.get(status)
        self.hubspot.send_transactional_email(
            email_id=template_id,
            to_email=self.fetch_recipient(contact_record.get("email")),
            cc=self.fetch_cc(),
            custom_properties={
                "first_name": self.format_first_name(contact_record.get("first_name")),
                "opening": opening,
                "badge_data": competency_data,
                "closing": closing,
                "week_number": course_comp_data.get("week_number") if course_comp_data.get("week_number", 0) > 0 else 1,
                "signature": self.fetch_signature(),
            },
            email_name=f"Update Email ({timeline_data.get('Timeline')})",
        )
        self.logger.info(
            f"Sent Weekly Email for {contact_record.get('email')} - {status} ({user_comp_data.get('weeks_behind')})"
        )
