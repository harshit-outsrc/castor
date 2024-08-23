#!/usr/bin/python3

import os
import aiohttp
import student_integrations.student_programs as student_programs
import student_integrations.pace_and_progress as pace_and_progress
from dotenv import load_dotenv
from propus.logging_utility import Logging

logger = Logging.get_logger("castor/jobs/strut_progress_activity_tracker/student_integrations/strut")

load_dotenv()
# Strut API Request Variables
STRUT_USER = os.getenv("STRUT_USER")
STRUT_PSW = os.getenv("STRUT_PSW")
STRUT_ORG = os.getenv("STRUT_ORG")
BASE_URL = os.getenv("BASE_URL")
STRUT_TOKEN = None

# should be in a database, but for now create dictionary
COURSE_VERSIONS = [
    # WF500 - Essentials course
    {"version": "1.0", "course_name": "WF500", "competencies": [31]},
    {"version": "2.0", "course_name": "WF500", "competencies": [45]},
    {"version": "3.0", "course_name": "WF500", "competencies": [110]},
    {"version": "4.0", "course_name": "WF500", "competencies": [199]},
    {"version": "5.0", "course_name": "WF500", "competencies": [210]},
    # IT500 - IT Support
    {"version": "1.0", "course_name": "IT500", "competencies": [23, 24]},
    {"version": "2.0", "course_name": "IT500", "competencies": [74, 75]},
    {"version": "3.0", "course_name": "IT500", "competencies": [102, 114, 109]},
    {"version": "4.0", "course_name": "IT500", "competencies": [200]},
    {"version": "5.0", "course_name": "IT500", "competencies": [214]},
    # IT510 - Cybersecurity
    {"version": "1.0", "course_name": "IT510", "competencies": [22]},
    {"version": "2.0", "course_name": "IT510", "competencies": [66, 67]},
    {"version": "3.0", "course_name": "IT510", "competencies": [113, 106, 108]},
    {"version": "4.0", "course_name": "IT510", "competencies": [201]},
    {"version": "5.0", "course_name": "IT510", "competencies": [211]},
    # MC500 - Medical Coding
    {"version": "1.0", "course_name": "MC500", "competencies": [40, 37, 38, 39]},
    {"version": "2.0", "course_name": "MC500", "competencies": [117, 37, 38, 39]},
    {"version": "3.0", "course_name": "MC500", "competencies": [198]},
    # HC501 - HC DEI module 1
    {"version": "1.0", "course_name": "HC501", "competencies": [152]},
    {"version": "2.0", "course_name": "HC501", "competencies": [202]},
    # HC502 - HC DEI module 2
    {"version": "1.0", "course_name": "HC502", "competencies": [150]},
    {"version": "2.0", "course_name": "HC502", "competencies": [203]},
    # WF510 - Career Readiness
    {"version": "1.0", "course_name": "WF510", "competencies": [153]},
    # BUS500 - Data Analysis module 1
    {"version": "1.0", "course_name": "BUS500", "competencies": [207]},
    {"version": "2.0", "course_name": "BUS500", "competencies": [222, 223, 224, 225, 226, 227, 228]},
    # BUS501 - Data Analysis module 2
    {"version": "1.0", "course_name": "BUS501", "competencies": [205]},
    {"version": "2.0", "course_name": "BUS501", "competencies": [221, 229, 230, 231, 232]},
    # IT532 - T2T Intro to Networks module 1
    {"version": "1.0", "course_name": "IT532", "competencies": [233, 234, 235, 236, 237, 238, 239, 240, 241]},
    # IT533 - T2T Intro to Networks module 2
    {
        "version": "1.0",
        "course_name": "IT533",
        "competencies": [242, 243, 245, 244, 246, 247, 248, 249, 250, 251, 252, 253],
    },
    # BUS520 - Project Management module 1
    {
        "version": "1.0",
        "course_name": "BUS520",
        "competencies": [268, 269, 270, 271, 272, 273],
    },
    # BUS521 - Project Management module 2
    {
        "version": "1.0",
        "course_name": "BUS521",
        "competencies": [274, 275, 276, 277, 278],
    },
    # BUS522 - Project Management module 3
    {
        "version": "1.0",
        "course_name": "BUS522",
        "competencies": [279, 280, 281, 282, 283, 284, 285, 286],
    },
]

PROGRAM_TAGS = {
    1: "Medical Coding",
    2: "IT Support",
    3: "Cybersecurity",
    5: "HC DEI",
    6: "Career Readiness",
    7: "Data Analysis",
    54: "T2T Intro to Networks",
    57: "Project Management",
}


