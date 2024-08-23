# CCCApply Student Application Ingestion

This lambda runs on a given schedule and checks if there are new student applicants waiting to be ingested from our CollegeAdapter OracleDB. If there is, the script will query the records waiting to be ingested from the STAGING_STUDENT_APPLICATIONS table. After the APP_IDs are received a select is performed on the OracleDB to grab all the information needed from the CCCApplication. These student records are then applied to the ccc_application model and inserted into Calbright's Postgres Database. Upon final ingestion, records are marked ingested on the STAGING_STUDENT_APPLICATIONS table in OracleDB.

## How to Install for Deployment
Ensure you have npm installed.
Install the required packages:
 - `cd lambda_functions/cccapply_student_application_ingestion`
 - `npm install`

## How to Deploy
From project root run `./lambda_functions/cccapply_student_application_ingestion/deploy.sh`
