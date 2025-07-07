@echo off
cd /d "%~dp0src"

:: Stap 1: Check of Python beschikbaar is
where python >nul 2>nul
if errorlevel 1 (
    echo Python is niet geïnstalleerd of staat niet in PATH.
    echo Installeer Python vanaf: https://www.python.org/downloads/
    pause
    exit /b
)

:: Stap 2: Check of virtuele omgeving bestaat
if not exist "vergelijker_env\Scripts\activate.bat" (
    echo Virtuele omgeving niet gevonden. Aanmaken...
    python -m venv vergelijker_env

    echo Dependencies installeren...
    call vergelijker_env\Scripts\activate.bat
    pip install --upgrade pip >nul
    pip install -r requirements.txt
) else (
    echo Virtuele omgeving gevonden.
)

:: Stap 3: Activeer en start
call vergelijker_env\Scripts\activate.bat
python main.py
pause