def get_competency_list(courseName):
    competencyList = []
    for version in COURSE_VERSIONS:
        if version["course_name"] == courseName:
            competencyList.append(version)
    return competencyList


def get_current_version(studentEnrollments, courseName, verbose=False):
    # need to get latest by competency id first to determine if they are enrolled in a later version
    sortedEnrollments = sorted(studentEnrollments, key=lambda kv: int(kv["competency"]["id"]), reverse=True)
    index = 0

    for enrollment in sortedEnrollments:
        index += 1
        if verbose:
            logger.info(
                f"""Student ID: {studentEnrollments[0]["student"]["id"]},
                Sorted Enrollment {index} of {len(sortedEnrollments)},
                Sorted Competency ID: {enrollment["competency"]["id"]} - {enrollment["competency"]["title"]}"""
            )
        competencyList = get_competency_list(courseName)
        for version in competencyList:
            for competency in version["competencies"]:
                if competency == enrollment["competency"]["id"]:
                    return version

    return {"version": "N/A", "course_name": "N/A", "competencies": "N/A"}


async def token_request(session):
    async with session.post(
        f"{BASE_URL}/users/authorize",
        headers={"SL-Tenant": STRUT_ORG, "Accept": "application/vnd.strut.v2"},
        data={"identifier": STRUT_USER, "password": STRUT_PSW},
    ) as resp:
        token_response = await resp.json(content_type="application/json")

    logger.info("Strut Authorization Received.")
    token = token_response["token"]
    return token


# Grab all active students in strut with a tag tied to their user determining they are enrolled in a program
async def strut_active_students(verbose=False):
    async with aiohttp.ClientSession() as session:
        if STRUT_TOKEN is None:
            token = await token_request(session)
        else:
            token = STRUT_TOKEN
        batchIndex = 0
        recordIndex = 0
        recordsPerPage = 50
        activeStudents = []
        studentCount = 0

        async with session.get(
            f"{BASE_URL}/users/users",
            headers={
                "SL-Tenant": STRUT_ORG,
                "Accept": "application/vnd.strut.v2",
                "Authorization": "Bearer " + token,
            },
            params={
                "count": 1,
                "shallow": "true",
                "state": "active",
                "test_users": "false",
            },
        ) as resp:
            students_response = await resp.json(content_type="application/json")

        studentCount = students_response["total"]
        logger.info(f"Found {studentCount} active users. Extracting only the ones with tags...")
        # Test
        # while recordIndex < 1:
        # Production
        while recordIndex < studentCount:
            if verbose:
                logger.info(f"Checking {recordIndex} - {recordIndex + recordsPerPage}...")

            async with session.get(
                f"{BASE_URL}/users/users",
                headers={
                    "SL-Tenant": STRUT_ORG,
                    "Accept": "application/vnd.strut.v2",
                    "Authorization": "Bearer " + token,
                },
                params={
                    "count": recordsPerPage,
                    "tags": "true",
                    "sort": "last_activity_date",
                    "start": recordIndex,
                    "shallow": "true",
                    "state": "active",
                    "test_users": "false",
                },
            ) as resp:
                users_response = await resp.json(content_type="application/json")
                usersList = users_response["users"]

                for user in usersList:
                    if len(user["tags"]) == 0:
                        logger.info(f"{user['id']}: Student doesn't have a tag.")
                    else:
                        student_tag = None
                        for tag in user["tags"]:
                            if PROGRAM_TAGS.get(tag["id"]):
                                student_tag = tag
                                break
                        if user["state"] == "active" and user["role"] == "student" and student_tag:
                            activeStudents.append(
                                {
                                    "student_id": user["id"],
                                    "student_username": user["username"],
                                    "calbright_email": user["email"],
                                    "student_name": user["first_name"] + " " + user["last_name"],
                                    "student_tag_id": student_tag["id"],
                                    "modified": user["modified"],
                                    "last_activity_date": user["last_activity_date"],
                                    "enrollments_needed": [],
                                    "enrollments_to_unlock": [],
                                }
                            )
                            batchIndex += 1
                            if verbose:
                                logger.info(f"{user['email']} contains tag id: {student_tag['id']}")
                        else:
                            logger.info(f"Skipping {user['id']}: State({user['state']}), Tags: {user['tags']}")
            recordIndex += recordsPerPage

        logger.info(f"Finished processing {batchIndex} batches of strut students.")
    return activeStudents


