#!/usr/bin/python3

from propus.logging_utility import Logging


class StudentPaceAndProgress:
    def __init__(
        self,
    ) -> None:
        self.logger = Logging.get_logger(
            "castor/jobs/strut_progress_activity_tracker/student_integrations/pace_and_progress"
        )
        self.strut_username = ""
        self.strut_id = ""
        self.last_activity_date = ""
        self.program_name = ""
        self.courses = []
        self.versions = []
        self.student_summary = []

    def calculate_progress(self, verbose=False):
        for version in self.versions:
            programSummary = ProgramSummary()
            programSummary.course = version["course_name"]
            overallProgress = 0.000000
            courseFinished = True

            # loop through current version of program and competencies tied to that version checking if Progress data
            # exists for overall Progress
            for competency in version["competencies"]:
                # if any(course for course in self.courses if course.competency == competency):
                for course in self.courses:
                    if course.competency == competency:
                        if course.progress is not None:
                            if verbose:
                                self.logger.info(
                                    f"""Competency: {course.competency},
                                    Current Overall: {overallProgress},
                                    Course Progress: {course.progress},
                                    Course Completion Status: {course.course_completed}"""
                                )

                            overallProgress += course.progress
                            if course.course_completed != "completed":
                                courseFinished = False
                        else:
                            if verbose:
                                self.logger.info(
                                    f"""Skipped  Comptency: {course.competency},
                                    Current Overall: {overallProgress},
                                    Course Progress: {course.progress},
                                    Course Completion Status: {course.course_completed}"""
                                )
                            if course.course_completed != "completed":
                                courseFinished = False

            programSummary.progress = (overallProgress / len(version["competencies"])) * 100
            programSummary.course_completed = courseFinished
            if verbose:
                self.logger.info(
                    f"""Student Summary: Course - {programSummary.course},
                    Pace - {programSummary.pace},
                    Progress - {programSummary.progress},
                    Course Completed: {programSummary.course_completed}"""
                )

            self.student_summary.append(programSummary)


class CoursePaceAndProgress:
    def __init__(
        self,
    ) -> None:
        self.competency = 0
        self.progress = 0.000000
        self.pace = 0.000000
        self.course_completed = None


class ProgramSummary:
    def __init__(
        self,
    ) -> None:
        self.course = ""
        self.progress = 0.000000
        self.pace = 0.000000
        self.course_completed = None
