from optparse import OptionParser
import time

from propus.aws.ssm import AWS_SSM
from propus.panda_doc import PandaDoc


FIELD_MAP = {
    "T2T CRM Admin": "Transition to Technology: CRM Platform Administration",
    "IT Support": "IT Support",
    "Data Analysis": "Introduction to Data Analysis",
}

COURSE_MAP = {
    "Data Analysis": "BUS500 - Introduction to Structured Data\nBUS501 - Application of Structured Data",
    "T2T CRM Admin": "IT520 - Customer Relationship Management (CRM) Technology\n"
    "IT525 - Customer Relationship Management (CRM) Platform Administration",
    "IT Support": "IT Support\nWF500 - College and Career Essential Skills",
}

CERT_MAP = {
    "Data Analysis": "Certificate of Competency in Introduction to Data Analysis",
    "T2T CRM Admin": "Salesforce Administrator credential",
    "IT Support": "CompTIA A+",
}


def fetch_args():
    parser = OptionParser()
    parser.add_option("-c", "--ccc_ids", dest="ccc_ids", help="Comma Delimited List of Student CCCIDs", type="string")
    parser.add_option(
        "-e", "--env", dest="env", help="Environment on when to send the CSEP", type="string", default="stage"
    )
    options, _ = parser.parse_args()
    if not options.ccc_ids:
        parser.error("List of CCC IDs not supplied")
    if options.env not in ["stage", "prod"]:
        parser.error("ENV must be stage or prod")
    return vars(options)


def fetch_student_data(ssm, cccid):
    from propus.salesforce import Salesforce

    salesforce = Salesforce.build_v2("stage", ssm)
    results = salesforce.custom_query(
        "select FirstName, LastName, cfg_Calbright_Email__c, cfg_Intended_Program__c"
        f" from Contact WHERE cfg_CCC_ID__c ='{cccid}'"
    )
    if results.get("totalSize") == 0:
        raise Exception("no matching student in sandbox salesforce")
    student = results.get("records")[0]
    return (
        student.get("FirstName"),
        student.get("LastName"),
        student.get("cfg_Calbright_Email__c"),
        student.get("cfg_Intended_Program__c"),
    )


def send_panda_doc(cccid, env):
    ssm = AWS_SSM.build()
    pd = PandaDoc.build(ssm.get_param("pandadoc.sandbox"))
    fname, lname, email, intended_program = fetch_student_data(ssm, cccid)
    email_name = "[WIP] DEV CSEP - testing"
    template_id = "znUZWaD6wReCLNH6ckvgJD"
    if env == "prod":
        email_name = "CSEP - PROD - Testing"
        template_id = "AYPN8iV8PeVahkVf9hzRMN"

    resp = pd.create_document_from_template(
        template_id=template_id,
        email_name=email_name,
        recipient_first_name=fname,
        recipient_last_name=lname,
        recipient_email=email,
        tokens=[
            {"name": "Student.Name", "value": f"{fname} {lname}"},
            {"name": "Student.CCCID", "value": cccid},
            {"name": "Student.CalbrightEmail", "value": email},
            {"name": "Student.ProgramName", "value": FIELD_MAP.get(intended_program)},
            {
                "name": "Student.ProgramCourses",
                "value": COURSE_MAP.get(intended_program),
            },
            {"name": "Student.ProgramIndustryCert", "value": CERT_MAP.get(intended_program)},
        ],
    )
    time.sleep(5)
    pd.send_document(
        doc_id=resp.get("id"),
        subject="Test CSEP",
        message="Please complete the CSEP document",
    )
    print(f"Sent a csep for {cccid}")


if __name__ == "__main__":
    args = fetch_args()
    for ccc_id in args.get("ccc_ids").replace(" ", "").split(","):
        send_panda_doc(ccc_id, args.get("env"))
