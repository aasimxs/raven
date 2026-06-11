@echo off
echo ==================================================
echo         Raven - Setup
echo ==================================================
echo.

echo [*] Setting up Python Backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo.
echo [*] Setting up React Frontend...
cd frontend
call npm install
call npm run build
cd ..

echo.
echo ==================================================
echo [SUCCESS] Setup Complete! 
echo.
echo To start using Raven, you can now run:
echo   raven.bat -help
echo.
echo Note: For the best experience, add this folder 
echo (%CD%) to your Windows PATH to use 'raven' anywhere.
echo ==================================================
pause
