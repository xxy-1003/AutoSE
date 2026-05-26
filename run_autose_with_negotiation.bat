@echo off
echo Starting AutoSE Platform with Conversational Sales Engineer Negotiation Capabilities
echo ================================================================================
echo.
echo 1. First, let's verify the negotiation implementation...
python verify_negotiation.py
echo.
echo 2. Testing negotiation capabilities...
python test_negotiation.py
echo.
echo 3. Starting AutoSE Platform...
echo    Backend API: http://localhost:8000
echo    Frontend UI: http://localhost:8501
echo.
echo 4. Open two separate terminals and run:
echo    Terminal 1: python -m src.autose_platform.main
echo    Terminal 2: streamlit run chat_frontend.py
echo.
echo 5. Try these negotiation examples in the chat:
echo    - "This solution is wrong"
echo    - "Too expensive, budget=3000"
echo    - "Reduce cameras to 20"
echo    - "Simplify the solution"
echo    - "Not reasonable for my needs"
echo.
echo Press any key to exit...
pause > nul