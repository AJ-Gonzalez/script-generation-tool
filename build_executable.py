#!/usr/bin/env python3
"""
Build script for creating an executable of the AI Script Generator
"""

import os
import subprocess
import sys
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """Build the executable using PyInstaller"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    main_file = src_path / "main.py"
    build_dir = project_root / "build"
    
    # Create build directory
    build_dir.mkdir(exist_ok=True)
    
    # PyInstaller command arguments
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        f"--distpath={build_dir}",
        f"--workpath={build_dir}/temp", 
        f"--specpath={build_dir}",
        "--name=AI_Script_Generator",
        "--hidden-import=customtkinter",
        "--hidden-import=tkinter",
        "--hidden-import=requests", 
        "--hidden-import=python-dotenv",
        "--hidden-import=chromadb",
        "--hidden-import=markdown2",
        "--hidden-import=yt-dlp",
        "--exclude-module=torch",
        "--exclude-module=torchvision",
        "--exclude-module=torchaudio",
        "--exclude-module=torch.nn",
        "--exclude-module=torch.cuda",
        "--noconsole",  # Remove this line if you want to see console output for debugging
        str(main_file)
    ]
    
    print("Building executable with command:")
    print(" ".join(cmd))
    print()
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, cwd=project_root)
        print("\nBuild completed successfully!")
        print(f"Executable created at: {build_dir / 'AI_Script_Generator.exe'}")
        
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        return False
    
    return True

def main():
    """Main build function"""
    print("AI Script Generator - Build Script")
    print("=" * 50)
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Build executable
    print("\nBuilding executable...")
    success = build_executable()
    
    if success:
        print("\nBuild process completed successfully!")
        print("You can now run the executable from the build directory.")
    else:
        print("\nBuild process failed. Check the error messages above.")
        
if __name__ == "__main__":
    main()