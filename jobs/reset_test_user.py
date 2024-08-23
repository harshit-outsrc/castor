from datetime import datetime
from optparse import OptionParser
from sqlalchemy import select
from random import randint

from propus.aws.ssm import AWS_SSM
from propus.salesforce import Salesforce
from propus.calbright_sql.calbright import Calbright
from propus.calbright_sql.student import Student
from propus.calbright_sql.learner_status import LearnerStatus
from propus.calbright_sql.program import Program
from propus.helpers.salesforce import SF_PROGRAMS_OF_INTEREST_MAP


def fetch_args():
    parser = OptionParser()
    parser.add_option("-c", "--ccc_ids", dest="ccc_ids", help="Comma Delimited List of Student CCCIDs", type="string")
    parser.add_option("-e", "--env", dest="env", help="Environment", type="string", default="prod")
    parser.add_option("-r", "--reset", dest="reset_state", help="Reset State", type="string", default="app_submitted")
    parser.add_option("-p", "--program", dest="program", help="Program", type="string", default="Data Analysis")
    parser.add_option("-l", "--lms", dest="lms", help="LMS", type="string", default="Canvas")
    options, _ = parser.parse_args()
    if not options.ccc_ids:
        parser.error("CSEP not supplied")
    if options.reset_state not in ["app_submitted", "pre_csep", "started_program_pathway"]:
        parser.error("Reset State must be either 'app_submitted' or 'pre_csep'")
    if options.reset_state not in ["app_submitted"]:
        if not options.program:
            parser.error(f"Program Required for Reset State of {options.reset_state}")
    if options.program not in [
        "Cybersecurity",
        "Data Analysis",
        "IT Support",
        "Project Managment",
        "T2T CRM Admin",
        "T2T Intro to Networks",
    ]:
        parser.error(f"Program {options.program} not available")
    if options.reset_state == "started_program_pathway" and options.lms not in ["Canvas", "Strut", "default"]:
        parser.error(f"LMS {options.lms} not available")
    return vars(options)


PROGRAM_COURSE_MAPPINGS = {
    "IT Support": ["IT500", "WF500"],
    "T2T CRM Admin": ["IT520", "IT525"],
    "Career Readiness": [],
    "Cybersecurity": ["IT510", "WF500"],
    "Data Analysis": ["BUS500", "BUS501"],
    "T2T Intro to Networks": ["IT532", "IT533"],
    "HC DEI": ["HC501", "HC502"],
    "Upskilling for Equitable Health Impacts: Diversity, Equity and Inclusion": ["HC501", "HC502"],
    "Medical Coding": ["MC500", "WF500"],
    "Project Management": ["BUS520", "BUS521", "BUS522"],
}


