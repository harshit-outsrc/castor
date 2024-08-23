import pandas as pd

# If pandas / read_excel gets dropped then the openpyxl dependency may no longer be needed in the project's setup.py
from datetime import datetime, timedelta
import os

ENROLL_CSEP_DELTA = 14
TERM_DELTA = 6
WITHDRAW_DELTA = 30

COMPLETED = "Completed"
DROPPED = "Dropped"
IN_PROGRESS = "In Progress"
WITHDRAWN = "Withdrawn"
CERTIFIED = "Certified"

NO_ERROR_STATUS = "No Error"
ERROR_STATUS = "Error"

LSH_COMPLETED = 12
LSH_IN_PROGRESS = 11
LSH_DROPPED = 0

GRADE_NP = "NP"
GRADE_P = "P"
GRADE_SP = "SP"
GRADE_W = "W"

YES = "Yes"
NO = "No"
NA = "N/A"

# TODO: The begin date will need to be set dynamically when run as the current term week beginning or as a parameter
BEGIN_DATE = "2022-01-03"


def student_progress_by_term():
    """
    Determines student progress by term for a given set of students during a calendar year (two terms).
    The current / MVP output is a spreadsheet that can then be used for subsequent analyses, e.g., pivot tables.

    The basic algorithm for processing students is to take the student and their enrollment date, then:
        # Step 1 -> Get Program Name from CSEP data file
        # Step 2 -> Fill in estimated term information
        # Step 3 -> Determine whether the student became actively enrolled in this program during their first term.
        # Step 4 -> Assign enrollment status and status date for the first term (e.g., if withdrawn or completed)
        # Step 5 -> Carry over to the second term as appropriate and determine the status in that term
    """
    base_directory = os.path.dirname(os.path.abspath(__file__))

    # TODO: These data files need to be replaced by dynamically generated queries
    # initially from SalesForce, and then ultimately from Postgres.
    # Most files are filtered subset from LSHqueryallstudents.xlsx / SalesForce query of learner status history.
    # SalesForce SoQL queries related to each spreadsheet as provided in comments at the bottom of this file,
    # although they should be refactored and/or actually joined, whereas the current implementation
    # tends to perform loose matching as opposed to actual relationship-based joins.

    # https://docs.google.com/spreadsheets/d/1RE6TS-I0IUTxj8vcaoOwK1hYDwk7rDuo/view
    df_main_file = pd.read_excel(f"{base_directory}/seed_data/Masterlist.xlsx")
    # https://docs.google.com/spreadsheets/d/1rzqlTe8XzEYh0E8lgcGzTQMVuUEabCHA/view
    df_csep_file = pd.read_excel(f"{base_directory}/seed_data/CSEP.xlsx")
    # https://docs.google.com/spreadsheets/d/1anNUgWfXhUQbPB2JFvZx0v5i7fmcnDa0/view
    df_term_file = pd.read_excel(f"{base_directory}/seed_data/Term.xlsx")
    # https://docs.google.com/spreadsheets/d/1anNUgWfXhUQbPB2JFvZx0v5i7fmcnDa0/view
    df_lsh_file = pd.read_excel(
        f"{base_directory}/seed_data/LSHqueryallstudents.xlsx",
        "LSH query - all students with d",
    )
    # https://docs.google.com/spreadsheets/d/15FmcZwJq-uXY8FTLFMnPMa8vYZlPq2so/view
    df_eot_file = pd.read_excel(f"{base_directory}/seed_data/EOTgradedata(all students).xlsx", "02-01-22 query")
    # https://docs.google.com/spreadsheets/d/1LseX5GAZxR9vwGMXUKqbEIMIe5P7l6rU/view
    df_roster_file = pd.read_excel(f"{base_directory}/seed_data/CalbrightOfficialGradeRoster.xlsx", "Full Roster")

    # TODO: Currently the results are output to a spreadsheet, although the results ought
    # to be stored in the database as objects or as a view instead of being generated ephemerally.
    df_deac_output = pd.DataFrame(
        columns=[
            "CCCID",
            "Name",
            "Program",
            "Date_of_enrollment",
            "Actively_enrolled",
            "Term1_name",
            "Term1_start_date",
            "Term1_end_date",
            "Term1_enrollment_status",
            "Term1_enrollment_status_date",
            "Term2_name",
            "Term2_start_date",
            "Term2_end_date",
            "Term2_enrollment_status",
            "Term2_enrollment_status_date",
            "Error_Term1_Date",
            "Error_InProgress_Status",
            "Error_Dropped_Status",
            "Error_Withdrawn_Status",
        ]
    )
    df_lsh_output = pd.DataFrame(columns=["CCCID", "LSH"])

    # Loop through each student
    for i, row in df_main_file.iterrows():
        # Set variables from the main file
        ccc_id = row["CCCID"]
        student_name = row["Name"]
        enroll_date = row["Date_of_enrollment"]
        # Initialize variables to be determined
        is_actively_enrolled = ""
        enroll_status = ""
        enroll_status_2 = ""
        withdrawn_status = ""
        withdrawn_error = ""
        progress_error = ""

        # Set dataframes that will be used throughout
        student_filter = f"CCCID == '{ccc_id}'"
        df_csep_student = df_csep_file.query(student_filter)
        df_eot_student = df_eot_file.query(student_filter)
        df_lsh_student = df_lsh_file.query(student_filter)
        df_roster_student = df_roster_file.query(student_filter)

        # Step 1 -> Use the CSEP data file to fill in the program name, matching by CCCID and date
        # TODO: Can a student only be enrolled in one CSEP program at a time?
        # Or why are there some students with two records in the Master.xlsx sheet?
        csep_set = False
        csep_program = ""
        for i, csep_row in df_csep_student.iterrows():
            csep_date = csep_row["CSEPDate"]
            # In case there is more than one CSEP date / program, match with the first one that is within 14 days
            if abs((enroll_date - csep_date).days) <= ENROLL_CSEP_DELTA:
                if csep_set:
                    print(f"{ccc_id} ({student_name}) originally matched CSEP program: {csep_program}")
                csep_program = csep_row["Program"]
                if csep_set:
                    print(f"{ccc_id} ({student_name}) now matched CSEP program by date: {csep_program}")
                break
            elif csep_set:
                print(f"{ccc_id} ({student_name}) originally matched CSEP program: {csep_program}")
                csep_program = csep_row["Program"]
                print(f"{ccc_id} ({student_name}) now matched CSEP program by default: {csep_program}")
            csep_set = True

        # Step 2 -> Fill in estimated term information (term name, start date, end date) for the student’s first term
        # TODO: Just get the row (rows?) where the term_delta <= TERM_DELTA and term_date_start >= enroll_date
        for i, term_row in df_term_file.iterrows():
            term_name = term_row["Name"]
            term_date_start = term_row["hed__Start_Date__c"]
            term_date_end = term_row["hed__End_Date__c"]
            term_delta = abs((enroll_date - term_date_start).days)

            term_error = NO_ERROR_STATUS
            if term_delta <= TERM_DELTA and term_date_start >= enroll_date:
                # TODO: Can there be more than one row here? If so, why?
                # Get the row not a for loop
                for i, eot_row in df_eot_student.iterrows():
                    term_error = NO_ERROR_STATUS if term_date_start == eot_row["hed__Start_Date__c"] else ERROR_STATUS
                    term_date_start = eot_row["hed__Start_Date__c"]
                    term_date_end = eot_row["hed__End_Date__c"]
                    term_name = eot_row["Term__r.Name"]
                    break

                # Step 3 -> Did student became actively enrolled in this program during their first term.
                df_lsh_11 = df_lsh_student.query(f"LSN == {LSH_IN_PROGRESS}")
                lsh_11_date = pd.to_datetime(
                    df_lsh_11["cfg_Current_Learner_Status_Date__c"],
                    format="%Y-%m-%dT%H:%M:%S.000+0000",
                )
                mask = (lsh_11_date >= enroll_date) & (lsh_11_date <= term_date_end)
                df_lsh_11_date_range = df_lsh_11.loc[mask]
                # TODO: Can there be more than one row here?
                # and if so, is it appropriate to take the first or last?
                for i, lsh_11_date_row in df_lsh_11_date_range.iterrows():
                    activity_date = datetime.strptime(
                        lsh_11_date_row["cfg_Current_Learner_Status_Date__c"],
                        "%Y-%m-%dT%H:%M:%S.000+0000",
                    )
                    is_actively_enrolled = YES if enroll_date <= activity_date <= term_date_end else NO
                    break

                # Step 4 -> Assign enrollment status and status date for the first term
                is_enrolled = False
                df_lsh_12_0 = df_lsh_student.query(f"LSN in ({LSH_COMPLETED},{LSH_DROPPED})")
                for i, lsh_student_row in df_lsh_12_0.iterrows():
                    lsh_status_date = datetime.strptime(
                        lsh_student_row["cfg_Current_Learner_Status_Date__c"],
                        "%Y-%m-%dT%H:%M:%S.000+0000",
                    )
                    lsh_status = lsh_student_row["LSN"]

                    if lsh_status == LSH_COMPLETED:
                        if term_date_start <= lsh_status_date <= term_date_end:
                            is_enrolled = True
                            enroll_status = COMPLETED

                    else:
                        df_lsh_output = df_lsh_output._append({"CCCID": ccc_id, "LSH": lsh_status}, ignore_index=True)
                        is_enrolled = True
                        enroll_delta = abs((enroll_date - lsh_status_date).days)
                        if enroll_delta <= WITHDRAW_DELTA:
                            enroll_status = DROPPED
                            dropped_error = (
                                NO_ERROR_STATUS if df_eot_student.empty and df_roster_student.empty else ERROR_STATUS
                            )

                            df_deac_output = df_deac_output._append(
                                {
                                    "CCCID": ccc_id,
                                    "Name": student_name,
                                    "Program": csep_program,
                                    "Date_of_enrollment": enroll_date,
                                    "Actively_enrolled": is_actively_enrolled,
                                    "Term1_name": term_name,
                                    "Term1_start_date": term_date_start,
                                    "Term1_end_date": term_date_end,
                                    "Term1_enrollment_status": enroll_status,
                                    "Term1_enrollment_status_date": lsh_status_date,
                                    "Term2_name": "",
                                    "Term2_start_date": "",
                                    "Term2_end_date": "",
                                    "Term2_enrollment_status": "",
                                    "Term2_enrollment_status_date": "",
                                    "Error_Term1_Date": term_error,
                                    "Error_InProgress_Status": "",
                                    "Error_Dropped_Status": dropped_error,
                                    "Error_Withdrawn_Status": "",
                                },
                                ignore_index=True,
                            )

                        else:
                            enroll_status = WITHDRAWN
                            df_eot_withdrawn = df_eot_student.query(
                                f'hed__Start_Date__c=="{term_date_start}" and hed__End_Date__c=="{term_date_end}" and Grade__c=="{GRADE_SP}"'  # NOQA: E501
                            )

                            if df_eot_withdrawn.empty:
                                df_deac_output = df_deac_output._append(
                                    {
                                        "CCCID": ccc_id,
                                        "Name": student_name,
                                        "Program": csep_program,
                                        "Date_of_enrollment": enroll_date,
                                        "Actively_enrolled": is_actively_enrolled,
                                        "Term1_name": term_name,
                                        "Term1_start_date": term_date_start,
                                        "Term1_end_date": term_date_end,
                                        "Term1_enrollment_status": enroll_status,
                                        "Term1_enrollment_status_date": lsh_status_date,
                                        "Term2_name": "",
                                        "Term2_start_date": "",
                                        "Term2_end_date": "",
                                        "Term2_enrollment_status": "",
                                        "Term2_enrollment_status_date": "",
                                        "Error_Term1_Date": term_error,
                                        "Error_InProgress_Status": "",
                                        "Error_Dropped_Status": "",
                                        "Error_Withdrawn_Status": "",
                                    },
                                    ignore_index=True,
                                )
                            else:
                                for i, eot_withdrawn_row in df_eot_withdrawn.iterrows():
                                    if eot_withdrawn_row["Grade__c"] == GRADE_SP:
                                        enroll_status = IN_PROGRESS
                                        term_withdrawn = df_term_file.query(
                                            f'hed__Start_Date__c == "{term_date_end + timedelta(days=1)}"'
                                        )

                                        for (
                                            i,
                                            term_withdrawn_row,
                                        ) in term_withdrawn.iterrows():
                                            term_withdrawn_name = term_withdrawn_row["Name"]
                                            term_withdrawn_date_start = term_withdrawn_row["hed__Start_Date__c"]
                                            term_withdrawn_date_end = term_withdrawn_row["hed__End_Date__c"]

                                            # Step 7 -> Assign enrollment status and status date for the second term
                                            is_withdrawn = False
                                            for (
                                                i,
                                                lsh_12_0_row,
                                            ) in df_lsh_12_0.iterrows():
                                                withdrawn_enrollment_date = datetime.strptime(
                                                    lsh_student_row["cfg_Current_Learner_Status_Date__c"],
                                                    "%Y-%m-%dT%H:%M:%S.000+0000",
                                                )
                                                withdrawn_status_2 = lsh_12_0_row["LSN"]
                                                if withdrawn_status_2 == LSH_COMPLETED:
                                                    if (
                                                        term_withdrawn_date_start
                                                        <= withdrawn_enrollment_date
                                                        <= term_withdrawn_date_end
                                                    ):
                                                        is_withdrawn = True
                                                        withdrawn_status = WITHDRAWN

                                                elif withdrawn_status_2 == LSH_DROPPED:
                                                    is_withdrawn = True
                                                    withdrawn_status = WITHDRAWN

                                            if not is_withdrawn:
                                                withdrawn_status = WITHDRAWN
                                                # Step 5 -> Use the EOT grade data file to confirm
                                                df_eot_date_2 = df_eot_student.query(
                                                    f'hed__Start_Date__c=="{term_date_start}" and hed__End_Date__c=="{term_date_end}"'  # NOQA: E501
                                                )
                                                # TODO: Can there be more than one row here?
                                                for (
                                                    i,
                                                    eot_grade_row,
                                                ) in df_eot_date_2.iterrows():
                                                    if eot_grade_row["Grade__c"] == GRADE_NP:
                                                        withdrawn_error = NO_ERROR_STATUS
                                                    else:
                                                        withdrawn_error = ERROR_STATUS
                                                    break

                                        # TODO: Dynamically set when being run, so that new students in current term
                                        # do not have a status / date?
                                        if str(term_withdrawn_date_end) > BEGIN_DATE:
                                            withdrawn_status = NA
                                            withdrawn_enrollment_date = NA

                                        df_deac_output = df_deac_output._append(
                                            {
                                                "CCCID": ccc_id,
                                                "Name": student_name,
                                                "Program": csep_program,
                                                "Date_of_enrollment": enroll_date,
                                                "Actively_enrolled": is_actively_enrolled,
                                                "Term1_name": term_name,
                                                "Term1_start_date": term_date_start,
                                                "Term1_end_date": term_date_end,
                                                "Term1_enrollment_status": enroll_status,
                                                "Term1_enrollment_status_date": term_date_end,
                                                "Term2_name": term_withdrawn_name,
                                                "Term2_start_date": term_withdrawn_date_start,
                                                "Term2_end_date": term_withdrawn_date_end,
                                                "Term2_enrollment_status": withdrawn_status,
                                                "Term2_enrollment_status_date": withdrawn_enrollment_date,
                                                "Error_Term1_Date": term_error,
                                                "Error_InProgress_Status": withdrawn_error,
                                                "Error_Dropped_Status": "",
                                                "Error_Withdrawn_Status": "",
                                            },
                                            ignore_index=True,
                                        )

                                        break

                if not is_enrolled:
                    enroll_status = IN_PROGRESS
                    lsh_status_date = lsh_status_date
                    # Step 5 -> If the student was “in progress” during their first term,
                    # assign estimated term information (term name, start date, end date),
                    # enrollment status, and status date for the second term.
                    # Estimate for Second term, First Term End Date + 1 will be the start date for Second Term.
                    # Match with EOT Term1 Name, Start Date, End Date with Term Data.
                    # TODO: Get the row instead of for loop
                    df_term_2 = df_term_file.query(f'hed__Start_Date__c == "{term_date_end + timedelta(days=1)}"')
                    for i, term_row_2 in df_term_2.iterrows():
                        term_name_2 = term_row_2["Name"]
                        term_date_start_2 = term_row_2["hed__Start_Date__c"]
                        term_date_end_2 = term_row_2["hed__End_Date__c"]
                        break

                    # Step 6 -> Assign enrollment status and status date for the second term
                    is_enrolled_2 = False
                    # df_lsh_12_0 = df_lsh_file.query('CCCID == @ccc_id and LSN in (12,0) ') # Already declared above
                    for i, lsh_row_2 in df_lsh_12_0.iterrows():
                        enroll_date_2 = datetime.strptime(
                            lsh_row_2["cfg_Current_Learner_Status_Date__c"],
                            "%Y-%m-%dT%H:%M:%S.000+0000",
                        )
                        lsh_status_2 = lsh_row_2["LSN"]
                        enroll_date_2_loop = ""
                        if lsh_status_2 == LSH_COMPLETED:
                            if term_date_start_2 <= enroll_date_2 <= term_date_end_2:
                                is_enrolled_2 = True
                                enroll_status_2 = COMPLETED
                                enroll_date_2_loop = enroll_date_2
                            else:
                                enroll_date_2 = enroll_date_2_loop
                        elif lsh_status_2 == LSH_DROPPED:
                            enroll_delta_2 = abs((enroll_date - enroll_date_2).days)
                            is_enrolled_2 = True
                            enroll_status_2 = DROPPED if enroll_delta_2 <= WITHDRAW_DELTA else WITHDRAWN
                    if not is_enrolled_2:
                        enroll_status_2 = IN_PROGRESS
                        enroll_date_2 = term_date_end_2
                        # Step 5 -> Use the EOT grade data file to confirm
                        # TODO: Get the row, not a for loop
                        df_eot_student_2 = df_eot_student.query(
                            f'hed__Start_Date__c=="{term_date_start}" and hed__End_Date__c=="{term_date_end}"'
                        )
                        for i, eot_2_row in df_eot_student_2.iterrows():
                            progress_error = ERROR_STATUS if eot_2_row["Grade__c"] == GRADE_NP else NO_ERROR_STATUS
                            break

                    # TODO: Compare actual dates, not strings
                    if str(term_date_end_2) > BEGIN_DATE:
                        enroll_status_2 = NA
                        enroll_date_2 = NA
                    df_deac_output = df_deac_output._append(
                        {
                            "CCCID": ccc_id,
                            "Name": student_name,
                            "Program": csep_program,
                            "Date_of_enrollment": enroll_date,
                            "Actively_enrolled": is_actively_enrolled,
                            "Term1_name": term_name,
                            "Term1_start_date": term_date_start,
                            "Term1_end_date": term_date_end,
                            "Term1_enrollment_status": enroll_status,
                            "Term1_enrollment_status_date": term_date_end,
                            "Term2_name": term_name_2,
                            "Term2_start_date": term_date_start_2,
                            "Term2_end_date": term_date_end_2,
                            "Term2_enrollment_status": enroll_status_2,
                            "Term2_enrollment_status_date": enroll_date_2,
                            "Error_Term1_Date": term_error,
                            "Error_InProgress_Status": progress_error,
                            "Error_Dropped_Status": "",
                            "Error_Withdrawn_Status": "",
                        },
                        ignore_index=True,
                    )
    # Writing to a new Excel Sheet
    # df_deac_output.to_excel(f"{base_directory}/reports/programlevelenrollmentsnew5.xlsx",sheet_name='DEAC Reports')
    # df_lsh_output.to_excel(f"{base_directory}/reports/LSHZero.xlsx",sheet_name='DEAC Reports')

    # Writing to CSV for testing purposes for easier diff comparison between iterations of the code
    df_deac_output.to_csv(f"{base_directory}/reports/programlevelenrollmentsnew5.csv")
    df_lsh_output.to_csv(f"{base_directory}/reports/LSHZero.csv")


