# Calbright Trigger Workflow

This lambda is invoked by the PSQL database whenever a trigger fires. It will proceed to validate information coming in and either push it off to the correct event system or process the steps required.

## How to Install for Deployment
Ensure you have npm installed.
Install the required packages:
 - `cd lambda_functions/psql_trigger_handler`
 - `npm install`

## How to Deploy
From project root run `./lambda_functions/psql_trigger_handler/deploy.sh`

## Errors or Issues
For Module Import Errors on AWS, even though we specify to not cache in the yaml, may need to `serverless requirements cleanCache` then process deployment again.
