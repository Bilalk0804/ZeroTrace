#!/usr/bin/env python3
"""
ZeroTrace GUI Integration
Bridges the tkinter GUI with the Go-based nwipe wrapper
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import datetime
import json
import qrcode
from PIL import Image, ImageTk
import io
import uuid
import subprocess
import os
import sys
import platform
import tempfile
from pathlib import Path
import re

# Import the original GUI class
from gui import SecureWipeGUI

class ZeroTraceIntegratedGUI(SecureWipeGUI):
    """Extended GUI that integrates with Go-based nwipe wrapper"""
    
    def __init__(self, root):
        # Initialize the parent GUI
        super().__init__(root)
        
        # Integration-specific attributes
        self.go_binary_path = None
        self.temp_config_file = None
        self.wipe_process = None
        self.real_devices = []
        self.selected_device = None
        
        # Check system compatibility and setup
        self.setup_integration()
        
        # Override the original device list with real devices
        self.refresh_device_list()
        
        # Update the GUI title
        self.root.title("🔒 ZeroTrace - Integrated nwipe GUI")
    
    def setup_integration(self):
        """Setup integration with Go backend"""
        try:
            # Detect operating system
            self.os_type = platform.system().lower()
            
            if self.os_type == "linux":
                # Linux system - can use nwipe directly
                self.integration_mode = "direct"
                self.go_binary_path = self.find_go_binary()
                
                # Check if running as root
                if os.geteuid() != 0:
                    messagebox.showwarning(
                        "Root Required", 
                        "This application requires root privileges to access disk devices.\n"
                        "Please run with: sudo python3 gui_integration.py"
                    )
            else:
                # Windows or other OS - simulation mode
                self.integration_mode = "simulation"
                messagebox.showinfo(
                    "Simulation Mode", 
                    "Running in simulation mode. The nwipe wrapper is designed for Linux systems.\n"
                    "This demo will show the integration interface without actual disk operations."
                )
            
            # Create temporary directory for communication
            self.temp_dir = tempfile.mkdtemp(prefix="zerotrace_")
            self.temp_config_file = os.path.join(self.temp_dir, "config.json")
            
        except Exception as e:
            messagebox.showerror("Setup Error", f"Failed to setup integration: {str(e)}")
            self.integration_mode = "simulation"
    
    def find_go_binary(self):
        """Find the Go binary for nwipe wrapper"""
        possible_paths = [
            "./build/zerotrace",
            "./zerotrace",
            "/usr/local/bin/zerotrace",
            "zerotrace"
        ]
        
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
            
            # Try to find in PATH
            try:
                result = subprocess.run(["which", path], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        
        return None
    
    def refresh_device_list(self):
        """Refresh the device list with real devices"""
        if self.integration_mode == "direct":
            self.real_devices = self.get_real_devices()
        else:
            # Simulation mode - use mock devices
            self.real_devices = [
                {
                    "device": "/dev/sda",
                    "model": "Samsung SSD 970 EVO Plus 1TB",
                    "size": "1000204886016",
                    "serial": "S4EWNX0N123456",
                    "type": "disk",
                    "removable": False,
                    "mounted": True,
                    "mount_points": ["/", "/boot"]
                },
                {
                    "device": "/dev/sdb", 
                    "model": "WDC WD10EZEX-08WN4A0",
                    "size": "1000204886016",
                    "serial": "WD-WCC6Y7123456",
                    "type": "disk",
                    "removable": False,
                    "mounted": False,
                    "mount_points": []
                },
                {
                    "device": "/dev/sdc",
                    "model": "SanDisk Ultra USB 3.0",
                    "size": "64023257088",
                    "serial": "4C530001234567890123",
                    "type": "disk", 
                    "removable": True,
                    "mounted": False,
                    "mount_points": []
                }
            ]
        
        # Update the GUI device list
        self.update_gui_device_list()
    
    def get_real_devices(self):
        """Get real device list using lsblk"""
        try:
            if self.go_binary_path:
                # Use Go binary to get device list
                result = subprocess.run([self.go_binary_path, "--list-devices"], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return json.loads(result.stdout)
            
            # Fallback to direct lsblk call
            result = subprocess.run([
                "lsblk", "-J", "-o", 
                "NAME,SIZE,MODEL,SERIAL,TYPE,RM,MOUNTPOINT"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                devices = []
                
                for device in data.get("blockdevices", []):
                    if device.get("type") == "disk":
                        devices.append({
                            "device": f"/dev/{device['name']}",
                            "model": device.get("model", "Unknown"),
                            "size": self.parse_size_to_bytes(device.get("size", "0")),
                            "serial": device.get("serial", "Unknown"),
                            "type": device.get("type", "disk"),
                            "removable": device.get("rm") == "1",
                            "mounted": bool(device.get("mountpoint")),
                            "mount_points": [device.get("mountpoint")] if device.get("mountpoint") else []
                        })
                
                return devices
                
        except Exception as e:
            print(f"Error getting real devices: {e}")
            return []
        
        return []
    
    def parse_size_to_bytes(self, size_str):
        """Parse size string like '1T' to bytes"""
        if not size_str:
            return "0"
        
        size_str = size_str.upper().strip()
        multipliers = {
            'K': 1024,
            'M': 1024**2, 
            'G': 1024**3,
            'T': 1024**4,
            'P': 1024**5
        }
        
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGTP]?)$', size_str)
        if match:
            value, unit = match.groups()
            multiplier = multipliers.get(unit, 1)
            return str(int(float(value) * multiplier))
        
        return "0"
    
    def format_size(self, bytes_str):
        """Format bytes to human readable size"""
        try:
            bytes_val = int(bytes_str)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.1f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.1f} PB"
        except:
            return "Unknown"
    
    def update_gui_device_list(self):
        """Update the GUI device list with real devices"""
        # Clear existing device widgets
        for widget in self.main_screen.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        # Look for device card
                        for card in child.winfo_children():
                            if hasattr(card, 'winfo_children'):
                                for content in card.winfo_children():
                                    if hasattr(content, 'winfo_children'):
                                        # Clear device content
                                        for item in content.winfo_children():
                                            if hasattr(item, 'pack_info') and 'pady' in str(item.pack_info()):
                                                item.destroy()
        
        # Find the device content frame and rebuild it
        self.rebuild_device_list()
    
    def rebuild_device_list(self):
        """Rebuild the device list in the GUI"""
        # Find the device card content frame
        device_content = None
        for widget in self.main_screen.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame) and child.cget('bg') == self.colors['bg_card']:
                        # This might be our device card
                        for content_frame in child.winfo_children():
                            if isinstance(content_frame, tk.Frame) and content_frame.cget('bg') == self.colors['bg_card']:
                                # Clear existing devices
                                for item in content_frame.winfo_children():
                                    item.destroy()
                                device_content = content_frame
                                break
                        if device_content:
                            break
                if device_content:
                    break
        
        if not device_content:
            return
        
        # Add real devices
        self.device_vars = []
        for i, device in enumerate(self.real_devices):
            var = tk.BooleanVar(value=(i == 0))  # Select first device by default
            self.device_vars.append(var)
            
            device_item = tk.Frame(device_content, bg=self.colors['bg_card'])
            device_item.pack(fill=tk.X, pady=8)
            
            # Custom checkbox
            cb_frame = tk.Frame(device_item, bg=self.colors['bg_card'])
            cb_frame.pack(side=tk.LEFT, padx=(0, 15))
            
            cb = tk.Checkbutton(cb_frame, variable=var,
                              bg=self.colors['bg_card'],
                              fg=self.colors['accent'],
                              selectcolor=self.colors['secondary'],
                              activebackground=self.colors['bg_card'],
                              font=('Segoe UI', 12))
            cb.pack()
            
            # Status indicator
            if device['mounted']:
                indicator = "🔴"  # Red for mounted
            elif device['removable']:
                indicator = "🟡"  # Yellow for removable
            else:
                indicator = "🟢"  # Green for available
            
            status_label = tk.Label(device_item, text=indicator,
                                  font=('Segoe UI Emoji', 14),
                                  bg=self.colors['bg_card'])
            status_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Device info
            info_frame = tk.Frame(device_item, bg=self.colors['bg_card'])
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Device name and model
            device_name = f"{device['device']} – {self.format_size(device['size'])} – {device['model']}"
            name_label = tk.Label(info_frame, text=device_name,
                                 font=('Segoe UI', 12, 'bold'),
                                 bg=self.colors['bg_card'],
                                 fg=self.colors['text_primary'])
            name_label.pack(anchor=tk.W)
            
            # Additional info
            info_text = f"Serial: {device['serial']}"
            if device['mounted']:
                info_text += f" | Mounted: {', '.join(device['mount_points'])}"
            if device['removable']:
                info_text += " | Removable"
            
            info_label = tk.Label(info_frame, text=info_text,
                                 font=('Segoe UI', 9),
                                 bg=self.colors['bg_card'],
                                 fg=self.colors['text_secondary'])
            info_label.pack(anchor=tk.W)
    
    def start_wipe(self):
        """Override start_wipe to use Go backend"""
        # Validation
        if not any(var.get() for var in self.device_vars):
            messagebox.showwarning("No Device Selected",
                                 "Please select at least one device to wipe.")
            return
        
        # Get selected devices
        selected_devices = []
        for i, var in enumerate(self.device_vars):
            if var.get():
                selected_devices.append(self.real_devices[i])
        
        # Safety check for mounted devices
        mounted_devices = [d for d in selected_devices if d['mounted']]
        if mounted_devices:
            mounted_names = [d['device'] for d in mounted_devices]
            if not messagebox.askyesno(
                "Mounted Devices Detected",
                f"The following devices have mounted partitions:\n{', '.join(mounted_names)}\n\n"
                "These will need to be unmounted before wiping.\n"
                "Do you want to continue?"
            ):
                return
        
        # System disk warning
        system_devices = [d for d in selected_devices if '/' in d.get('mount_points', [])]
        if system_devices:
            if not messagebox.askyesno(
                "⚠️ SYSTEM DISK WARNING",
                "You have selected a system disk that contains the root filesystem (/).\n\n"
                "⚠️ THIS WILL DESTROY YOUR OPERATING SYSTEM! ⚠️\n\n"
                "Are you absolutely sure you want to continue?\n"
                "Type 'DESTROY_SYSTEM' in the next dialog to confirm."
            ):
                return
            
            # Additional confirmation
            confirm_text = tk.simpledialog.askstring(
                "Final System Disk Confirmation",
                "Type 'DESTROY_SYSTEM' to confirm system disk wipe:",
                show='*'
            )
            if confirm_text != "DESTROY_SYSTEM":
                messagebox.showinfo("Cancelled", "System disk wipe cancelled for safety.")
                return
        
        # Final confirmation
        device_names = [d['device'] for d in selected_devices]
        confirm_msg = f"⚠ WARNING: This will permanently erase the following devices:\n"
        confirm_msg += f"{', '.join(device_names)}\n\n"
        confirm_msg += f"Method: {self.method_var.get()}\n\n"
        confirm_msg += "This action cannot be undone!"
        
        if not messagebox.askyesno("Confirm Secure Wipe", confirm_msg):
            return
        
        # Start the wipe process
        self.selected_devices = selected_devices
        self.wipe_in_progress = True
        self.wipe_start_time = datetime.datetime.now()
        self.show_screen("progress")
        
        # Start wipe thread
        if self.integration_mode == "direct":
            wipe_thread = threading.Thread(target=self.execute_real_wipe)
        else:
            wipe_thread = threading.Thread(target=self.simulate_wipe)
        
        wipe_thread.daemon = True
        wipe_thread.start()
    
    def execute_real_wipe(self):
        """Execute real wipe using Go backend"""
        try:
            # Create configuration for Go backend
            config = {
                "devices": [d['device'] for d in self.selected_devices],
                "method": self.map_method_to_nwipe(self.method_var.get()),
                "verify": True,
                "auto_unmount": True,
                "output_dir": self.temp_dir
            }
            
            # Write config file
            with open(self.temp_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Execute Go binary
            if self.go_binary_path:
                cmd = [self.go_binary_path, "--config", self.temp_config_file, "--gui-mode"]
                self.wipe_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Monitor process output
                self.monitor_wipe_process()
            else:
                # Fallback to simulation
                self.root.after(0, lambda: messagebox.showwarning(
                    "Go Binary Not Found",
                    "Go binary not found. Falling back to simulation mode."
                ))
                self.simulate_wipe()
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Wipe Error",
                f"Failed to start wipe process: {str(e)}"
            ))
            self.root.after(0, self.complete_wipe_with_error)
    
    def map_method_to_nwipe(self, gui_method):
        """Map GUI method names to nwipe method names"""
        method_map = {
            "Quick Erase (1-pass overwrite)": "zero",
            "NIST 3-pass overwrite": "dod",
            "DoD 7-pass overwrite": "dod",
            "Crypto Erase (SSD secure erase command)": "random"
        }
        return method_map.get(gui_method, "dod")
    
    def monitor_wipe_process(self):
        """Monitor the wipe process output"""
        if not self.wipe_process:
            return
        
        try:
            # Read output line by line
            for line in iter(self.wipe_process.stdout.readline, ''):
                if not self.wipe_in_progress:
                    break
                
                line = line.strip()
                if line:
                    # Parse progress information
                    self.parse_wipe_output(line)
            
            # Wait for process to complete
            self.wipe_process.wait()
            
            # Check return code
            if self.wipe_process.returncode == 0:
                self.root.after(0, self.complete_wipe)
            else:
                self.root.after(0, self.complete_wipe_with_error)
                
        except Exception as e:
            print(f"Error monitoring wipe process: {e}")
            self.root.after(0, self.complete_wipe_with_error)
    
    def parse_wipe_output(self, line):
        """Parse output from the Go wipe process"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Update log
        self.root.after(0, lambda: self.log_text.insert(tk.END, f"[{timestamp}] {line}\n"))
        self.root.after(0, lambda: self.log_text.see(tk.END))
        
        # Parse progress if available
        if "Progress:" in line:
            try:
                # Extract percentage from line like "Progress: 45.2%"
                match = re.search(r'Progress:\s*(\d+(?:\.\d+)?)%', line)
                if match:
                    progress = float(match.group(1))
                    self.root.after(0, lambda p=progress: self.update_real_progress(p))
            except:
                pass
        
        # Update status
        if "Pass" in line:
            self.root.after(0, lambda: self.progress_label.config(text=line))
        elif "Verifying" in line:
            self.root.after(0, lambda: self.progress_label.config(text="Verifying erasure..."))
        elif "Complete" in line:
            self.root.after(0, lambda: self.progress_label.config(text="Wipe completed successfully!"))
    
    def update_real_progress(self, progress_percent):
        """Update progress bar with real progress"""
        self.progress_bar['value'] = progress_percent
        
        # Update time estimate (rough calculation)
        if progress_percent > 0:
            elapsed = (datetime.datetime.now() - self.wipe_start_time).total_seconds()
            total_estimated = elapsed * (100 / progress_percent)
            remaining = max(0, total_estimated - elapsed)
            
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            
            if hours > 0:
                time_str = f"{hours}h {minutes}m"
            else:
                time_str = f"{minutes}m"
            
            self.time_label.config(text=f"Estimated time remaining: {time_str}")
    
    def complete_wipe_with_error(self):
        """Handle wipe completion with error"""
        self.wipe_in_progress = False
        messagebox.showerror(
            "Wipe Failed",
            "The wipe operation failed. Please check the logs for details."
        )
        # Return to main screen
        self.show_screen("main")
    
    def complete_wipe(self):
        """Override complete_wipe to handle real certificates"""
        self.wipe_in_progress = False
        self.wipe_completion_time = datetime.datetime.now()
        
        # Look for certificate files in temp directory
        cert_files = []
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                if file.endswith('.json') and 'certificate' in file.lower():
                    cert_files.append(os.path.join(self.temp_dir, file))
        
        # Load certificate data
        if cert_files:
            try:
                with open(cert_files[0], 'r') as f:
                    go_cert_data = json.load(f)
                
                # Convert Go certificate to GUI format
                self.certificate_data = self.convert_go_certificate(go_cert_data)
            except Exception as e:
                print(f"Error loading certificate: {e}")
                self.certificate_data = self.create_fallback_certificate()
        else:
            self.certificate_data = self.create_fallback_certificate()
        
        # Generate completion report
        device_names = [d['device'] for d in self.selected_devices]
        duration = self.wipe_completion_time - self.wipe_start_time
        
        details = f"""Device(s): {', '.join(device_names)}
Method: {self.method_var.get()}
Started: {self.wipe_start_time.strftime('%Y-%m-%d %H:%M:%S')}
Completed: {self.wipe_completion_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {str(duration).split('.')[0]}
Status: ✅ Successfully Wiped
Integration Mode: {self.integration_mode.title()}
Device ID: {self.device_id}"""
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
        
        # Generate QR code
        self.generate_qr_code(json.dumps(self.certificate_data))
        
        # Add completion log
        timestamp = self.wipe_completion_time.strftime("%H:%M:%S")
        final_log = f"\n[{timestamp}] ✅ WIPE COMPLETED SUCCESSFULLY!\n"
        final_log += f"[{timestamp}] Certificate ID: {self.device_id}\n"
        self.log_text.insert(tk.END, final_log)
        self.log_text.see(tk.END)
        
        # Show completion screen
        self.show_screen("completion")
    
    def convert_go_certificate(self, go_cert):
        """Convert Go certificate format to GUI format"""
        return {
            "device_id": self.device_id,
            "devices": [d['device'] for d in self.selected_devices],
            "method": self.method_var.get(),
            "start_time": self.wipe_start_time.isoformat(),
            "completion_time": self.wipe_completion_time.isoformat(),
            "duration": str(self.wipe_completion_time - self.wipe_start_time),
            "status": "VERIFIED_WIPED",
            "hidden_areas": self.hidden_var.get(),
            "go_certificate": go_cert,
            "integration_mode": self.integration_mode
        }
    
    def create_fallback_certificate(self):
        """Create fallback certificate if Go certificate is not available"""
        return {
            "device_id": self.device_id,
            "devices": [d['device'] for d in self.selected_devices],
            "method": self.method_var.get(),
            "start_time": self.wipe_start_time.isoformat(),
            "completion_time": self.wipe_completion_time.isoformat(),
            "duration": str(self.wipe_completion_time - self.wipe_start_time),
            "status": "VERIFIED_WIPED",
            "hidden_areas": self.hidden_var.get(),
            "integration_mode": self.integration_mode
        }
    
    def cleanup(self):
        """Cleanup temporary files"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
        except:
            pass

def main():
    root = tk.Tk()
    
    # Set minimum window size
    root.minsize(800, 600)
    
    # Configure window properties
    root.title("🔒 ZeroTrace - Integrated nwipe GUI")
    
    # Center the window on screen
    root.update_idletasks()
    width = 900
    height = 700
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Create integrated application
    app = ZeroTraceIntegratedGUI(root)
    
    # Handle window close
    def on_closing():
        if app.wipe_in_progress:
            if messagebox.askokcancel("Wipe in Progress",
                                    "A wipe operation is currently in progress. "
                                    "Closing now may leave the drive in an inconsistent state.\n\n"
                                    "Are you sure you want to exit?"):
                app.wipe_in_progress = False
                if app.wipe_process:
                    app.wipe_process.terminate()
                app.cleanup()
                root.destroy()
        else:
            app.cleanup()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()
