#!/usr/bin/env bash
cd lambda_functions/canvas_events
cp ../unzip_requirements.py .
npm i
./node_modules/serverless/bin/serverless.js deploy