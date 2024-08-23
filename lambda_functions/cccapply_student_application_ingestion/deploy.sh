#!/usr/bin/env bash
cd lambda_functions/cccapply_student_application_ingestion
cp ../unzip_requirements.py .
npm i
./node_modules/serverless/bin/serverless.js deploy