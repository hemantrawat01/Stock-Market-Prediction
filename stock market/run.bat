@echo off
echo ========================================================
echo   Starting QuantPulse AI - Stock Market Prediction App
echo ========================================================
echo.
echo Opening server at http://localhost:8080 (http://127.0.0.1:8080)
echo Press CTRL+C to stop the server anytime.
echo.
py -3.13 app.py 8080
if %ERRORLEVEL% NEQ 0 (
    python app.py 8080
)
pause
