Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AutoSE Platform Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -e . 2>&1 | Out-Null
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "Installing dependencies (verbose mode)..." -ForegroundColor Yellow
    pip install -e .
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚠  .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host ""
    Write-Host "Please edit .env file and add your DeepSeek API key" -ForegroundColor Yellow
    Write-Host "Get API key from: https://platform.deepseek.com/api_keys" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AutoSE Platform Ready to Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Choose an option:" -ForegroundColor White
Write-Host "1. Start Backend API (FastAPI)" -ForegroundColor Gray
Write-Host "2. Start Frontend (Streamlit)" -ForegroundColor Gray
Write-Host "3. Start Both (separate terminals)" -ForegroundColor Gray
Write-Host "4. Run Demo" -ForegroundColor Gray
Write-Host "5. Run Tests" -ForegroundColor Gray
Write-Host "6. Exit" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Enter choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting FastAPI backend..." -ForegroundColor Green
        Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host ""
        python -m uvicorn src.autose_platform.main:app --reload
    }
    "2" {
        Write-Host ""
        Write-Host "Starting Streamlit frontend..." -ForegroundColor Green
        Write-Host "Frontend will be available at: http://localhost:8501" -ForegroundColor Cyan
        Write-Host ""
        streamlit run streamlit_app.py
    }
    "3" {
        Write-Host ""
        Write-Host "Please open two separate terminals and run:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Terminal 1: python -m uvicorn src.autose_platform.main:app --reload" -ForegroundColor Gray
        Write-Host "Terminal 2: streamlit run streamlit_app.py" -ForegroundColor Gray
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    "4" {
        Write-Host ""
        Write-Host "Running demo..." -ForegroundColor Green
        python run_demo.py
        Read-Host "Press Enter to continue"
    }
    "5" {
        Write-Host ""
        Write-Host "Running tests..." -ForegroundColor Green
        python test_implementation.py
        Read-Host "Press Enter to continue"
    }
    "6" {
        Write-Host ""
        Write-Host "Exiting..." -ForegroundColor Gray
    }
    default {
        Write-Host ""
        Write-Host "Invalid choice" -ForegroundColor Red
        Read-Host "Press Enter to continue"
    }
}

# Deactivate virtual environment
deactivate 2>&1 | Out-Null