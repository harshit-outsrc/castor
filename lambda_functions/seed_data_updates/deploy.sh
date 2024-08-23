#!/usr/bin/env bash
cd lambda_functions/seed_data_updates
cp ../unzip_requirements.py .
npm i
./node_modules/serverless/bin/serverless.js deploy