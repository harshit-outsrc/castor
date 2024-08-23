# Calbright Trigger Workflow

This lambda is invoked by the PSQL database whenever a trigger fires. It will proceed to validate information coming in and either push it off to the correct event system or process the steps required.

## How to Install for Deployment
Ensure you have npm installed.
Install the required packages:
 - `cd lambda_functions/calbright_trigger_workflow`
 - `npm install`

## How to Deploy
From project root run `./lambda_functions/calbright_trigger_workflow/deploy.sh`

## Errors or Issues
For Module Import Errors on AWS, even though we specify to not cache in the yaml, may need to `serverless requirements cleanCache` then process deployment again.

## Local Dev Testing
In order to test in local database, you need first have your database contain the required records on the tables used for each trigger workflow. Once the records are in place, supply the record id and the workflow trigger type data into the `handler.py` `main` where the `run` is called and supply argument `test` when running.
