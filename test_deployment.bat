@echo off
REM Test Deployment Script for Kuraz AI (Windows)
REM Usage: test_deployment.bat https://your-app-name.onrender.com

if "%1"=="" (
    echo Error: Please provide your Render URL
    echo Usage: test_deployment.bat https://your-app-name.onrender.com
    exit /b 1
)

set BASE_URL=%1
echo Testing Kuraz AI deployment at: %BASE_URL%
echo ================================================
echo.

echo 1. Testing root endpoint...
curl -s "%BASE_URL%/"
echo.
echo.

echo 2. Testing health check...
curl -s "%BASE_URL%/api/health"
echo.
echo.

echo 3. Seeding database...
curl -s -X POST "%BASE_URL%/api/seed"
echo.
echo.

echo 4. Getting room types...
curl -s "%BASE_URL%/api/room-types"
echo.
echo.

echo 5. Getting dashboard KPIs...
curl -s "%BASE_URL%/api/dashboard/kpis"
echo.
echo.

echo ================================================
echo Testing complete!
echo.
echo View full API docs at: %BASE_URL%/docs
echo.
