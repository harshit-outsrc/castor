import csv
from decimal import Decimal, getcontext
import logging
import os

ASSESSMENT_FILENAME = "dashboardReport.csv"
OUTPUT_FILENAME = "comptency_tracker.csv"
PROJECT_FILENAME = "Project_Final_Exam_Rubric_Summary_by_Competency_Report.csv"
RUBRIC_SCALE = 4
getcontext().prec = 2

# Layout of output file, loaded with initial headers values
rows_out = [
    (
        "competency_id",
        "competency_title",
        "assessment_id",
        "num_students_attempted",
        "passed_first",
        "passed_subsequently",
        "final_avg_score",
        "num_tests_taken",
    )
]

# tracked_values previously supplied values to carryover from previous row to the next
tracked_values = {
    "Assessment Id": None,
    "Competency Id": None,
    "Competency Title": None,
}


def track_values(row, column_name, is_string=False):
    row_value = row.get(column_name)
    if row_value:
        tracked_values[column_name] = row_value if is_string else int(row_value)
    elif not tracked_values.get(column_name):
        tracked_values[column_name] = None

    return tracked_values[column_name]


def parse_projects(input_file):
    # These columns do not apply here
    num_attempts = passed_first = passed_subsequently = None

    assessment_dict = {}

    with open(input_file, encoding="utf8") as csvfile:
        # Skip title row
        next(csvfile)
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                competency_id = track_values(row, "Competency Id")
                competency_title = track_values(row, "Competency Title", is_string=True)
                assessment_id = track_values(row, "Assessment Id")
                rubric_count = 1
                rubric_grade = Decimal(row.get("Average Rubric Grade"))
                num_tests_taken = int(row.get("# of Graded Tests").replace(",", ""))
            except Exception as e:
                # Shouldn't get here, but set values on error if so
                competency_id = "Error processing competency_tracker file"
                competency_title = assessment_id = rubric_count = rubric_grade = num_tests_taken = None
                logging.error(f"competency_tracker: unable to parse project row: {e}")

            if assessment_id not in assessment_dict:
                # New assessment data
                assessment_dict[assessment_id] = {
                    "rubric_count": rubric_count,
                    "rubric_sum": rubric_grade,
                    "num_tests_taken": num_tests_taken,
                    "competency_id": competency_id,
                    "competency_title": competency_title,
                }
            else:
                # Update existing assessment data
                assessment_dict[assessment_id]["rubric_count"] += 1
                assessment_dict[assessment_id]["rubric_sum"] += rubric_grade

    for assessment_id, values_dict in assessment_dict.items():
        competency_id = values_dict.get("competency_id")
        competency_title = values_dict.get("competency_title")
        rubric_count = values_dict.get("rubric_count")
        rubric_sum = values_dict.get("rubric_sum")
        num_tests_taken = values_dict.get("num_tests_taken")
        if rubric_count:
            final_avg_score = f"{(Decimal(100.00) * rubric_sum / (RUBRIC_SCALE * rubric_count)):2f}"
        else:
            final_avg_score = None

        rows_out.append(
            (
                competency_id,
                competency_title,
                assessment_id,
                num_attempts,
                passed_first,
                passed_subsequently,
                final_avg_score,
                num_tests_taken,
            )
        )


def parse_assessments(input_file):
    # These columns do not apply here
    competency_id = final_avg_score = num_tests_taken = None

    with open(input_file, encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                assessment_id = row.get("Assessment Id")
                competency_title = row.get("Competency Title")
                num_attempts = f'{int(row.get("# of Students Attempted").replace(",",""))}'
                passed_first = row.get("% Passed - 1st Attempt")
                passed_subsequently = row.get("% Passed - 2nd Attempt")
            except Exception as e:
                competency_id = "Error processing competency_tracker file"
                competency_title = assessment_id = num_attempts = passed_first = passed_subsequently = None
                logging.error(f"competency_tracker unable to parse assessment row: {e}")

            rows_out.append(
                (
                    competency_id,
                    competency_title,
                    assessment_id,
                    num_attempts,
                    passed_first,
                    passed_subsequently,
                    final_avg_score,
                    num_tests_taken,
                )
            )


def competency_tracker():
    """
    Calculates course and program assessment / competency, and adjusts
    rubric-based scores (4pts/rubric) to a 0.00-100.00 score.

    The current / MVP output is a CSV that gets dumped into a formatted
    spreadsheet where the CSV will populate cells with vlookups.

    The basic algorithm is to take two report outputs from Strut and then:
        # Step 1 -> Parse project file to calculate normalized scores
        # Step 2 -> Parse assessment file for course pass rates
        # Step 3 -> Export to csv for use in the competency tracker
    """
    logging.info("competency_tracker: running...")
    base_directory = os.path.dirname(os.path.abspath(__file__))

    try:
        # Data source for the Project File:
        # https://certify.strutlearning.com/jasperserver-pro/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2Fpublic%2FFWK_Reports%2FReports%2FAdmin&reportUnit=%2Fpublic%2FFWK_Reports%2FReports%2FAdmin%2FProject_Final_Exam_Rubric_Summary_by_Competency_Report&standAlone=true  # NOQA: E501
        # Set `Submitted Dtm is on or after` value to desired range,
        # e.g., YEAR-10 to get all test scores
        project_file = f"{base_directory}/seed_data/{PROJECT_FILENAME}"
        parse_projects(project_file)
        logging.info(f"competency_tracker: parsed project file ({project_file})")
    except Exception as e:
        logging.error(f"competency_tracker: parsing project file ({e})")

    try:
        # Data source for the Assessment File
        # https://certify.strutlearning.com/jasperserver-pro/dashboard/viewer.html#%2Fpublic%2FFWK_Reports%2FDashboard%2FAssessment_Analysis_Dashboard
        # Filter or select all `Competency Titles`,
        # all `Assessment Types` and `Assessment Kinds`,
        # and `# of Students Attempted is greater than or equal to` 1
        assessment_file = f"{base_directory}/seed_data/{ASSESSMENT_FILENAME}"
        parse_assessments(assessment_file)
        logging.info(f"competency_tracker: parsed assessment file ({assessment_file})")
    except Exception as e:
        logging.error(f"competency_tracker: parsing assessment file ({e})")

    try:
        output_file = f"{base_directory}/reports/{OUTPUT_FILENAME}"
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows_out)
        logging.info(f"competency_tracker: generated output file ({output_file})")
    except Exception as e:
        logging.error(f"competency_tracker: generating output file ({e})")

    logging.info("competency_tracker: finished running.")


if __name__ == "__main__":
    competency_tracker()
