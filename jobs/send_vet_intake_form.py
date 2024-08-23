from optparse import OptionParser
from datetime import datetime

from propus.aws.ssm import AWS_SSM
from propus.hubspot import Hubspot
from propus.salesforce import Salesforce


def fetch_args():
    parser = OptionParser()
    parser.add_option("-c", "--cccid", dest="cccid", help="Student CCCID", type="string")
    options, _ = parser.parse_args()
    if not options.cccid or len(options.cccid) == 0:
        parser.error("CCCID not supplied")
    return vars(options)


def fetch_student_data(salesforce, cccid):
    results = salesforce.custom_query(
        f"""SELECT Id, FirstName, cfg_Calbright_Email__c, (Select Id From Veteran_Service_Records__r)
        FROM Contact WHERE cfg_CCC_ID__c  = '{cccid}'"""
    )
    if results.get("totalSize") == 0:
        raise Exception(f"no matching student in salesforce with cccid {cccid}")
    student = results.get("records")[0]

    if not student.get("cfg_Calbright_Email__c"):
        raise Exception(f"Student {cccid} does not have a calbright email")
    return (
        student.get("Id"),
        student.get("FirstName"),
        student.get("cfg_Calbright_Email__c"),
        student.get("Veteran_Service_Records__r"),
    )


def send_veteran_intake_form(cccid):
    ssm = AWS_SSM.build()
    salesforce = Salesforce.build(**ssm.get_param(parameter_name="salesforce.propus.prod", param_type="json"))
    sf_id, first_name, student_email, vet_record = fetch_student_data(salesforce, cccid)
    #  Create a new Veteran Record in Salesforce (Add date completed for when Veteran intake form was sent)
    if vet_record is None:
        salesforce.create_vet_record(sf_id, intake_form_sent=datetime.now().isoformat() + "Z")

    hubspot = Hubspot.build(ssm.get_param("hubspot.production"))
    #   Send them the intake form to fill out
    hubspot.send_transactional_email(
        email_id=115635608160,
        to_email=student_email,
        custom_properties={
            "first_name": first_name,
        },
    )


if __name__ == "__main__":
    send_veteran_intake_form(**fetch_args())
