#!/usr/bin/env python3
"""
ZeroTrace GUI Launcher
Cross-platform launcher for the integrated GUI
"""

import sys
import os
import platform
import subprocess
import tkinter as tk
from tkinter import messagebox
import importlib.util

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    # Check Python modules
    required_modules = [
        'tkinter', 'PIL', 'qrcode', 'reportlab'
    ]
    
    for module in required_modules:
        try:
            if module == 'PIL':
                import PIL
            elif module == 'tkinter':
                import tkinter
            elif module == 'qrcode':
                import qrcode
            elif module == 'reportlab':
                import reportlab
        except ImportError:
            missing_deps.append(module)
    
    return missing_deps

def install_dependencies():
    """Install missing dependencies"""
    missing = check_dependencies()
    
    if not missing:
        return True
    
    print("Missing dependencies detected:", missing)
    
    # Create a simple GUI to ask user about installation
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    install_map = {
        'PIL': 'Pillow',
        'qrcode': 'qrcode[pil]',
        'reportlab': 'reportlab',
        'tkinter': 'tkinter (usually pre-installed)'
    }
    
    missing_names = [install_map.get(dep, dep) for dep in missing]
    
    response = messagebox.askyesno(
        "Missing Dependencies",
        f"The following Python packages are required but not installed:\n\n"
        f"{', '.join(missing_names)}\n\n"
        f"Would you like to install them automatically using pip?"
    )
    
    root.destroy()
    
    if not response:
        return False
    
    # Install packages
    for dep in missing:
        if dep == 'tkinter':
            print("tkinter is usually pre-installed with Python. Please install it manually.")
            continue
        
        package_name = install_map.get(dep, dep)
        print(f"Installing {package_name}...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package_name
            ])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e}")
            return False
    
    return True

def check_system_requirements():
    """Check system requirements"""
    system = platform.system().lower()
    
    if system == "linux":
        # Check if running as root for actual disk operations
        if os.geteuid() == 0:
            print("✓ Running as root - disk operations enabled")
            return "direct"
        else:
            print("⚠ Not running as root - simulation mode only")
            return "simulation"
    else:
        print(f"⚠ Running on {system} - simulation mode only")
        return "simulation"

def find_go_binary():
    """Find the Go binary"""
    possible_paths = [
        "./build/zerotrace",
        "./zerotrace", 
        "/usr/local/bin/zerotrace",
        "zerotrace"
    ]
    
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    # Try PATH
    try:
        result = subprocess.run(["which", "zerotrace"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

def build_go_binary():
    """Build the Go binary if source is available"""
    if not os.path.exists("nwipe_main.go"):
        return False
    
    print("Building Go binary...")
    try:
        # Try using Makefile first
        if os.path.exists("Makefile"):
            result = subprocess.run(["make", "build"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True
        
        # Fallback to direct go build
        result = subprocess.run([
            "go", "build", "-o", "build/zerotrace", 
            "nwipe_main.go", "config.go", "utils.go", "gui_backend.go"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            print(f"Build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Build error: {e}")
        return False

def main():
    """Main launcher function"""
    print("🔒 ZeroTrace GUI Launcher")
    print("=" * 40)
    
    # Check Python dependencies
    print("Checking Python dependencies...")
    if not install_dependencies():
        print("❌ Failed to install required dependencies")
        return 1
    
    print("✓ Python dependencies satisfied")
    
    # Check system requirements
    print("Checking system requirements...")
    mode = check_system_requirements()
    
    # Check for Go binary
    print("Checking Go backend...")
    go_binary = find_go_binary()
    
    if not go_binary:
        print("Go binary not found. Attempting to build...")
        if build_go_binary():
            go_binary = find_go_binary()
            if go_binary:
                print(f"✓ Built Go binary: {go_binary}")
            else:
                print("⚠ Build succeeded but binary not found")
        else:
            print("⚠ Failed to build Go binary - using simulation mode")
    else:
        print(f"✓ Found Go binary: {go_binary}")
    
    # Launch GUI
    print("\nLaunching ZeroTrace GUI...")
    print("=" * 40)
    
    try:
        # Import and run the integrated GUI
        if os.path.exists("gui_integration.py"):
            # Run the integrated version
            subprocess.run([sys.executable, "gui_integration.py"])
        elif os.path.exists("gui.py"):
            # Fallback to original GUI
            print("Using original GUI (no Go integration)")
            subprocess.run([sys.executable, "gui.py"])
        else:
            print("❌ GUI files not found")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Failed to launch GUI: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