# Grab strut enrollments based on active students that are passed into the function
async def strut_student_enrollments(strutActiveStudents):
    async with aiohttp.ClientSession() as session:
        if STRUT_TOKEN is None:
            token = await token_request(session)
        else:
            token = STRUT_TOKEN

        recordsPerPage = 50
        studentEnrollments = []
        logger.info("Starting process for strut enrollments.")

        for student in strutActiveStudents:
            logger.info(
                f"Processing Enrollment for {student.get('student_username')} with ID: {student.get('student_id')}"
            )
            async with session.get(
                BASE_URL + "/enrollments",
                headers={
                    "SL-Tenant": STRUT_ORG,
                    "Accept": "application/vnd.strut.v2+json",
                    "Authorization": "Bearer " + token,
                },
                params={
                    "student_id": student["student_id"],
                    "count": recordsPerPage,
                    "shallow": "false",
                    "depth": 0,
                    "include_state": "true",
                    "structure_only": "true",
                },
            ) as resp:
                enrollments_response = await resp.json(content_type="application/json")

            if enrollments_response["enrollments"] is not None:
                enrollments = enrollments_response["enrollments"]

                for enrollment in enrollments:
                    studentEnrollments.append(enrollment)

            else:
                logger.info(f"Student: {student['student_id']} - {student['username']} missing enrollments.")

        logger.info("Finished processing strut enrollments.")
    return studentEnrollments


# Calculate Overall Progress data for the active students found based on program and competencies assigned.
async def handle_progress_student_data(activeStudents, studentEnrollments, verbose=False):
    processedStudents = []
    index = 0

    logger.info("Calculating Student Progress Data.")
    for student in activeStudents:
        studentPaceProgress = pace_and_progress.StudentPaceAndProgress()
        processedEnrollments = []
        versionList = []
        currentStudentProgram = student_programs.StudentProgram()
        if verbose:
            logger.info(f"Student {student['student_id']} Program by student_tag_id: {student['student_tag_id']}")

        studentPaceProgress.strut_username = student["student_username"]
        studentPaceProgress.strut_id = student["student_id"]
        # Last Updated/Modified Date in the enrollment record is unreliable so we will need to use last_activity_date
        studentPaceProgress.last_activity_date = student.get("last_activity_date")
        currentStudentProgram.determine_program(student["student_tag_id"], "N/A", "N/A", 0)
        studentPaceProgress.program_name = currentStudentProgram.program_name

        for enrollment in studentEnrollments:
            if student["student_id"] == enrollment["student"]["id"]:
                courseData = pace_and_progress.CoursePaceAndProgress()
                processedEnrollments.append(enrollment)
                index += 1
                if verbose:
                    logger.info(
                        f"""Processing Enrollment {index} of {len(studentEnrollments)}.
                        ID: {enrollment['competency']['root_node']['id']},
                        Competency: {enrollment['competency']['id']} - {enrollment['competency']['root_node']['title']},
                        Pace: {enrollment['competency']['root_node']['progress']},
                        Progress: {enrollment['progress']},
                        Course Completion: {enrollment['state']},
                        Updated At: {enrollment['updated_at']}"""
                    )

                # If needing to check for updated_at timestamps
                # updated_at = enrollment['updated_at']
                # if(updated_at != None and
                #    (pandas.to_datetime(studentPaceProgress.last_activity_date) < pandas.to_datetime(updated_at))):
                #     studentPaceProgress.last_activity_date = updated_at

                courseData.progress = enrollment["competency"]["root_node"]["progress"]
                courseData.pace = enrollment["progress"]["assessments_passed_percentage"]

                # Need to adjust course completed based on completion date rather then state since state can be locked
                # courseData.course_completed = enrollment['state']
                if enrollment["completed_at"] is not None:
                    # if completed date is not None, mark as completed as state doesn't matter
                    courseData.course_completed = "completed"
                    courseData.progress = 1.0
                else:
                    # if completed date is None, use the enrollment state as this is potentially active, locked or null
                    courseData.course_completed = enrollment["state"]

                courseData.competency = enrollment["competency"]["id"]
                if verbose:
                    logger.info(
                        f"""Competency: {courseData.competency}, Pace: {courseData.pace},
                        Progress: {courseData.progress}, Course Completion Status: {courseData.course_completed}"""
                    )
                studentPaceProgress.courses.append(courseData)

        if len(processedEnrollments) == 0:
            logger.warning(f"Missing Enrollment: Student - {student.get('student_id')}, skipping student.")
            continue

        for course in currentStudentProgram.program_courses:
            versionList.append(get_current_version(processedEnrollments, course, verbose))
            if verbose:
                logger.info(f"Determine Version by course: {course} - {versionList[-1]}")

            # append whole object for calculations to determine competency matching
            studentPaceProgress.versions.append(versionList[-1])

        studentPaceProgress.calculate_progress(verbose)
        processedStudents.append(studentPaceProgress)

    logger.info("Finished Calculating Student Progress Data.")
    return processedStudents
