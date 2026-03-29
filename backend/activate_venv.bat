@echo off
REM Activate virtual environment for Alpha LPGas backend

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated!
    echo.
    echo You can now run:
    echo   python manage.py runserver
    echo   python manage.py makemigrations
    echo   python manage.py migrate
) else (
    echo Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
    echo Virtual environment created and activated!
)
