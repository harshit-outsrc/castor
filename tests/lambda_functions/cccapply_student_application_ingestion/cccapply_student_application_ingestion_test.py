import unittest
import datetime
from unittest.mock import MagicMock, Mock
from propus.calbright_sql.calbright import Calbright
from lambda_functions.cccapply_student_application_ingestion.src.process_oracle import CCCApplyOracleDB
from lambda_functions.cccapply_student_application_ingestion.src.process_postgres import CalbrightPSQL


class Row(object):
    def __init__(self, x):
        self.query_id = x


class TestIngestCCCApplyStudentApplication(unittest.TestCase):
    def setUp(self):
        self.dbc = MagicMock(name="dbconn")
        self.dbc.commit = Mock(side_effect=self.commit_ran)
        self.dbc.cursor = Mock(side_effect=self.cursor_setup)
        self.cccapply_student_application_ingestion_oracle = CCCApplyOracleDB()
        self.cccapply_student_application_ingestion_psql = CalbrightPSQL()
        self.called_executemany = False
        self.called_execute = False
        self.called_fetchall = False
        self.called_commit = False
        self.test_data_expected = [{"id": "123", "name": "john", "ccc_id": "Test1234"}]
        self.student_ingestion_records = [
            {
                "APP_ID": "12345678",
                "CCC_ID": "TEST123",
                "CREATED_AT": datetime.datetime(2020, 2, 1, 0, 0),
                "INGESTED_RECORD": 0,
            }
        ]
        self.oracle_student_dict = [
            {
                "APP_ID": 10000004,
                "ACCEPTED_TERMS": "Y",
                "ACCEPTED_TERMS_TSTMP": datetime.datetime(2023, 4, 7, 0, 0),
                "CCC_ID": "CMC9862",
                "IP_ADDR_ACCT_CREATE": "100.00.000.000",
                "IP_ADDR_APP_CREATE": "100.00.000.000",
                "STATUS": "I",
                "COLLEGE_ID": "211",
                "TERM_ID": None,
                "MAJOR_ID": None,
                "INTENDED_MAJOR": "C1",
                "EDU_GOAL": "M",
                "HIGHEST_EDU_LEVEL": "82020",
                "CONSENT_INDICATOR": "Y",
                "APP_LANG": "en",
                "ACK_FIN_AID": "Y",
                "FIN_AID_REF": None,
                "CONFIRMATION": "NC-26308281",
                "STREETADDRESS1": "123 Test st",
                "STREETADDRESS2": None,
                "CITY": "Test City",
                "POSTALCODE": "12345",
                "STATE": "CA",
                "NONUSAPROVINCE": None,
                "COUNTRY": "US",
                "NON_US_ADDRESS": "N",
                "ADDRESS_VAL_OVERRIDE": "N",
                "ADDRESS_VAL_OVER_TSTMP": None,
                "EMAIL": "stephen.teststudentchassie+stagingtest@calbrightcollege.org",
                "EMAIL_VERIFIED": "Y",
                "EMAIL_VERIFIED_TSTMP": datetime.datetime(2023, 4, 7, 0, 0),
                "PERM_STREETADDRESS1": None,
                "PERM_STREETADDRESS2": None,
                "PERM_CITY": None,
                "PERM_POSTALCODE": None,
                "PERM_STATE": None,
                "PERM_NONUSAPROVINCE": None,
                "PERM_COUNTRY": None,
                "ADDRESS_SAME": "N",
                "MAINPHONE": None,
                "PHONE_VERIFIED": "N",
                "PHONE_VERIFIED_TSTMP": None,
                "PHONE_TYPE": None,
                "PREF_CONTACT_METHOD": "email",
                "ENROLL_STATUS": "2",
                "HS_EDU_LEVEL": "3",
                "HS_COMP_DATE": datetime.datetime(2012, 1, 1, 0, 0),
                "HIGHER_EDU_LEVEL": "8",
                "HIGHER_COMP_DATE": datetime.datetime(2020, 2, 1, 0, 0),
                "CAHS_GRADUATED": "Y",
                "CAHS_3YEAR": "Y",
                "HS_NAME": "Apple Valley Christian",
                "HS_STATE": "CA",
                "HS_COUNTRY": "US",
                "HS_CDS": "690069",
                "HS_CEEB": "050122 ",
                "HS_NOT_LISTED": "N",
                "COLLEGE_COUNT": 2,
                "HS_ATTENDANCE": 1,
                "COENROLL_CONFIRM": "N",
                "GENDER": "X",
                "PG_FIRSTNAME": None,
                "PG_LASTNAME": None,
                "PG_REL": None,
                "PG1_EDU": "1",
                "PG2_EDU": "X",
                "PG_EDU_MIS": "1X",
                "UNDER19_IND": "N",
                "DEPENDENT_STATUS": "3",
                "RACE_ETHNIC": "NNNNNNNNNNNNNNNNNNNNY",
                "HISPANIC": "N",
                "RACE_GROUP": "21",
                "RACE_ETHNIC_FULL": "800,807,808",
                "SSN": None,
                "BIRTHDATE": datetime.datetime(1990, 1, 1, 0, 0),
                "FIRSTNAME": "Stephen",
                "MIDDLENAME": None,
                "LASTNAME": "StagingTest",
                "SUFFIX": None,
                "OTHERFIRSTNAME": None,
                "OTHERMIDDLENAME": None,
                "OTHERLASTNAME": None,
                "CITIZENSHIP_STATUS": "X",
                "ALIEN_REG_NUMBER": None,
                "VISA_TYPE": None,
                "NO_DOCUMENTS": "N",
                "ALIEN_REG_ISSUE_DATE": None,
                "ALIEN_REG_EXPIRE_DATE": None,
                "ALIEN_REG_NO_EXPIRE": "N",
                "MILITARY_STATUS": "X",
                "MILITARY_DISCHARGE_DATE": None,
                "MILITARY_HOME_STATE": None,
                "MILITARY_HOME_COUNTRY": None,
                "MILITARY_CA_STATIONED": None,
                "MILITARY_LEGAL_RESIDENCE": None,
                "CA_RES_2_YEARS": None,
                "CA_DATE_CURRENT": None,
                "CA_NOT_ARRIVED": None,
                "CA_COLLEGE_EMPLOYEE": None,
                "CA_SCHOOL_EMPLOYEE": None,
                "CA_SEASONAL_AG": None,
                "CA_OUTSIDE_TAX": None,
                "CA_OUTSIDE_TAX_YEAR": None,
                "CA_OUTSIDE_VOTED": None,
                "CA_OUTSIDE_VOTED_YEAR": None,
                "CA_OUTSIDE_COLLEGE": None,
                "CA_OUTSIDE_COLLEGE_YEAR": None,
                "CA_OUTSIDE_LAWSUIT": None,
                "CA_OUTSIDE_LAWSUIT_YEAR": None,
                "RES_STATUS": "N",
                "RES_STATUS_CHANGE": None,
                "RES_PREV_DATE": None,
                "ADM_INELIGIBLE": None,
                "ELIG_AB540": None,
                "RES_AREA_A": 9,
                "RES_AREA_B": 9,
                "RES_AREA_C": 9,
                "RES_AREA_D": 9,
                "EXPERIENCE": None,
                "RECOMMEND": None,
                "COMMENTS": None,
                "COMFORTABLE_ENGLISH": "Y",
                "FINANCIAL_ASSISTANCE": "Y",
                "TANF_SSI_GA": "N",
                "FOSTER_YOUTHS": None,
                "ACADEMIC_COUNSELING": "N",
                "BASIC_SKILLS": "Y",  # noqa: E501
                "CALWORKS": "N",
                "CAREER_PLANNING": "N",
                "CHILD_CARE": "N",
                "COUNSELING_PERSONAL": "N",
                "DSPS": "N",
                "EOPS": "N",
                "ESL": "N",
                "HEALTH_SERVICES": "N",
                "HOUSING_INFO": "Y",
                "EMPLOYMENT_ASSISTANCE": "N",
                "ONLINE_CLASSES": "Y",
                "REENTRY_PROGRAM": "N",
                "SCHOLARSHIP_INFO": "Y",
                "STUDENT_GOVERNMENT": "Y",
                "TESTING_ASSESSMENT": "N",
                "TRANSFER_INFO": "N",
                "TUTORING_SERVICES": "N",
                "VETERANS_SERVICES": "N",
                "COL1_CEEB": "004099 ",
                "COL1_CDS": "366184",
                "COL1_NOT_LISTED": "N",
                "COL1_NAME": "California State University, S",
                "COL1_DEGREE_DATE": datetime.datetime(2020, 2, 1, 0, 0),
                "COL1_DEGREE_OBTAINED": "B",
                "COL2_CEEB": "004932 ",
                "COL2_CDS": "365790",
                "COL2_NOT_LISTED": "N",
                "COL2_NAME": "Victor Valley College",
                "COL2_DEGREE_DATE": datetime.datetime(2016, 2, 1, 0, 0),
                "COL2_DEGREE_OBTAINED": "A",
                "COLLEGE_NAME": "Calbright College",
                "DISTRICT_NAME": None,
                "TERM_CODE": "2022-2023",
                "TERM_DESCRIPTION": "Open Enrollment for all Calbright Programs",
                "MAJOR_CODE": "C1",
                "MAJOR_DESCRIPTION": "Calbright Programs",
                "TSTMP_SUBMIT": datetime.datetime(2023, 4, 7, 20, 21, 57, 631000),
                "TSTMP_CREATE": datetime.datetime(2023, 4, 7, 20, 11, 48, 915000),
                "TSTMP_UPDATE": None,
                "SSN_DISPLAY": None,
                "FOSTER_YOUTH_STATUS": None,
                "FOSTER_YOUTH_PREFERENCE": None,
                "FOSTER_YOUTH_MIS": None,
                "FOSTER_YOUTH_PRIORITY": None,
                "TSTMP_DOWNLOAD": None,
                "ADDRESS_VALIDATION": "0",
                "MAIL_ADDR_VALIDATION_OVR": "N",
                "ZIP4": None,
                "PERM_ADDRESS_VALIDATION": None,
                "PERM_ZIP4": None,
                "DISCHARGE_TYPE": None,
                "COLLEGE_EXPELLED_SUMMARY": "N",
                "COL1_EXPELLED_STATUS": "N",
                "COL2_EXPELLED_STATUS": "N",
                "RDD": datetime.datetime(2022, 6, 30, 0, 0),
                "SSN_TYPE": None,
                "MILITARY_STATIONED_CA_ED": None,
                "IP_ADDRESS": "10.000.000.00",
                "CAMPAIGN1": "self-guided",
                "CAMPAIGN2": "https://www.calbright.org/enroll/it-step2/?user2=https://www.calbright.org/programs/cybersecurity/=stephen+stagingtest@calbright.org",  # noqa: E501
                "CAMPAIGN3": None,
                "ORIENTATION_ENCRYPTED": "5",
                "TRANSGENDER_ENCRYPTED": "3",
                "SSN_EXCEPTION": "N",
                "PREFERRED_FIRSTNAME": None,
                "PREFERRED_NAME": "N",
                "SSN_NO": "Y",
                "GRADE_POINT_AVERAGE": None,
                "HIGHEST_ENGLISH_COURSE": None,
                "HIGHEST_ENGLISH_GRADE": None,
                "HIGHEST_MATH_COURSE_TAKEN": None,
                "HIGHEST_MATH_TAKEN_GRADE": None,
                "HIGHEST_MATH_COURSE_PASSED": None,
                "HIGHEST_MATH_PASSED_GRADE": None,
                "HS_CDS_FULL": "36750776900690",
                "COL1_CDS_FULL": "36305513661840",
                "COL2_CDS_FULL": "36679263657905",
                "SSID": None,
                "NO_PERM_ADDRESS_HOMELESS": "Y",
                "NO_MAILING_ADDRESS_HOMELESS": "N",
                "TERM_START": datetime.datetime(2022, 7, 1, 0, 0),
                "TERM_END": datetime.datetime(2023, 7, 1, 0, 0),
                "HOMELESS_YOUTH": None,
                "CIP_CODE": None,
                "MAJOR_CATEGORY": None,
                "MAINPHONEINTL": None,
                "SECONDPHONEINTL": None,
                "NON_CREDIT": "Y",
                "FRAUD_SCORE": 0.426485002,
                "FRAUD_STATUS": 6,
                "HIGHEST_GRADE_COMPLETED": None,
                "SUPP_MENU_01": "2",
                "SUPP_TEXT_04": "55",
                "SUPP_CHECK_12": "Y",
                "SUPP_CHECK_13": None,
                "SUPP_CHECK_14": None,
                "SUPP_CHECK_15": "Y",
                "SUPP_CHECK_17": None,
                "SUPP_CHECK_18": "Y",
                "SUPP_CHECK_19": "Y",
                "SUPP_CHECK_22": "Y",
                "SUPP_CHECK_20": None,
                "SUPP_CHECK_21": None,
                "SUPP_TEXT_05": "Something that looked interesting",
                "SUPP_CHECK_05": "Y",
                "SUPP_CHECK_06": "Y",
                "SUPP_CHECK_07": None,
                "SUPP_CHECK_08": None,
                "SUPP_CHECK_09": "Y",
                "SUPP_CHECK_10": None,
                "SUPP_CHECK_11": None,
                "SUPP_CHECK_04": "Y",
            }
        ]  # noqa: E501

    def test_check_new_student_applications(self):
        self.cccapply_student_application_ingestion_oracle.check_new_student_applications(self.dbc)

        self.assertTrue(self.called_execute)
        self.assertTrue(self.called_fetchall)
        self.assertEqual(
            self.cccapply_student_application_ingestion_oracle.new_student_applicants, self.test_data_expected
        )
        self.assertTrue(self.cccapply_student_application_ingestion_oracle.new_student_applicants_exist)

    def test_lookup_student_application(self):
        self.cccapply_student_application_ingestion_oracle.lookup_student_application(
            self.dbc, self.student_ingestion_records
        )

        self.assertTrue(self.called_execute)
        self.assertTrue(self.called_fetchall)
        self.assertEqual(self.cccapply_student_application_ingestion_oracle.student_records, self.test_data_expected)

    def test_update_ingested_student_applications(self):
        self.cccapply_student_application_ingestion_oracle.update_ingested_student_applications(
            self.dbc, self.student_ingestion_records
        )

        self.assertTrue(self.called_executemany)
        self.assertTrue(self.called_commit)

    def test_validate_new_student_applications(self):
        result = self.cccapply_student_application_ingestion_psql.validate_new_student_applications(
            self.oracle_student_dict
        )
        self.assertIsInstance(result[0], Calbright.CCCApplication)

    def test_apply_to_ccc_application(self):
        result = self.cccapply_student_application_ingestion_psql.apply_to_ccc_application(self.oracle_student_dict[0])
        self.assertIsInstance(result, Calbright.CCCApplication)

    def test_convert_oracle_bool(self):
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("Y"), True)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("T"), True)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("1"), True)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("True"), True)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("False"), False)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("N"), False)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("F"), False)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("0"), False)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool("something"), None)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool(0), None)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool(True), None)
        self.assertEqual(self.cccapply_student_application_ingestion_psql.convert_oracle_bool(None), None)

    def executemany_update(self, sql, data):
        self.called_executemany = True

    def fetchall_ran(self):
        self.called_fetchall = True
        return [("123", "john", "Test1234")]

    def execute_ran(self, sql):
        self.called_execute = True

    def commit_ran(self):
        self.called_commit = True

    def cursor_setup(self):
        cursor = MagicMock(name="cursor")
        cursor.__enter__().description = [["id"], ["name"], ["ccc_id"]]
        cursor.__enter__().fetchall = Mock(side_effect=self.fetchall_ran)
        cursor.__enter__().fetchall.return_value = self.oracle_student_dict
        cursor.__enter__().executemany = Mock(side_effect=self.executemany_update)
        cursor.__enter__().execute = Mock(side_effect=self.execute_ran)
        return cursor


if __name__ == "__main__":
    unittest.main()
