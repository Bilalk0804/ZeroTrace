#!/usr/bin/env python3
"""
ZeroTrace Pro GUI - Linux Bootable OS Version
Optimized for Tiny Core Linux environment with direct hardware access
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import os
import sys
import threading
import time
import datetime
import platform

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import SecureWipeGUI
    from backend_interface import BackendInterface
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure gui.py and backend_interface.py are in the same directory")
    sys.exit(1)

class ZeroTraceLinuxGUI(SecureWipeGUI):
    """Linux-optimized version of ZeroTrace GUI for bootable OS"""
    
    def __init__(self, root):
        # Initialize with Linux-specific settings
        self.is_bootable_os = True
        self.hardware_access = True
        
        # Check if running as root (required for disk access)
        if os.geteuid() != 0:
            messagebox.showerror(
                "Root Access Required",
                "ZeroTrace Pro requires root privileges for direct disk access.\n"
                "The bootable OS should automatically provide this."
            )
        
        # Initialize parent class
        super().__init__(root)
        
        # Override title for bootable OS
        self.root.title("🔒 ZeroTrace Pro - Bootable Data Erasure Appliance")
        
        # Add bootable OS specific features
        self.setup_bootable_features()
    
    def setup_bootable_features(self):
        """Setup features specific to bootable OS"""
        # Enable full-screen mode option
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        
        # Add shutdown/reboot options
        self.add_power_management()
        
        # Auto-detect hardware on startup
        self.auto_detect_hardware()
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.root.attributes('-fullscreen', False)
    
    def add_power_management(self):
        """Add power management options to the GUI"""
        # Add power menu to the sidebar
        power_frame = tk.Frame(self.nav_frame, bg=self.colors['bg_secondary'])
        power_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=10)
        
        # Shutdown button
        shutdown_btn = tk.Button(power_frame, text="🔌 Shutdown",
                                font=('Segoe UI', 10),
                                bg=self.colors['danger'], fg=self.colors['text_primary'],
                                relief=tk.FLAT, bd=0, padx=12, pady=8,
                                command=self.shutdown_system)
        shutdown_btn.pack(fill=tk.X, pady=2)
        
        # Reboot button
        reboot_btn = tk.Button(power_frame, text="🔄 Reboot",
                              font=('Segoe UI', 10),
                              bg=self.colors['accent_orange'], fg=self.colors['text_primary'],
                              relief=tk.FLAT, bd=0, padx=12, pady=8,
                              command=self.reboot_system)
        reboot_btn.pack(fill=tk.X, pady=2)
    
    def shutdown_system(self):
        """Safely shutdown the system"""
        if messagebox.askyesno("Shutdown System", 
                              "Are you sure you want to shutdown the system?\n\n"
                              "Any unsaved data will be lost."):
            # Ensure no wipe operations are running
            if self.wipe_in_progress:
                messagebox.showwarning("Wipe in Progress", 
                                     "Cannot shutdown while wipe operation is running.")
                return
            
            # Clear memory and shutdown
            self.secure_shutdown()
    
    def reboot_system(self):
        """Safely reboot the system"""
        if messagebox.askyesno("Reboot System", 
                              "Are you sure you want to reboot the system?\n\n"
                              "Any unsaved data will be lost."):
            if self.wipe_in_progress:
                messagebox.showwarning("Wipe in Progress", 
                                     "Cannot reboot while wipe operation is running.")
                return
            
            self.secure_reboot()
    
    def secure_shutdown(self):
        """Perform secure shutdown with memory clearing"""
        try:
            # Clear sensitive data from memory
            self.clear_sensitive_memory()
            
            # Sync filesystems
            subprocess.run(['sync'], check=True)
            
            # Shutdown
            subprocess.run(['poweroff'], check=True)
        except Exception as e:
            messagebox.showerror("Shutdown Error", f"Failed to shutdown: {e}")
    
    def secure_reboot(self):
        """Perform secure reboot with memory clearing"""
        try:
            # Clear sensitive data from memory
            self.clear_sensitive_memory()
            
            # Sync filesystems
            subprocess.run(['sync'], check=True)
            
            # Reboot
            subprocess.run(['reboot'], check=True)
        except Exception as e:
            messagebox.showerror("Reboot Error", f"Failed to reboot: {e}")
    
    def clear_sensitive_memory(self):
        """Clear sensitive data from memory"""
        try:
            # Clear Python variables
            if hasattr(self, 'certificate_data'):
                self.certificate_data = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear system caches
            subprocess.run(['sync'], check=False)
            subprocess.run(['echo', '3', '>', '/proc/sys/vm/drop_caches'], 
                          shell=True, check=False)
        except Exception:
            pass  # Best effort
    
    def auto_detect_hardware(self):
        """Auto-detect hardware on startup"""
        def detect_thread():
            try:
                # Wait a moment for system to stabilize
                time.sleep(2)
                
                # Trigger hardware detection
                self.root.after(0, self.refresh_devices)
                
                # Update device count in UI
                devices = self.backend.get_disks()
                count = len(devices)
                
                self.root.after(0, lambda: self.update_device_count(count))
                
            except Exception as e:
                print(f"Hardware detection error: {e}")
        
        # Run detection in background
        thread = threading.Thread(target=detect_thread)
        thread.daemon = True
        thread.start()
    
    def update_device_count(self, count):
        """Update device count in sidebar"""
        if hasattr(self, 'device_count_label'):
            if count == 0:
                self.device_count_label.configure(text="No devices detected")
            elif count == 1:
                self.device_count_label.configure(text="1 device detected")
            else:
                self.device_count_label.configure(text=f"{count} devices detected")
    
    def get_system_info(self):
        """Get system information for the bootable OS"""
        try:
            info = {
                'os': 'ZeroTrace Pro Bootable OS',
                'kernel': platform.release(),
                'architecture': platform.machine(),
                'memory': self.get_memory_info(),
                'boot_time': self.get_boot_time()
            }
            return info
        except Exception:
            return {'os': 'ZeroTrace Pro Bootable OS', 'status': 'Unknown'}
    
    def get_memory_info(self):
        """Get memory information"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        mb = kb // 1024
                        return f"{mb} MB"
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def get_boot_time(self):
        """Get system boot time"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                uptime = datetime.timedelta(seconds=int(uptime_seconds))
                return str(uptime)
        except Exception:
            return "Unknown"

def setup_linux_environment():
    """Setup Linux environment for ZeroTrace"""
    try:
        # Ensure we have necessary permissions
        os.umask(0o022)
        
        # Set environment variables
        os.environ['PYTHONPATH'] = '/usr/local/share/zerotrace'
        
        # Check for required directories
        required_dirs = ['/tmp', '/var/log']
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        return True
    except Exception as e:
        print(f"Environment setup error: {e}")
        return False

def main():
    """Main function for Linux bootable OS"""
    print("🔒 ZeroTrace Pro - Bootable OS Starting...")
    
    # Setup Linux environment
    if not setup_linux_environment():
        print("Failed to setup Linux environment")
        sys.exit(1)
    
    # Create root window
    root = tk.Tk()
    
    # Configure for bootable OS
    root.configure(bg='#0f1419')
    
    # Set window properties
    root.title("🔒 ZeroTrace Pro - Bootable Data Erasure Appliance")
    
    # Start in fullscreen mode for appliance feel
    root.attributes('-fullscreen', True)
    
    # Create application
    try:
        app = ZeroTraceLinuxGUI(root)
        
        # Handle window close
        def on_closing():
            if app.wipe_in_progress:
                if messagebox.askokcancel("Wipe in Progress",
                                        "A wipe operation is currently in progress.\n"
                                        "Closing now may leave drives in an inconsistent state.\n\n"
                                        "Are you sure you want to exit?"):
                    app.wipe_in_progress = False
                    app.secure_shutdown()
            else:
                app.secure_shutdown()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        print("✅ ZeroTrace Pro GUI started successfully")
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting ZeroTrace Pro: {e}")
        messagebox.showerror("Startup Error", 
                           f"Failed to start ZeroTrace Pro:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
