#!/usr/bin/env python3
"""
ZeroTrace Functionality Test Script
Tests all major components of the ZeroTrace system
"""

import subprocess
import sys
import os
import json

def test_go_compilation():
    """Test if Go code compiles successfully"""
    print("🔨 Testing Go compilation...")
    try:
        result = subprocess.run([
            "go", "build", "-o", "test_zerotrace", 
            "nwipe_main.go", "config.go", "utils.go", "gui_backend.go"
        ], capture_output=True, text=True, cwd="/home/bilal/ZeroTrace")
        
        if result.returncode == 0:
            print("✅ Go compilation successful")
            return True
        else:
            print(f"❌ Go compilation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Go compilation error: {e}")
        return False

def test_go_binary():
    """Test if the Go binary works correctly"""
    print("🚀 Testing Go binary...")
    try:
        # Test help/version
        result = subprocess.run(["./test_zerotrace"], capture_output=True, text=True, cwd="/home/bilal/ZeroTrace")
        if "ZeroTrace Pro" in result.stdout:
            print("✅ Go binary runs successfully")
        else:
            print(f"❌ Go binary output unexpected: {result.stdout}")
            return False
        
        # Test JSON device listing
        result = subprocess.run(["./test_zerotrace", "--list-devices"], capture_output=True, text=True, cwd="/home/bilal/ZeroTrace")
        if result.returncode == 0:
            try:
                devices = json.loads(result.stdout)
                if isinstance(devices, list) and len(devices) > 0:
                    print(f"✅ JSON device listing works - found {len(devices)} devices")
                else:
                    print("❌ JSON device listing returned empty or invalid data")
                    return False
            except json.JSONDecodeError:
                print("❌ JSON device listing returned invalid JSON")
                return False
        else:
            print(f"❌ JSON device listing failed: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Go binary test error: {e}")
        return False

def test_python_dependencies():
    """Test if Python dependencies are available"""
    print("🐍 Testing Python dependencies...")
    try:
        import tkinter
        import PIL
        import qrcode
        import reportlab
        print("✅ All Python dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        return False

def test_python_syntax():
    """Test Python syntax for all Python files"""
    print("📝 Testing Python syntax...")
    python_files = ["gui.py", "backend_interface.py", "launch_gui.py"]
    
    for file in python_files:
        try:
            result = subprocess.run([
                "python3", "-m", "py_compile", file
            ], capture_output=True, text=True, cwd="/home/bilal/ZeroTrace")
            
            if result.returncode == 0:
                print(f"✅ {file} syntax OK")
            else:
                print(f"❌ {file} syntax error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error testing {file}: {e}")
            return False
    
    return True

def test_gui_import():
    """Test if GUI can be imported without errors"""
    print("🖥️ Testing GUI import...")
    try:
        # Change to the project directory
        os.chdir("/home/bilal/ZeroTrace")
        
        # Test importing the GUI module
        sys.path.insert(0, "/home/bilal/ZeroTrace")
        import gui
        print("✅ GUI module imports successfully")
        return True
    except Exception as e:
        print(f"❌ GUI import error: {e}")
        return False

def test_backend_interface():
    """Test backend interface functionality"""
    print("🔌 Testing backend interface...")
    try:
        os.chdir("/home/bilal/ZeroTrace")
        sys.path.insert(0, "/home/bilal/ZeroTrace")
        
        from backend_interface import BackendInterface
        
        # Create backend interface
        backend = BackendInterface()
        
        # Test getting wipe methods
        methods = backend.get_wipe_methods()
        if isinstance(methods, list) and len(methods) > 0:
            print(f"✅ Backend interface works - found {len(methods)} wipe methods")
        else:
            print("❌ Backend interface returned no wipe methods")
            return False
        
        # Test getting sample disks
        disks = backend._get_sample_disks()
        if isinstance(disks, list) and len(disks) > 0:
            print(f"✅ Sample disk data works - found {len(disks)} sample disks")
        else:
            print("❌ Sample disk data failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Backend interface test error: {e}")
        return False

def cleanup():
    """Clean up test files"""
    print("🧹 Cleaning up test files...")
    try:
        if os.path.exists("/home/bilal/ZeroTrace/test_zerotrace"):
            os.remove("/home/bilal/ZeroTrace/test_zerotrace")
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def main():
    """Run all tests"""
    print("🔒 ZeroTrace Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Go Compilation", test_go_compilation),
        ("Go Binary", test_go_binary),
        ("Python Dependencies", test_python_dependencies),
        ("Python Syntax", test_python_syntax),
        ("GUI Import", test_gui_import),
        ("Backend Interface", test_backend_interface),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ZeroTrace is ready to use.")
        print("\nTo run the GUI:")
        print("  python3 gui.py")
        print("  or")
        print("  python3 launch_gui.py")
        print("\nTo run the CLI:")
        print("  ./zerotrace")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    cleanup()
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
