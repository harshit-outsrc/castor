#!/usr/bin/env bash

cd lambda_functions/psql_trigger_handler
cp ../unzip_requirements.py .
npm i
./node_modules/serverless/bin/serverless.js deploy