@echo off
cd /d "c:\MyIT\it_management_platform\backend"
.venv\Scripts\activate
python -m pytest apps/frontend/tests/ -v --tb=short > test_output.txt 2>&1
type test_output.txt

