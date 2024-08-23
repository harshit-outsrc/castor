# Requirements

1. Python3 (modules located in requirements.txt)
2. Docker (Install, but Dockerfile is already setup)
3. AWS CLI (Install and Config)
4. Environment Variables (`.env`)

# Quickstart

1. Clone repo.
2. Install modules in requirements.txt via `pip3`
3. Log into AWS ECR `aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 523292522460.dkr.ecr.us-west-2.amazonaws.com`
4. Build Docker Image `docker build --ssh default={location of ssh key} -t strut_progress_activity_tracker .` or `docker build --build-arg default={location of ssh key} -t strut_progress_activity_tracker .` based on being in the same folder as the Dockerfile
5. Tag Docker Image `docker tag strut_progress_activity_tracker:latest 523292522460.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker`
6. Push Docker Image `docker push 523292522460.dkr.ecr.us-west-2.amazonaws.com/strut_progress_activity_tracker`
7. Go into AWS and launch Scheduled Task under the ECS castor-cluster using CRON Expression: `cron(0 3 * * ? *)`

# Notes

The application is meant to be modular. `student_integrations` folder contains the integration access functions and classes used in order to determine process students.

1. `strut.py` contains functions that will grant access to strut and grab student user information and enrollments for processing.

2. `salesforce.py` contains functions that will grant access to Salesforce API, which will allow the processing of bulk updates if student information has changed.

3. For Local Environment runs, there are adjustments that need to be made to the Event Loop Policy in `student_progress_script.py` marked by `#Set Async Loop policy to avoid RuntimeError` if you are running on Windows machine or leave as Default if you are running a Docker Image. When running locally, `logs/strut_progress_activity_tracker.log` will contain output information related to logger. There are two adjustments that can be made for testing, one in `salesforce.py` where the SALESFORCE_QUERY is located and one in `strut.py` where the users are being grabbed related to the recordIndex and paging if you don't want processing times to take long periods.

# Deployment Checks

## Verify modifications are using async/await

A lot of what we do interfaces with APIs. You don't want to hit rate-limits, and 
you don't want to have parts of your code finishing before API calls complete. 

The general layout of a successful job is as follows:

1. Some async helper functions
2. An anonymous async block where you sequentially call your helper functions.

## Ensure your `.env` file is setup correctly.

Ensure you also create the `.env` file and store it in the root of the project. 

This is not pushed to the repository and will exist in a secure location as it contains sensitive information for logging into our integrations.

## Send your code to the server

Merge your changes to the `master` branch and make sure to push your Docker Image to the ECR

## Schedule your trigger

Schedule your Task on the ECS Cluster called castor-cluster. This uses Fargate instead of EC2.
