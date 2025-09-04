@echo off
echo Building AI Script Generator executable...

:: Create build directory if it doesn't exist
if not exist "build" mkdir build

:: Install PyInstaller if not already installed
pip install pyinstaller

:: Build the executable with --onefile option
pyinstaller --onefile ^
    --distpath build ^
    --workpath build\temp ^
    --specpath build ^
    --name "AI_Script_Generator" ^
    --add-data "src;src" ^
    --hidden-import customtkinter ^
    --hidden-import tkinter ^
    --hidden-import requests ^
    --hidden-import python-dotenv ^
    --hidden-import chromadb ^
    --hidden-import markdown2 ^
    --hidden-import yt-dlp ^
    --noconsole ^
    src\main.py

echo.
echo Build complete! Executable created in build directory.
echo You can run: build\AI_Script_Generator.exe

pause