import dictdiffer

from propus import Logging
from propus.helpers.etl import batch_generator


class ErrorsOnBatchProcess(Exception):
    pass


class CsmService:
    def __init__(self, csm):
        self.csm = csm
        self.batch_size = 500

        self.all_possible_fields = [
            "id",
            "schoolStudentId",
            "email",
            "username",
            "firstName",
            "middleName",
            "lastName",
            "fullName",
            "preferredName",
            "permanentEmail",
            "phone",
            "mobile_phone_number",
            "enrollment_status",
            "address",
            "majors",
            "counselors",
            "calbright_programs_completed",
            "date_of_enrollment",
            "leave_start_date",
            "leave_end_date",
            "most_recent_certificate_comple",
            "email_opt_out",
            "sms_opt_out",
            "do_not_call",
            "current_end_term_date",
            "accountDisabled",
            "accountBlocked",
            "customFields",
            "applicantType",
        ]

        self.optional_fields = [
            "middleName",
            "preferredName",
            "calbright_programs_completed",
            "most_recent_certificate_comple",
            "leave_start_date",
            "last_term_enrolled",
            "leave_end_date",
            "current_end_term_date",
        ]

        self.career_specialists = {
            "967d170116baf1f15f36ac103caaedc1": "Jennifer Cunningham",
            "d1963c8579595d68acf1526694d908bf": "Mike Palmieri ",
        }

        self.logger = Logging.get_logger("salesforce_service.py")

    def normalize_csm_data(self, csm_data: dict):
        """Normalize CSM data by standardizing fields.

        This function takes raw CSM data and normalizes/standardizes various fields
        to prepare the data for downstream use.

        It extracts IDs from nested objects, standardizes address formatting, converts
        boolean fields, removes optional empty fields, and more.

        Args:
            csm_data (dict): Raw CSM data to normalize

        Returns:
            dict: Normalized CSM data
        """

        csm_data["majors"] = [m.get("id") for m in csm_data.get("majors")]
        csm_address = {"country": "US", "state": "US-CA"}
        if csm_data.get("address") and csm_data.get("address").get("label"):
            address = csm_data.get("address").get("label").split("\n")
            if len(address) >= 3:
                subaddr = address[-2].split(" ")
                if len(subaddr) >= 3:
                    csm_address = {
                        "street": "\n".join(address[: len(address) - 2]).replace("\r", ""),
                        "city": " ".join(subaddr[:-2]).replace(",", ""),
                        "state": "US-CA" if subaddr[-2] == "California" else subaddr[-2],
                        "zip": subaddr[-1],
                        "country": "US",
                    }
        csm_data["address"] = csm_address
        for field, value in csm_data.get("customFields", {}).items():
            csm_data[field] = value
        if "customFields" in csm_data:
            del csm_data["customFields"]

        for field in ["email_opt_out", "sms_opt_out", "do_not_call"]:
            csm_data[field] = True if csm_data.get(field) == "1" else False

        for field in self.optional_fields:
            if field in csm_data and not csm_data.get(field):
                del csm_data[field]
        csm_data["accountBlocked"] = csm_data.get("accountBlocked").get("id")
        if csm_data.get("enrollment_status"):
            csm_data["enrollment_status"] = csm_data.get("enrollment_status").get("id")
        csm_data["counselors"] = [c.get("id") for c in csm_data.get("counselors")]
        csm_data["applicantType"] = [a.get("id") for a in csm_data.get("applicantType")]
        if csm_data.get("calbright_programs_completed"):
            csm_data["calbright_programs_completed"] = sorted(
                [p.get("id") for p in csm_data.get("calbright_programs_completed")]
            )
        if csm_data.get("county_of_residence") == "":
            csm_data["county_of_residence"] = None

        fields_to_be_removed = [
            "assigned_success_counselor_tex",
            "assigned_success_counselor_ema",
            "assigned_success_counselor_mee",
            "county",
            "portfolio",
            "international_student",
            "first_generation_college_stude",
            "current_program",
        ]
        keys_to_del = [key for key in csm_data.keys() if key in fields_to_be_removed or "fg_generated" in key]
        for key in keys_to_del:
            del csm_data[key]
        return csm_data

    def fetch_csm_students(self):
        """Fetch student data from CSM in batches.

        This function paginates through CSM to retrieve all student records.
        It makes repeated calls to the CSM API to fetch students in batches,
        specified by the "page" and "perPage" parameters.

        The fetched student records are merged and normalized using the
        normalize_csm_data function before being returned.

        Returns:
            dict: A dictionary of all normalized student records indexed by CCC ID
        """
        page = 1
        more_students = True
        student_data = {}
        while more_students:
            response = self.csm.list_students(page=page)
            student_data |= {
                s.get("schoolStudentId"): self.normalize_csm_data(
                    {k: v for k, v in s.items() if k in self.all_possible_fields}
                )
                for s in response.get("models")
            }
            page += 1
            if (response.get("page") * response.get("perPage")) > response.get("total"):
                more_students = False
        self.logger.info(f"Fetched {len(student_data)} students from CSM")
        return student_data

    def create_new_students(self, student_data: list):
        """Create students in batches from a list of student data.

        This function takes a list of student data and creates the students
        in batches by calling the CSM batch create API.

        It iterates through the list in batches of size self.batch_size. For each
        batch, it calls the API and parses the results.

        Args:
            student_data (list): List of student data dictionaries
        """
        if not student_data:
            return

        for student in student_data:
            student["counselors"] = student.get("counselors", []) + list(self.career_specialists.keys())

        for i in range(0, len(student_data), self.batch_size):
            this_batch = student_data[i : i + self.batch_size]
            resp = self.csm.batch_create_students(this_batch)
            self.parse_batch_results(resp, this_batch, "Create")
        self.logger.info(f"Created {len(student_data)} students")

    def update_students(self, salesforce_students: dict, csm_students: dict):
        """Update student data from Salesforce in CSM in batches.

        This function takes dictionaries of student data from Salesforce
        and CSM. It iterates through the Salesforce data to check for
        differences with the CSM data.

        Any differences are added to a batch update list. Once the batch
        reaches 50 students, it makes a call to update those students
        in CSM.

        After processing all students, it updates any remaining batches
        and logs the total number of updates.

        Args:
            salesforce_students (dict): Dict of student salesforce data keyed by ccc_id
            csm_students (dict): Dict of student csm data keyed by ccc_id
        """

        batch_update_data = []
        for ccc_id, salesforce_data in salesforce_students.items():
            csm_data = csm_students.get(ccc_id)
            update_data = {"id": csm_data.get("id")} | salesforce_data

            del csm_data["id"]
            del salesforce_data["username"]
            del csm_data["username"]

            csm_data["counselors"] = list(set(csm_data.get("counselors")) - self.career_specialists.keys())

            differences = list(dictdiffer.diff(csm_data, salesforce_data))
            if differences:
                update_data["counselors"] += self.career_specialists.keys()
                batch_update_data.append(update_data)

        if batch_update_data:
            self.logger.info(f"Found {len(batch_update_data)} updates to make to CSM")
            completions = 0
            for batch in batch_generator(batch_update_data, self.batch_size):
                resp = self.csm.batch_update_students(batch)
                self.parse_batch_results(resp, batch_update_data, "Update")
                completions += 1
                self.logger.info(f"Completed updating {completions * self.batch_size} students")
        self.logger.info(f"Updated {len(batch_update_data)} students")

    @staticmethod
    def parse_batch_results(resp: dict, batch_data: list, batch_type: str):
        """Parse batch results from CSM.

        This function takes a response from CSM and a list of batch data.
        It checks for errors in the response and raises an exception if
        any errors are found.

        Args:
            resp (dict): Response from CSM
            batch_data (list): List of batch data
            batch_type (str): Type of batch, e.g. "Create", "Update", "Disable"
        Raises:
            ErrorsOnBatchProcess: If errors are found in the response
        """

        possible_errors = [i for i in range(len(resp.get("responses"))) if "errors" in resp.get("responses")[i]]
        if possible_errors:
            error_data = [{"record": batch_data[idx], "error": resp.get("responses")[idx]} for idx in possible_errors]
            raise ErrorsOnBatchProcess(f"Batch {batch_type} Failures. Errors: {error_data}")

    def update_merged_students(self, csm_students, salesforce_students):
        csm_email_dict = {}
        for ccc_id, s_data in csm_students.items():
            if not ccc_id:
                continue
            csm_email_dict[s_data.get("email")] = ccc_id

        sforce_student_map = {}
        for ccc_id, s_data in salesforce_students.items():
            sforce_student_map[s_data.get("email")] = ccc_id

        for common_email in set(csm_email_dict.keys()).intersection(set(sforce_student_map.keys())):
            if (
                csm_email_dict.get(common_email)
                and sforce_student_map.get(common_email)
                and csm_email_dict.get(common_email) != sforce_student_map.get(common_email)
            ):
                csm_ccc_id = csm_email_dict.get(common_email)
                sforce_ccc_id = sforce_student_map.get(common_email)
                self.logger.info(f"Updating merged student from {csm_ccc_id} to {sforce_ccc_id}")
                record = csm_students.get(csm_ccc_id)
                record["schoolStudentId"] = sforce_ccc_id
                csm_students[sforce_ccc_id] = record
                del csm_students[csm_ccc_id]
                self.csm.update_student(record.get("id"), record)
        return csm_students
