@echo off
REM Change the directory to where your Python script is located
set "current_dir=%CD%"
cd %current_dir%

REM remember to have a venv created! run python -m venv venv to do this
call venv\Scripts\activate
pip install -r requirements.txt

REM Run the Python script
python email_questions.py > output.log 2>&1

deactivate
