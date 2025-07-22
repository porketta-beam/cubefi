@echo off
echo Fixing datasets package unicode issue...
echo =============================================

echo Current datasets version:
pip show datasets | findstr Version

echo.
echo Downgrading datasets to fix unicode() error...
pip install "datasets>=2.21.0,<4.0.0"

echo.
echo New datasets version:
pip show datasets | findstr Version

echo.
echo Fix completed! Please restart the server.
pause