@echo off
REM ===================================================
REM Render Auto Deploy Script for ship-bot
REM ===================================================

REM Step 1: Add all changes
git add .

REM Step 2: Commit changes
set /p msg="Enter commit message: "
git commit -m "%msg%"

REM Step 3: Push to GitHub main branch
git push origin main

REM Step 4: Inform user to deploy on Render
echo.
echo ===================================================
echo Changes pushed to GitHub.
echo Now go to Render dashboard and click Manual Deploy.
echo Web Service: marin_ship
echo URL: https://marin-ship.onrender.com
echo ===================================================
pause
