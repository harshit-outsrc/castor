import os
from propus.calbright_sql.calbright import Calbright
from propus.aws.ssm import AWS_SSM
from propus.logging_utility import Logging


class CalbrightPSQL:
    def __init__(self):
        self.logger = Logging.get_logger(
            "castor/lambda_functions/cccapply_student_application_ingestion/src/process_postgres"
        )

    def ingest_student_applications(self, student_records):
        """ingestion process for student applications that need to be added to PSQL

        Args:
            student_records (List[dict]): List of dict values for student applications that need to be ingested
        """

        try:
            if student_records:
                student_applicants = self.validate_new_student_applications(student_records)
                calbright_engine = self.create_postgres_engine()
                calbright_engine.add_all(student_applicants)

        except Exception as err:
            self.logger.error(f" - Error during ingest_student_applications: {err}")
            raise err

    def create_postgres_engine(self):
        try:
            if os.environ.get("localhost"):
                calbright_postgres = Calbright.build(
                    {
                        "db": os.environ.get("DB"),
                        "host": "localhost",
                        "user": os.environ.get("USER"),
                        "password": os.environ.get("PASSWORD"),
                    },
                    verbose=False,
                )
            else:
                ssm = AWS_SSM.build("us-west-2")
                psql_staging_creds = ssm.get_param(f'psql.calbright.{os.environ.get("env")}.write', "json")
                calbright_postgres = Calbright.build(psql_staging_creds, verbose=False)
            return calbright_postgres
        except Exception as err:
            self.logger.error(f" - Error during create_postgres_engine: {err}")
            raise err

    def validate_new_student_applications(self, student_applicants: list):
        """validation process for student applications being applicable to ccc_application sqlalchemy model

        Args:
            student_applicants (list): list of student applications
        """

        ccc_applications = [
            self.apply_to_ccc_application(student_applicant) for student_applicant in student_applicants
        ]
        return ccc_applications

    def apply_to_ccc_application(self, student_applicant: dict):
        """applying student application to ccc_application sqlalchemy model

        Args:
            student_applicant (dict): dict value of student application
        """

        applicant = Calbright.CCCApplication()

        applicant.app_id = student_applicant.get("APP_ID")
        applicant.accepted_terms = self.convert_oracle_bool(student_applicant.get("ACCEPTED_TERMS"))
        applicant.accepted_terms_tstmp = student_applicant.get("ACCEPTED_TERMS_TSTMP")
        applicant.ccc_id = student_applicant.get("CCC_ID")
        applicant.ip_addr_acct_create = student_applicant.get("IP_ADDR_ACCT_CREATE")
        applicant.ip_addr_app_create = student_applicant.get("IP_ADDR_APP_CREATE")
        applicant.status = student_applicant.get("STATUS")
        applicant.college_id = student_applicant.get("COLLEGE_ID")
        applicant.term_id = student_applicant.get("TERM_ID")
        applicant.major_id = student_applicant.get("MAJOR_ID")
        applicant.intended_major = student_applicant.get("INTENDED_MAJOR")
        applicant.edu_goal = student_applicant.get("EDU_GOAL")
        applicant.highest_edu_level = student_applicant.get("HIGHEST_EDU_LEVEL")
        applicant.consent_indicator = self.convert_oracle_bool(student_applicant.get("CONSENT_INDICATOR"))
        applicant.app_lang = student_applicant.get("APP_LANG")
        applicant.ack_fin_aid = self.convert_oracle_bool(student_applicant.get("ACK_FIN_AID"))
        applicant.fin_aid_ref = student_applicant.get("FIN_AID_REF")
        applicant.confirmation = student_applicant.get("CONFIRMATION")
        applicant.streetaddress1 = student_applicant.get("STREETADDRESS1")
        applicant.streetaddress2 = student_applicant.get("STREETADDRESS2")
        applicant.city = student_applicant.get("CITY")
        applicant.postalcode = student_applicant.get("POSTALCODE")
        applicant.state = student_applicant.get("STATE")
        applicant.nonusaprovince = student_applicant.get("NONUSAPROVINCE")
        applicant.country = student_applicant.get("COUNTRY")
        applicant.non_us_address = self.convert_oracle_bool(student_applicant.get("NON_US_ADDRESS"))
        applicant.address_val_override = self.convert_oracle_bool(student_applicant.get("ADDRESS_VAL_OVERRIDE"))
        applicant.address_val_over_tstmp = student_applicant.get("ADDRESS_VAL_OVER_TSTMP")
        applicant.email = student_applicant.get("EMAIL")
        applicant.email_verified = self.convert_oracle_bool(student_applicant.get("EMAIL_VERIFIED"))
        applicant.email_verified_tstmp = student_applicant.get("EMAIL_VERIFIED_TSTMP")
        applicant.perm_streetaddress1 = student_applicant.get("PERM_STREETADDRESS1")
        applicant.perm_streetaddress2 = student_applicant.get("PERM_STREETADDRESS2")
        applicant.perm_city = student_applicant.get("PERM_CITY")
        applicant.perm_postalcode = student_applicant.get("PERM_POSTALCODE")
        applicant.perm_state = student_applicant.get("PERM_STATE")
        applicant.perm_nonusaprovince = student_applicant.get("PERM_NONUSAPROVINCE")
        applicant.perm_country = student_applicant.get("PERM_COUNTRY")
        applicant.address_same = self.convert_oracle_bool(student_applicant.get("ADDRESS_SAME"))
        applicant.mainphone = student_applicant.get("MAINPHONE")
        applicant.phone_verified = self.convert_oracle_bool(student_applicant.get("PHONE_VERIFIED"))
        applicant.phone_verified_tstmp = student_applicant.get("PHONE_VERIFIED_TSTMP")
        applicant.phone_type = student_applicant.get("PHONE_TYPE")
        applicant.pref_contact_method = student_applicant.get("PREF_CONTACT_METHOD")
        applicant.enroll_status = student_applicant.get("ENROLL_STATUS")
        applicant.hs_edu_level = student_applicant.get("HS_EDU_LEVEL")
        applicant.hs_comp_date = student_applicant.get("HS_COMP_DATE")
        applicant.higher_edu_level = student_applicant.get("HIGHER_EDU_LEVEL")
        applicant.higher_comp_date = student_applicant.get("HIGHER_COMP_DATE")
        applicant.cahs_graduated = self.convert_oracle_bool(student_applicant.get("CAHS_GRADUATED"))
        applicant.cahs_3year = self.convert_oracle_bool(student_applicant.get("CAHS_3YEAR"))
        applicant.hs_name = student_applicant.get("HS_NAME")
        applicant.hs_state = student_applicant.get("HS_STATE")
        applicant.hs_country = student_applicant.get("HS_COUNTRY")
        applicant.hs_cds = student_applicant.get("HS_CDS")
        applicant.hs_ceeb = student_applicant.get("HS_CEEB")
        applicant.hs_not_listed = self.convert_oracle_bool(student_applicant.get("HS_NOT_LISTED"))
        applicant.college_count = student_applicant.get("COLLEGE_COUNT")
        applicant.hs_attendance = student_applicant.get("HS_ATTENDANCE")
        applicant.coenroll_confirm = self.convert_oracle_bool(student_applicant.get("COENROLL_CONFIRM"))
        applicant.gender = student_applicant.get("GENDER")
        applicant.pg_firstname = student_applicant.get("PG_FIRSTNAME")
        applicant.pg_lastname = student_applicant.get("PG_LASTNAME")
        applicant.pg_rel = student_applicant.get("PG_REL")
        applicant.pg1_edu = student_applicant.get("PG1_EDU")
        applicant.pg2_edu = student_applicant.get("PG2_EDU")
        applicant.pg_edu_mis = student_applicant.get("PG_EDU_MIS")
        applicant.under19_ind = self.convert_oracle_bool(student_applicant.get("UNDER19_IND"))
        applicant.dependent_status = student_applicant.get("DEPENDENT_STATUS")
        applicant.race_ethnic = student_applicant.get("RACE_ETHNIC")
        applicant.hispanic = self.convert_oracle_bool(student_applicant.get("HISPANIC"))
        applicant.race_group = student_applicant.get("RACE_GROUP")
        applicant.race_ethnic_full = student_applicant.get("RACE_ETHNIC_FULL")
        applicant.ssn = student_applicant.get("SSN")
        applicant.birthdate = student_applicant.get("BIRTHDATE")
        applicant.firstname = student_applicant.get("FIRSTNAME")
        applicant.middlename = student_applicant.get("MIDDLENAME")
        applicant.lastname = student_applicant.get("LASTNAME")
        applicant.suffix = student_applicant.get("SUFFIX")
        applicant.otherfirstname = student_applicant.get("OTHERFIRSTNAME")
        applicant.othermiddlename = student_applicant.get("OTHERMIDDLENAME")
        applicant.otherlastname = student_applicant.get("OTHERLASTNAME")
        applicant.citizenship_status = student_applicant.get("CITIZENSHIP_STATUS")
        applicant.alien_reg_number = student_applicant.get("ALIEN_REG_NUMBER")
        applicant.visa_type = student_applicant.get("VISA_TYPE")
        applicant.no_documents = self.convert_oracle_bool(student_applicant.get("NO_DOCUMENTS"))
        applicant.alien_reg_issue_date = student_applicant.get("ALIEN_REG_ISSUE_DATE")
        applicant.alien_reg_expire_date = student_applicant.get("ALIEN_REG_EXPIRE_DATE")
        applicant.alien_reg_no_expire = self.convert_oracle_bool(student_applicant.get("ALIEN_REG_NO_EXPIRE"))
        applicant.military_status = student_applicant.get("MILITARY_STATUS")
        applicant.military_discharge_date = student_applicant.get("MILITARY_DISCHARGE_DATE")
        applicant.military_home_state = student_applicant.get("MILITARY_HOME_STATE")
        applicant.military_home_country = student_applicant.get("MILITARY_HOME_COUNTRY")
        applicant.military_ca_stationed = self.convert_oracle_bool(student_applicant.get("MILITARY_CA_STATIONED"))
        applicant.military_legal_residence = student_applicant.get("MILITARY_LEGAL_RESIDENCE")
        applicant.ca_res_2_years = self.convert_oracle_bool(student_applicant.get("CA_RES_2_YEARS"))
        applicant.ca_date_current = student_applicant.get("CA_DATE_CURRENT")
        applicant.ca_not_arrived = self.convert_oracle_bool(student_applicant.get("CA_NOT_ARRIVED"))
        applicant.ca_college_employee = self.convert_oracle_bool(student_applicant.get("CA_COLLEGE_EMPLOYEE"))
        applicant.ca_school_employee = self.convert_oracle_bool(student_applicant.get("CA_SCHOOL_EMPLOYEE"))
        applicant.ca_seasonal_ag = self.convert_oracle_bool(student_applicant.get("CA_SEASONAL_AG"))
        applicant.ca_outside_tax = self.convert_oracle_bool(student_applicant.get("CA_OUTSIDE_TAX"))
        applicant.ca_outside_tax_year = student_applicant.get("CA_OUTSIDE_TAX_YEAR")
        applicant.ca_outside_voted = self.convert_oracle_bool(student_applicant.get("CA_OUTSIDE_VOTED"))
        applicant.ca_outside_voted_year = student_applicant.get("CA_OUTSIDE_VOTED_YEAR")
        applicant.ca_outside_college = self.convert_oracle_bool(student_applicant.get("CA_OUTSIDE_COLLEGE"))
        applicant.ca_outside_college_year = student_applicant.get("CA_OUTSIDE_COLLEGE_YEAR")
        applicant.ca_outside_lawsuit = self.convert_oracle_bool(student_applicant.get("CA_OUTSIDE_LAWSUIT"))
        applicant.ca_outside_lawsuit_year = student_applicant.get("CA_OUTSIDE_LAWSUIT_YEAR")
        applicant.res_status = student_applicant.get("RES_STATUS")
        applicant.res_status_change = student_applicant.get("RES_STATUS_CHANGE")
        applicant.res_prev_date = student_applicant.get("RES_PREV_DATE")
        applicant.adm_ineligible = student_applicant.get("ADM_INELIGIBLE")
        applicant.elig_ab540 = self.convert_oracle_bool(student_applicant.get("ELIG_AB540"))
        applicant.res_area_a = student_applicant.get("RES_AREA_A")
        applicant.res_area_b = student_applicant.get("RES_AREA_B")
        applicant.res_area_c = student_applicant.get("RES_AREA_C")
        applicant.res_area_d = student_applicant.get("RES_AREA_D")
        applicant.experience = student_applicant.get("EXPERIENCE")
        applicant.recommend = student_applicant.get("RECOMMEND")
        applicant.comments = student_applicant.get("COMMENTS")
        applicant.comfortable_english = self.convert_oracle_bool(student_applicant.get("COMFORTABLE_ENGLISH"))
        applicant.financial_assistance = self.convert_oracle_bool(student_applicant.get("FINANCIAL_ASSISTANCE"))
        applicant.tanf_ssi_ga = self.convert_oracle_bool(student_applicant.get("TANF_SSI_GA"))
        applicant.foster_youths = self.convert_oracle_bool(student_applicant.get("FOSTER_YOUTHS"))
        applicant.academic_counseling = self.convert_oracle_bool(student_applicant.get("ACADEMIC_COUNSELING"))
        applicant.basic_skills = self.convert_oracle_bool(student_applicant.get("BASIC_SKILLS"))
        applicant.calworks = self.convert_oracle_bool(student_applicant.get("CALWORKS"))
        applicant.career_planning = self.convert_oracle_bool(student_applicant.get("CAREER_PLANNING"))
        applicant.child_care = self.convert_oracle_bool(student_applicant.get("CHILD_CARE"))
        applicant.counseling_personal = self.convert_oracle_bool(student_applicant.get("COUNSELING_PERSONAL"))
        applicant.dsps = self.convert_oracle_bool(student_applicant.get("DSPS"))
        applicant.eops = self.convert_oracle_bool(student_applicant.get("EOPS"))
        applicant.esl = self.convert_oracle_bool(student_applicant.get("ESL"))
        applicant.health_services = self.convert_oracle_bool(student_applicant.get("HEALTH_SERVICES"))
        applicant.housing_info = self.convert_oracle_bool(student_applicant.get("HOUSING_INFO"))
        applicant.employment_assistance = self.convert_oracle_bool(student_applicant.get("EMPLOYMENT_ASSISTANCE"))
        applicant.online_classes = self.convert_oracle_bool(student_applicant.get("ONLINE_CLASSES"))
        applicant.reentry_program = self.convert_oracle_bool(student_applicant.get("REENTRY_PROGRAM"))
        applicant.scholarship_info = self.convert_oracle_bool(student_applicant.get("SCHOLARSHIP_INFO"))
        applicant.student_government = self.convert_oracle_bool(student_applicant.get("STUDENT_GOVERNMENT"))
        applicant.testing_assessment = self.convert_oracle_bool(student_applicant.get("TESTING_ASSESSMENT"))
        applicant.transfer_info = self.convert_oracle_bool(student_applicant.get("TRANSFER_INFO"))
        applicant.tutoring_services = self.convert_oracle_bool(student_applicant.get("TUTORING_SERVICES"))
        applicant.veterans_services = self.convert_oracle_bool(student_applicant.get("VETERANS_SERVICES"))
        applicant.col1_ceeb = student_applicant.get("COL1_CEEB")
        applicant.col1_cds = student_applicant.get("COL1_CDS")
        applicant.col1_not_listed = self.convert_oracle_bool(student_applicant.get("COL1_NOT_LISTED"))
        applicant.col1_name = student_applicant.get("COL1_NAME")
        applicant.col1_degree_date = student_applicant.get("COL1_DEGREE_DATE")
        applicant.col1_degree_obtained = student_applicant.get("COL1_DEGREE_OBTAINED")
        applicant.col2_ceeb = student_applicant.get("COL2_CEEB")
        applicant.col2_cds = student_applicant.get("COL2_CDS")
        applicant.col2_not_listed = self.convert_oracle_bool(student_applicant.get("COL2_NOT_LISTED"))
        applicant.col2_name = student_applicant.get("COL2_NAME")
        applicant.col2_degree_date = student_applicant.get("COL2_DEGREE_DATE")
        applicant.col2_degree_obtained = student_applicant.get("COL2_DEGREE_OBTAINED")
        applicant.college_name = student_applicant.get("COLLEGE_NAME")
        applicant.district_name = student_applicant.get("DISTRICT_NAME")
        applicant.term_code = student_applicant.get("TERM_CODE")
        applicant.term_description = student_applicant.get("TERM_DESCRIPTION")
        applicant.major_code = student_applicant.get("MAJOR_CODE")
        applicant.major_description = student_applicant.get("MAJOR_DESCRIPTION")
        applicant.tstmp_submit = student_applicant.get("TSTMP_SUBMIT")
        applicant.tstmp_create = student_applicant.get("TSTMP_CREATE")
        applicant.tstmp_update = student_applicant.get("TSTMP_UPDATE")
        applicant.ssn_display = student_applicant.get("SSN_DISPLAY")
        applicant.foster_youth_status = student_applicant.get("FOSTER_YOUTH_STATUS")
        applicant.foster_youth_preference = self.convert_oracle_bool(student_applicant.get("FOSTER_YOUTH_PREFERENCE"))
        applicant.foster_youth_mis = self.convert_oracle_bool(student_applicant.get("FOSTER_YOUTH_MIS"))
        applicant.foster_youth_priority = self.convert_oracle_bool(student_applicant.get("FOSTER_YOUTH_PRIORITY"))
        applicant.tstmp_download = student_applicant.get("TSTMP_DOWNLOAD")
        applicant.address_validation = student_applicant.get("ADDRESS_VALIDATION")
        applicant.mail_addr_validation_ovr = self.convert_oracle_bool(student_applicant.get("MAIL_ADDR_VALIDATION_OVR"))
        applicant.zip4 = student_applicant.get("ZIP4")
        applicant.perm_address_validation = student_applicant.get("PERM_ADDRESS_VALIDATION")
        applicant.perm_zip4 = student_applicant.get("PERM_ZIP4")
        applicant.discharge_type = student_applicant.get("DISCHARGE_TYPE")
        applicant.college_expelled_summary = self.convert_oracle_bool(student_applicant.get("COLLEGE_EXPELLED_SUMMARY"))
        applicant.col1_expelled_status = self.convert_oracle_bool(student_applicant.get("COL1_EXPELLED_STATUS"))
        applicant.col2_expelled_status = self.convert_oracle_bool(student_applicant.get("COL2_EXPELLED_STATUS"))
        applicant.rdd = student_applicant.get("RDD")
        applicant.ssn_type = student_applicant.get("SSN_TYPE")
        applicant.military_stationed_ca_ed = self.convert_oracle_bool(student_applicant.get("MILITARY_STATIONED_CA_ED"))
        applicant.ip_address = student_applicant.get("IP_ADDRESS")
        applicant.campaign1 = student_applicant.get("CAMPAIGN1")
        applicant.campaign2 = student_applicant.get("CAMPAIGN2")
        applicant.campaign3 = student_applicant.get("CAMPAIGN3")
        applicant.orientation_encrypted = student_applicant.get("ORIENTATION_ENCRYPTED")
        applicant.transgender_encrypted = student_applicant.get("TRANSGENDER_ENCRYPTED")
        applicant.ssn_exception = self.convert_oracle_bool(student_applicant.get("SSN_EXCEPTION"))
        applicant.preferred_firstname = student_applicant.get("PREFERRED_FIRSTNAME")
        applicant.preferred_name = self.convert_oracle_bool(student_applicant.get("PREFERRED_NAME"))
        applicant.ssn_no = self.convert_oracle_bool(student_applicant.get("SSN_NO"))
        applicant.grade_point_average = student_applicant.get("GRADE_POINT_AVERAGE")
        applicant.highest_english_course = student_applicant.get("HIGHEST_ENGLISH_COURSE")
        applicant.highest_english_grade = student_applicant.get("HIGHEST_ENGLISH_GRADE")
        applicant.highest_math_course_taken = student_applicant.get("HIGHEST_MATH_COURSE_TAKEN")
        applicant.highest_math_taken_grade = student_applicant.get("HIGHEST_MATH_TAKEN_GRADE")
        applicant.highest_math_course_passed = student_applicant.get("HIGHEST_MATH_COURSE_PASSED")
        applicant.highest_math_passed_grade = student_applicant.get("HIGHEST_MATH_PASSED_GRADE")
        applicant.hs_cds_full = student_applicant.get("HS_CDS_FULL")
        applicant.col1_cds_full = student_applicant.get("COL1_CDS_FULL")
        applicant.col2_cds_full = student_applicant.get("COL2_CDS_FULL")
        applicant.ssid = student_applicant.get("SSID")
        applicant.no_perm_address_homeless = self.convert_oracle_bool(student_applicant.get("NO_PERM_ADDRESS_HOMELESS"))
        applicant.no_mailing_address_homeless = self.convert_oracle_bool(
            student_applicant.get("NO_MAILING_ADDRESS_HOMELESS")
        )
        applicant.term_start = student_applicant.get("TERM_START")
        applicant.term_end = student_applicant.get("TERM_END")
        applicant.homeless_youth = self.convert_oracle_bool(student_applicant.get("HOMELESS_YOUTH"))
        applicant.cip_code = student_applicant.get("CIP_CODE")
        applicant.major_category = student_applicant.get("MAJOR_CATEGORY")
        applicant.mainphoneintl = student_applicant.get("MAINPHONEINTL")
        applicant.secondphoneintl = student_applicant.get("SECONDPHONEINTL")
        applicant.non_credit = self.convert_oracle_bool(student_applicant.get("NON_CREDIT"))
        applicant.fraud_score = student_applicant.get("FRAUD_SCORE")
        applicant.fraud_status = student_applicant.get("FRAUD_STATUS")
        applicant.highest_grade_completed = student_applicant.get("HIGHEST_GRADE_COMPLETED")
        applicant.current_jobs = student_applicant.get("SUPP_MENU_01")
        applicant.current_job_hours = student_applicant.get("SUPP_TEXT_04")
        applicant.background_has_dependent = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_12"))
        applicant.background_immigrant = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_13"))
        applicant.background_military_veteran = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_14"))
        applicant.background_recent_job_impact = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_15"))
        applicant.background_incarcerated = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_17"))
        applicant.reason_online_program = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_18"))
        applicant.reason_skill_jobs = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_19"))
        applicant.reason_affordable = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_22"))
        applicant.reason_non_traditional_schedule = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_20"))
        applicant.reason_caregiving_responsibilities = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_21"))
        applicant.reason_other = student_applicant.get("SUPP_TEXT_05")
        applicant.available_mornings = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_05"))
        applicant.available_afternoons = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_06"))
        applicant.available_evenings = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_07"))
        applicant.available_weekends = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_08"))
        applicant.contact_email = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_09"))
        applicant.contact_phone_call = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_10"))
        applicant.contact_text_message = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_11"))
        applicant.acceptable_use_policy = self.convert_oracle_bool(student_applicant.get("SUPP_CHECK_04"))

        return applicant

    def convert_oracle_bool(key, value):
        if value == "Y" or value == "T" or value == "1" or value == "True":
            return True
        elif value == "N" or value == "F" or value == "0" or value == "False":
            return False
        else:
            return None
