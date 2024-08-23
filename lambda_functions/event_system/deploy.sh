#!/usr/bin/env bash
cd lambda_functions/event_system
cp ../unzip_requirements.py .
npm i
./node_modules/serverless/bin/serverless.js deploy