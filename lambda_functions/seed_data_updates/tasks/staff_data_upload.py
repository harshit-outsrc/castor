from . import read_s3_csv
from copy import deepcopy
from sqlalchemy import select

from propus.calbright_sql.course import Course
from propus.calbright_sql.instructor_course import InstructorCourse, InstructorType
from propus.calbright_sql.staff import Staff, StaffTitle, StaffRole
from propus.calbright_sql.user import User
from propus.helpers.sql_alchemy import update_or_create


def staff_data_upload(s3, key, stage_session, prod_session):
    data = read_s3_csv(s3.s3_client, key)
    staff_data = []
    for row in data:
        row["active_staff"] = row.get("active_staff") == "TRUE"
        row["canvas_instructor"] = row.get("canvas_instructor") == "TRUE"
        for key in ["primary_instructor", "adjunct_instructor"]:
            row[key] = row.get(key).replace(" ", "").split(",") if row.get(key) else None
        staff_data.append(row)

    ingest_staff_data(deepcopy(staff_data), stage_session)
    print("STAGE) Staff Data Upserted Successfully")
    ingest_staff_data(staff_data, prod_session)
    print("PROD) Staff Data Upserted Successfully")


def ingest_staff_data(staff_data, session):
    all_staff = session.scalars(select(Staff)).all()
    staff_dict = {staff.user.calbright_email: staff for staff in all_staff}
    course_dict = {course.course_code: course for course in session.scalars(select(Course)).all()}

    staff_title_map = {s.value: s for s in StaffTitle}
    staff_items = ["calendly_link", "staff_slack_link", "active_staff"]
    unused_cols = [
        "name",
        "title",
        "calendly_link",
        "role",
        "active_staff",
        "staff_slack_link",
        "courses_instructed",
        "availability",
        "primary_instructor",
        "adjunct_instructor",
        "canvas_instructor",
    ]

    for staff in staff_data:
        staff_id = None
        user_id = None
        if staff_dict.get(staff.get("calbright_email")):
            staff_id = staff_dict.get(staff.get("calbright_email")).id
            user_id = staff_dict.get(staff.get("calbright_email")).user.id
            if not staff.get("active_staff"):
                staff_dict.get(staff.get("calbright_email")).active_staff = False
                continue

        staff_data = {"staff_title": staff_title_map.get(staff.get("title"))}
        if staff.get("role"):
            staff_data["staff_role"] = (
                StaffRole.veteran if staff.get("role") == "Veteran Services" else StaffRole.accessability
            )
        staff_data |= {item: staff.get(item) for item in staff_items if staff.get(item)}
        staff_data["availability"] = (
            ",".join(staff.get("availability").replace(" ", "").split(";")) if staff.get("availability") else None
        )

        obj, _ = update_or_create(session, Staff, staff_data, id=staff_id)

        for key in ["primary_instructor", "adjunct_instructor"]:
            if not staff.get(key):
                continue

            # Delete Courses Instructor No Longer Teaching
            current_courses = {ic.course.course_code: ic for ic in obj.instructor_course}
            for course in set(current_courses.keys()) - set(staff.get(key)):
                current_courses.get(course).active = False

            # Upsert Courses Instructor is Teaching
            for course in staff.get(key):
                course_data = course_dict.get(course)
                if not course_data:
                    raise Exception(f"Course {course} not found")
                instructor_course = {
                    "course_id": course_data.id,
                    "instructor_id": obj.id,
                    "instructor_type": (
                        InstructorType.adjunct if key == "adjunct_instructor" else InstructorType.primary
                    ),
                    "canvas_instructor": staff.get("canvas_instructor"),
                    "active": True,
                }
                update_or_create(
                    session,
                    InstructorCourse,
                    instructor_course,
                    course_id=instructor_course.get("course_id"),
                    instructor_id=instructor_course.get("instructor_id"),
                )

        staff["staff"] = obj
        if staff.get("name"):
            name_split = staff.get("name", "").split()
            staff["first_name"] = name_split[0]
            staff["last_name"] = " ".join(name_split[1:])

        for key in unused_cols:
            if key in staff:
                del staff[key]

        update_or_create(session, User, staff, id=user_id)

        if staff_dict.get(staff.get("calbright_email")):
            del staff_dict[staff.get("calbright_email")]
    for staff in staff_dict.values():
        staff.active_staff = False
    session.commit()
