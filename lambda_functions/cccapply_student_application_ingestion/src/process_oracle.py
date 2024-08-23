import oracledb
from propus.logging_utility import Logging
from propus.aws.ssm import AWS_SSM


class CCCApplyOracleDB:
    def __init__(self):
        self.logger = Logging.get_logger(
            "castor/lambda_functions/cccapply_student_application_ingestion/src/process_oracle"
        )
        self.new_student_applicants_exist = False
        self.new_student_applicants = []
        self.student_records = []

    def query_student_applications_for_ingestion(self):
        try:
            with self.connect_oracle() as connection:
                self.check_new_student_applications(connection)
                if self.new_student_applicants_exist:
                    self.lookup_student_application(connection, self.new_student_applicants)
            return self.student_records

        except oracledb.Error or Exception as err:
            self.logger.error(f" - Error during query_student_applications_for_ingestion: {err}")
            raise err

    def finish_processing_ingested_records(self):
        try:
            with self.connect_oracle() as connection:
                if self.new_student_applicants_exist:
                    self.update_ingested_student_applications(connection, self.new_student_applicants)
        except oracledb.Error or Exception as err:
            self.logger.error(f"Error during finish_processing_ingested_records: {err}")
            raise err

    def connect_oracle(self):
        try:
            ssm = AWS_SSM.build("us-west-2")
            oracle_staging_creds = ssm.get_param("oracle.calbright-staging.root", "json")
            oracle_connection = oracledb.connect(
                user=oracle_staging_creds.get("username"),
                password=oracle_staging_creds.get("password"),
                dsn=oracle_staging_creds.get("dns"),
            )
            return oracle_connection
        except oracledb.Error or Exception as err:
            self.logger.error(f" - Error during connect_oracle: {err}")
            raise err

    def check_new_student_applications(self, oracle_connection):
        """check to see if ingestable student records exist and get the APP_IDs

        Args:
            oracle_connection (Connection): Oracle DB Connection
        """

        with oracle_connection.cursor() as cursor:
            sql = """select APP_ID from CCCTCUSER_STAGING.STAGING_STUDENT_APPLICATIONS where INGESTED_RECORD = 0"""
            cursor.execute(sql)
            columns = [i[0] for i in cursor.description]
            db_query = cursor.fetchall()
            if len(db_query) > 0:
                for r in db_query:
                    self.new_student_applicants.append(dict(zip(columns, r)))
                self.new_student_applicants_exist = True
            else:
                self.new_student_applicants_exist = False

    def lookup_student_application(self, oracle_connection, student_applications: list(dict())):
        """Look up list of student applications and grab specific fields that will exist in
        postgres database.

        Note: PostgreSQL has fields for ccc_application that match up differently to Oracle DB.
            those fields are determined below and should never change when updating CCCApplication.
                current_jobs = supp_menu_01
                current_job_hours = supp_text_04
                background_has_dependent = supp_check_12
                background_immigrant = supp_check_13
                background_military_veteran = supp_check_14
                background_recent_job_impact = supp_check_15
                background_incarcerated = supp_check_17
                reason_online_program = supp_check_18
                reason_skill_jobs = supp_check_19
                reason_affordable = supp_check_22
                reason_non_traditional_schedule = supp_check_20
                reason_caregiving_responsibilities = supp_check_21
                reason_other = supp_text_05
                available_mornings = supp_check_05
                available_afternoons = supp_check_06
                available_evenings = supp_check_07
                available_weekends = supp_check_08
                contact_email = supp_check_09
                contact_phone_call = supp_check_10
                contact_text_message = supp_check_11
                acceptable_use_policy = supp_check_04

        Args:
            oracle_connection (Connection): Oracle DB Connection
            student_applications (List): Student Applications that have not been ingested
        """

        sql = """select app_id, accepted_terms, accepted_terms_tstmp, ccc_id, ip_addr_acct_create, ip_addr_app_create,
                 status, college_id, term_id, major_id, intended_major, edu_goal, highest_edu_level, consent_indicator,
                 app_lang, ack_fin_aid, fin_aid_ref, confirmation, streetaddress1, streetaddress2, city, postalcode,
                 state, nonusaprovince, country, non_us_address, address_val_override, address_val_over_tstmp, email,
                 email_verified, email_verified_tstmp, perm_streetaddress1, perm_streetaddress2, perm_city,
                 perm_postalcode, perm_state, perm_nonusaprovince, perm_country, address_same, mainphone,
                 phone_verified, phone_verified_tstmp, phone_type, pref_contact_method, enroll_status, hs_edu_level,
                 hs_comp_date, higher_edu_level, higher_comp_date, cahs_graduated, cahs_3year, hs_name, hs_state,
                 hs_country, hs_cds, hs_ceeb, hs_not_listed, college_count, hs_attendance, coenroll_confirm, gender,
                 pg_firstname, pg_lastname, pg_rel, pg1_edu, pg2_edu, pg_edu_mis, under19_ind, dependent_status,
                 race_ethnic, hispanic, race_group, race_ethnic_full, ssn, birthdate, firstname, middlename, lastname,
                 suffix, otherfirstname, othermiddlename, otherlastname, citizenship_status, alien_reg_number,
                 visa_type, no_documents, alien_reg_issue_date, alien_reg_expire_date, alien_reg_no_expire,
                 military_status, military_discharge_date, military_home_state, military_home_country,
                 military_ca_stationed, military_legal_residence, ca_res_2_years, ca_date_current, ca_not_arrived,
                 ca_college_employee, ca_school_employee, ca_seasonal_ag, ca_outside_tax, ca_outside_tax_year,
                 ca_outside_voted, ca_outside_voted_year, ca_outside_college, ca_outside_college_year,
                 ca_outside_lawsuit, ca_outside_lawsuit_year, res_status, res_status_change, res_prev_date,
                 adm_ineligible, elig_ab540, res_area_a, res_area_b, res_area_c, res_area_d, experience, recommend,
                 comments, comfortable_english, financial_assistance, tanf_ssi_ga, foster_youths, academic_counseling,
                 basic_skills, calworks, career_planning, child_care, counseling_personal, dsps, eops, esl,
                 health_services, housing_info, employment_assistance, online_classes, reentry_program,
                 scholarship_info, student_government, testing_assessment, transfer_info, tutoring_services,
                 veterans_services, col1_ceeb, col1_cds, col1_not_listed, col1_name, col1_degree_date,
                 col1_degree_obtained, col2_ceeb, col2_cds, col2_not_listed, col2_name, col2_degree_date,
                 col2_degree_obtained, college_name, district_name, term_code, term_description, major_code,
                 major_description, tstmp_submit, tstmp_create, tstmp_update, ssn_display, foster_youth_status,
                 foster_youth_preference, foster_youth_mis, foster_youth_priority, tstmp_download, address_validation,
                 mail_addr_validation_ovr, zip4, perm_address_validation, perm_zip4, discharge_type,
                 college_expelled_summary, col1_expelled_status, col2_expelled_status, rdd, ssn_type,
                 military_stationed_ca_ed, ip_address, campaign1, campaign2, campaign3, orientation_encrypted,
                 transgender_encrypted, ssn_exception, preferred_firstname, preferred_name, ssn_no, grade_point_average,
                 highest_english_course, highest_english_grade, highest_math_course_taken, highest_math_taken_grade,
                 highest_math_course_passed, highest_math_passed_grade, hs_cds_full, col1_cds_full, col2_cds_full, ssid,
                 no_perm_address_homeless, no_mailing_address_homeless, term_start, term_end, homeless_youth, cip_code,
                 major_category, mainphoneintl, secondphoneintl, non_credit, fraud_score, fraud_status,
                 highest_grade_completed, supp_menu_01, supp_text_04, supp_check_12, supp_check_13, supp_check_14,
                 supp_check_15, supp_check_17, supp_check_18, supp_check_19, supp_check_22, supp_check_20,
                 supp_check_21, supp_text_05, supp_check_05, supp_check_06, supp_check_07, supp_check_08,
                 supp_check_09, supp_check_10, supp_check_11, supp_check_04
                 from CCCTCUSER_STAGING.SZRAPLY where APP_ID = ANY({0})"""

        try:
            with oracle_connection.cursor() as cursor:
                formatted_sql = sql.format(", ".join(str(sid.get("APP_ID")) for sid in student_applications))
                cursor.execute(formatted_sql)
                columns = [i[0] for i in cursor.description]
                db_query = cursor.fetchall()
                for r in db_query:
                    self.student_records.append(dict(zip(columns, r)))
        except oracledb.Error or Exception as err:
            self.logger.error(f"Error during lookup_student_application: {err}")
            raise err

    def update_ingested_student_applications(self, oracle_connection, ingested_student_applications):
        """update ingested student applications based on APP_ID previously received

        Args:
            oracle_connection (Connection): Oracle DB Connection
            ingested_student_applications (List): Ingested student application APP_IDs for STAGING_STUDENT_APPLICATIONS
        """

        try:
            sql = """update CCCTCUSER_STAGING.STAGING_STUDENT_APPLICATIONS
                     set INGESTED_RECORD = '1' where APP_ID = (:APP_ID)"""
            with oracle_connection.cursor() as cursor:
                cursor.executemany(sql, [(sid.get("APP_ID"),) for sid in ingested_student_applications])
                oracle_connection.commit()
        except oracledb.Error or Exception as err:
            self.logger.error(f"Error during update_ingested_student_applications: {err}")
            raise err
