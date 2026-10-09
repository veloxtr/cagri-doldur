@echo off
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
echo Gerekli paketler kuruluyor...
%PY% -m pip install -q -r requirements.txt pyinstaller
if errorlevel 1 (
  echo Paket kurulumu basarisiz.
  pause
  exit /b
)
echo Exe derleniyor, 1-2 dakika surebilir...
%PY% build.py
if not exist "dist\BilnexAssist.exe" (
  echo Derleme basarisiz. Yukaridaki hatayi Claude'a gonder.
  pause
  exit /b
)
echo.
echo Hazir: dist\BilnexAssist.exe
echo Bu dosyayi istedigin yere (orn. Masaustu) kopyalayip kullanabilirsin.
explorer dist
pause