if __name__ == "__main__":
    student_progress_by_term()

# SalesForce SoQL used to generate source data spreadsheets originally

# EOTgradedata
# select term__r.Name,
# term__r.hed__Start_Date__c,
# term__r.Last_day_to_drop_without_a_W__c,
# term__r.Last_day_to_withdraw__c,
# term__r.hed__End_Date__c,
# Date_Grade_Certified__c,
# Student__r.cfg_CCC_ID__c,
# Student__r.Email,
# Course__c, Grade__c, Status__c from C_End_of_Term_Grade__c
# Where (NOT Student__r.Email like '%@calbright.org')
# order by Student__r.cfg_CCC_ID__c,term__r.hed__Start_Date__c

# LSHqueryallstudents
# select cfg_Contact__r.cfg_CCC_ID__c ,
# cfg_Contact__r.Name,
# cfg_Contact__r.email,
# cfg_Current_Learner_Status__c,
# Current_Learner_Status_Number__c,
# cfg_Current_Learner_Status_Date__c
# from Learner_Status_History__c
# where (NOT cfg_Contact__r.Email like '%@calbright.org')
# and (Current_Learner_Status_Number__c = 0 OR Current_Learner_Status_Number__c >6)
# order by
# cfg_Contact__r.cfg_CCC_ID__c, cfg_Current_Learner_Status_Date__c

# Term
# select Name, hed__Start_Date__c, Last_day_to_drop_without_a_W__c,
# Last_day_to_withdraw__c, hed__End_Date__c
# From hed__Term__c
