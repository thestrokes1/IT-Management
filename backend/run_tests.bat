@echo off
cd /d "c:\MyIT\it_management_platform\backend"
.venv\Scripts\activate
python -m pytest apps/frontend/tests/test_permissions/ -v --tb=short
pause

