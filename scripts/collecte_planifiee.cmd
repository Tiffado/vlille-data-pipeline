@echo off
rem Collecte lancée par le Planificateur de tâches Windows toutes les 30 minutes.
rem Solution provisoire, remplacée par Airflow en phase 2.
cd /d "%~dp0.."
set "PYTHONIOENCODING=utf-8"
"%USERPROFILE%\.local\bin\uv.exe" run --env-file .env vlille-collect >> logs\collecte.log 2>&1
