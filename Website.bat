echo OFF
start cmd /C python "manage.py" runserver
timeout 5
start "" http://127.0.0.1:8000/manager/