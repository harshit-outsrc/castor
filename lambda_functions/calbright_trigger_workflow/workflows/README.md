# Calbright Trigger Workflows List

`process_certificates.py`:
Creates certificate in Anthology when an enrollment is completed in AWS.

`process_grades.py`:
Updates existing courses in Anthology with Final grades based on what is updated in AWS.
Conditions:
  - SP,  I or {blank} grades will just be skipped since they will not be the final grades.
  - D, W, EW, MW or NP grades will proceed to post the grade of the student and drop the student's course adding a reason.
  - P grade will post the final grade for a student and mark the course as completed.

`process_new_ccc_applications.py`:
Processes new CCCApplications coming from CCCApply Oracle Database and adds the application into AWS, applying to existing records for deduplication or creating new ones accordingly.
Deduplication Conditions:
  - Student has matching CCCID existing on Student record.
  - Student's Firstname, Lastname and Phone Number match under User record.
  - Student's Firstname, Lastname under User record and Date of Birth under Student record attached to User record.
  - Student's Personal Email matches on User record.

`process_new_enrollment.py`:
Creates a new enrollment in Anthology based on what exists in AWS. After enrollment is created, proceeds to create courses tied to the enrollment in Anthology. Once enrollment is created, apply the Anthology id to AWS. If error occurs during course creation and trigger goes on DLQ, reprocessing should account for existing Enrollment if applied to the Enrollment record in AWS.
