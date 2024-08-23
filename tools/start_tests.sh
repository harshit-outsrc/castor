#!/bin/bash
set -e

coverage erase

coverage run -a tests/start_scripts/calbright_trigger_workflow_tests.py
coverage run -a tests/start_scripts/canvas_events_tests.py
coverage run -a tests/start_scripts/ccc_apply_student_ingestion_tests.py
coverage run -a tests/start_scripts/event_system_tests.py
coverage run -a tests/start_scripts/pace_progress_tests.py
coverage run -a tests/start_scripts/psql_trigger_tests.py
coverage run -a tests/start_scripts/seed_data_updates.py
coverage run -a tests/start_scripts/symplicity_student_ingestion.py

coverage report
coverage xml