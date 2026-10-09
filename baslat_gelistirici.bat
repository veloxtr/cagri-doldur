@echo off
rem Exe derlemeden, kaynak koddan calistirmak icin (gelistirme amacli).
cd /d "%~dp0"
set PY=
py -3 --version >nul 2>nul && set PY=py -3
if not defined PY (
  python --version >nul 2>nul && set PY=python
)
if not defined PY (
  echo Python bulunamadi.
  pause
  exit /b
)
%PY% -m pip install -q -r requirements.txt
%PY% main.py
