@echo off
setlocal
cd /d "%~dp0"

echo Checking virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment...
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    echo Virtual environment not found. Using system python...
    set PYTHON_EXE=python
)

echo Starting Market Risk Monitoring Dashboard...
"%PYTHON_EXE%" -m streamlit run app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start the app.
    echo Please make sure dependencies are installed: pip install -r requirements.txt
    pause
)
endlocal
