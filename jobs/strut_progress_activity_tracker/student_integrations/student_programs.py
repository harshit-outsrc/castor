#!/usr/bin/python3


class StudentProgram:
    def __init__(
        self,
    ) -> None:
        self.program_name = ""
        self.program_courses = []
        self.course_competencies_versions = []
        self.number_of_courses = 0
        self.number_of_comptencies = 0

    def set_current_program(
        self,
        program_name,
        program_courses,
        course_competencies,
        number_of_courses,
        number_of_competencies,
        program_versions,
    ):
        self.program_name = program_name
        self.program_courses = program_courses
        self.course_competencies = course_competencies
        self.number_of_courses = number_of_courses
        self.number_of_comptencies = number_of_competencies
        self.program_versions = program_versions

    def determine_program(self, tagID, programVersion, versionCompetencies, competencyCount):
        if tagID == 1:
            self.set_current_program(
                "Medical Coding", ["MC500", "WF500"], versionCompetencies, 2, competencyCount, programVersion
            )
        elif tagID == 2:
            self.set_current_program(
                "IT Support", ["IT500", "WF500"], versionCompetencies, 2, competencyCount, programVersion
            )
        elif tagID == 3:
            self.set_current_program(
                "Cybersecurity", ["IT510", "WF500"], versionCompetencies, 2, competencyCount, programVersion
            )
        elif tagID == 4:
            return
        elif tagID == 5:
            self.set_current_program(
                "HC DEI", ["HC501", "HC502"], versionCompetencies, 2, competencyCount, programVersion
            )
        elif tagID == 6:
            self.set_current_program(
                "Career Readiness", ["WF510"], versionCompetencies, 1, competencyCount, programVersion
            )
        elif tagID == 7:
            self.set_current_program(
                "Data Analysis", ["BUS500", "BUS501"], versionCompetencies, 2, competencyCount, programVersion
            )
        elif tagID == 54:
            self.set_current_program(
                "T2T Intro to Networks", ["IT532", "IT533"], versionCompetencies, 1, competencyCount, programVersion
            )
        elif tagID == 57:
            self.set_current_program(
                "Project Management",
                ["BUS520", "BUS521", "BUS522"],
                versionCompetencies,
                3,
                competencyCount,
                programVersion,
            )
