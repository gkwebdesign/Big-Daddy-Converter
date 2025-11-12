#!/usr/bin/env python3
"""
Build script to create standalone .exe using PyInstaller
"""

import subprocess
import sys
import os
from pathlib import Path

def build_exe():
    """Build the executable using PyInstaller"""
    
    print("Building Image Converter executable...")
    print("-" * 50)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install PyInstaller: {e}")
            print("Please install PyInstaller manually: pip install pyinstaller")
            sys.exit(1)
    
    # Check if pyinstaller command is available
    try:
        result = subprocess.run(["pyinstaller", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("PyInstaller command not found in PATH.")
        print("Trying to use python -m PyInstaller instead...")
        pyinstaller_cmd = [sys.executable, "-m", "PyInstaller"]
    else:
        pyinstaller_cmd = ["pyinstaller"]
    
    # Check if icon file exists
    icon_path = Path("icon.png")
    if not icon_path.exists():
        print("Warning: icon.png not found. Building without icon...")
        icon_flag = []
    else:
        icon_flag = ["--icon=icon.png"]
    
    # PyInstaller command
    cmd = pyinstaller_cmd + [
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (GUI only)
        "--name=Big Daddy Converter",   # Executable name
        "--hidden-import=PIL._tkinter_finder",  # Ensure PIL works
        "--hidden-import=tkinterdnd2",   # Include tkinterdnd2
        "--hidden-import=PIL.Image",     # Ensure PIL Image works
        "--hidden-import=PIL.ImageTk",  # Ensure PIL ImageTk works
    ] + icon_flag + [
        "image_converter.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ Build successful!")
        exe_name = "Big Daddy Converter.exe" if sys.platform == "win32" else "Big Daddy Converter"
        print(f"✓ Executable location: {Path('dist') / exe_name}")
        print("\nYou can now distribute the .exe file from the dist/ folder.")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with error code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()