def reset_test_user(ccc_id, env, program, reset_state, lms):
    """
    Delete the students Program Enrollments/Grade Objects (DB and SF)
    Reset Student's learner status to App Submitted
    Delete their Course information
    Delete the kickoff scheduled
    Need to delete the timestamps for enrollment and the term. But don't delete the LMS info like id and/or the CCUser
        created flags. That should be it
    Delete all Veteran Service Records
    """
    if lms == "default":
        lms = "Strut"
        if program == "Data Analysis":
            lms = "Canvas"
        elif program == "T2T CRM Admin":
            lms = "myTrailhead"

    ssm = AWS_SSM.build()
    sf = Salesforce.build_v2(env, ssm)
    calbright = Calbright.build(ssm.get_param(f"psql.calbright.{env}.write", "json"), verbose=False)
    record = sf.custom_query(f"SELECT Id From Contact WHERE Test_Demo__c = True and cfg_CCC_ID__c ='{ccc_id}'")
    if record.get("totalSize") != 1:
        raise Exception(f"No Salesforce user with CCC ID of {ccc_id} found with Test Demo Flag set to true")
    sf_id = record.get("records")[0].get("Id")
    default_configs = {
        "LMS__c": None,
        "cfg_Assigned_Learner_Advocate__c": None,
        "cfg_Intended_Program__c": program,
        "First_Strut_SAA_Timestamp__c": None,
        "Last_Strut_SAA_Timestamp__c": None,
        "Course_1__c": None,
        "Course_2__c": None,
        "Course_3__c": None,
        "Course_1_Progress__c": None,
        "Course_2_Progress__c": None,
        "Course_3_Progress__c": None,
        "IT520_Percent__c": None,
        "IT525_Percent__c": None,
    }
    sf_configs = {
        "app_submitted": {
            "cfg_Learner_Status__c": "App Submitted",
        },
        "pre_csep": {
            "cfg_Learner_Status__c": "Completed Orientation" if program == "T2T CRM Admin" else "Completed CSEP",
            "cfg_Assigned_Learner_Advocate__c": "0055G000006znXqQAI",
        },
        "started_program_pathway": {
            "cfg_Learner_Status__c": "Started Program Pathway",
            "cfg_Assigned_Learner_Advocate__c": "0055G000006znXqQAI",
            "First_Strut_SAA_Timestamp__c": datetime.now().isoformat(),
            "Last_Strut_SAA_Timestamp__c": datetime.now().isoformat(),
            "LMS__c": lms,
        },
    }
    if reset_state == "started_program_pathway":
        for idx, course in enumerate(PROGRAM_COURSE_MAPPINGS.get(program)):
            sf_configs.get(reset_state)[f"Course_{idx+1}__c"] = course
            sf_configs.get(reset_state)[f"Course_{idx+1}_Progress__c"] = randint(0, 100)

    sf.update_contact_record(
        salesforce_id=sf_id,
        Completed_Course_1__c=False,
        Completed_Course_2__c=False,
        Completed_Course_3__c=False,
        IT_520_Complete__c=False,
        IT_525_Complete__c=False,
        Kickoff_Scheduled__c=None,
        Date_of_Enrollment__c=None,
        First_Date_of_Enrollment__c=None,
        Current_Term__c=None,
        CSEP_Sent_for_Signature_Date__c=None,
        CSEP_Signed_Date__c=None,
        Accessibility_Date_Intake_Form_Signed__c=None,
        Accessibility_Intake_Form_Sent_Date__c=None,
        cfg_Chromebook_Requested__c=False,
        cfg_Hotspot_Requested__c=False,
        Device_Agreement_Signed_Date__c=None,
        Device_Requested_on_CSEP__c=False,
        Device_Agreement_Sent_For_Signature_Date__c=None,
        Has_Completed_WF500__c=False,
        hed__Do_Not_Contact__c=False,
        Leave_Start_Date__c=None,
        Leave_End_Date__c=None,
        Profile_Photo_URL__c=None,
        Prerequisite_Processed_By__c=None,
        Prerequisite_Status__c=None,
        Prerequisite_Status_Timestamp__c=None,
        SMS_Opt_Out__c=False,
        Veterans_Services_Requested__c=False,
        cfg_Learner_Status_Timestamp__c=datetime.now().isoformat(),
        cfg_Previous_Learner_Status_Timestamp__c=None,
        Program_Version__c=None,
        **(default_configs | sf_configs.get(reset_state)),
    )

    enrollments = sf.custom_query(f"SELECT Id From Program_Enrollments__c WHERE Contact__r.cfg_CCC_ID__c ='{ccc_id}'")
    for enrollment in enrollments.get("records"):
        sf.delete_program_enrollment_record(enrollment.get("Id"))

    eot_grades = sf.custom_query(f"SELECT Id From C_End_of_Term_Grade__c WHERE Student__r.cfg_CCC_ID__c ='{ccc_id}'")
    for grade in eot_grades.get("records"):
        sf.delete_end_of_term_grade(grade.get("Id"))

    vet_records = sf.fetch_vet_record_by_sf_id(sf_id)
    for vet_record in vet_records.get("records"):
        sf.delete_vet_record(vet_record.get("Id"))

    res = calbright.session.execute(select(Student).filter_by(ccc_id=ccc_id)).one_or_none()
    if not res:
        print(f"No Database Records for {ccc_id}")
        return
    student = res[0]
    student.user.learner_status = calbright.session.execute(
        select(LearnerStatus).filter_by(status=sf_configs.get(reset_state).get("cfg_Learner_Status__c"))
    ).scalar_one()
    student.user.intended_program = calbright.session.execute(
        select(Program).filter_by(short_name=SF_PROGRAMS_OF_INTEREST_MAP.get(program))
    ).scalar_one()
    for enrollment in student.enrollment_student:
        for ect in enrollment.enrollment_enrollment_course_term:
            calbright.session.delete(ect)
        for ew in enrollment.workflow_enrollment:
            calbright.session.delete(ew)
        for ec in enrollment.counselor_enrollment:
            calbright.session.delete(ec)
        for eas in enrollment.enrollment_assessment_submission:
            calbright.session.delete(eas)
        calbright.session.delete(enrollment)
    for user_lms in student.user.user_lms:
        calbright.session.delete(user_lms)

    if reset_state == "started_program_pathway":
        sf.create_program_enrollment_record(
            program_name=program,
            enrollment_status="In Progress",
            date_of_enrollment=datetime.now().isoformat(),
            contact=sf_id,
        )
        for course in PROGRAM_COURSE_MAPPINGS.get(program):
            sf.create_end_of_term_grade(
                course=course, ccc_id=ccc_id, sf_id=sf_id, term_id="a0Cca000002zxGaEAI", term_name="2024-25-TERM-03"
            )

        print("TODO: Create Enrollment/Grade Objects like grades above")

    calbright.session.commit()
    print(f"Finished updating student {ccc_id}")
    # TODO: Need to add in Canvas Deletion Stuff


if __name__ == "__main__":
    args = fetch_args()
    for ccc_id in args.get("ccc_ids").replace(" ", "").split(","):
        reset_test_user(
            ccc_id=ccc_id,
            env=args.get("env"),
            program=args.get("program"),
            reset_state=args.get("reset_state"),
            lms=args.get("lms"),
        )
