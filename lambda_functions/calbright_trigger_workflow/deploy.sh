#!/usr/bin/env bash

cd lambda_functions/calbright_trigger_workflow
cp ../unzip_requirements.py .
npm i
./node_modules/serverless/bin/serverless.js deploy