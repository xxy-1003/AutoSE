@echo off
echo ========================================
echo AutoSE Platform Startup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -e . >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies (verbose mode)...
    pip install -e .
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo ⚠  .env file not found
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo Please edit .env file and add your DeepSeek API key
    echo Get API key from: https://platform.deepseek.com/api_keys
    echo.
)

echo.
echo ========================================
echo AutoSE Platform Ready to Start
echo ========================================
echo.
echo Choose an option:
echo 1. Start Backend API (FastAPI)
echo 2. Start Frontend (Streamlit)
echo 3. Start Both (separate terminals)
echo 4. Run Demo
echo 5. Run Tests
echo 6. Exit
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo Starting FastAPI backend...
    echo API will be available at: http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    echo.
    python -m uvicorn src.autose_platform.main:app --reload
) else if "%choice%"=="2" (
    echo.
    echo Starting Streamlit frontend...
    echo Frontend will be available at: http://localhost:8501
    echo.
    streamlit run streamlit_app.py
) else if "%choice%"=="3" (
    echo.
    echo Please open two separate terminals and run:
    echo.
    echo Terminal 1: python -m uvicorn src.autose_platform.main:app --reload
    echo Terminal 2: streamlit run streamlit_app.py
    echo.
    pause
) else if "%choice%"=="4" (
    echo.
    echo Running demo...
    python run_demo.py
    pause
) else if "%choice%"=="5" (
    echo.
    echo Running tests...
    python test_implementation.py
    pause
) else if "%choice%"=="6" (
    echo.
    echo Exiting...
) else (
    echo.
    echo Invalid choice
    pause
)

REM Deactivate virtual environment
deactivate >nul 2>&1