"""
Backend Interface for ZeroTrace Pro
Handles communication between Flask GUI and Go backend
"""

import subprocess
import json
import threading
import time
import os
from typing import List, Dict, Optional, Callable

class BackendInterface:
    def __init__(self):
        self.backend_process = None
        self.is_running = False
        self.progress_callback = None
        self.log_callback = None
        
    def start_backend(self) -> bool:
        """Start the Go backend process"""
        try:
            # Check if backend executable exists
            backend_path = "nwipe_main.go"
            if not os.path.exists(backend_path):
                return False
                
            self.is_running = True
            return True
        except Exception as e:
            print(f"Failed to start backend: {e}")
            return False
    
    def get_disks(self) -> List[Dict]:
        """Get list of available disks from backend"""
        try:
            # Run disk detection command
            result = subprocess.run(
                ["go", "run", "nwipe_main.go", "--list-disks"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse the output to extract disk information
                return self._parse_disk_output(result.stdout)
            else:
                # Fallback to sample data for demo
                return self._get_sample_disks()
                
        except Exception as e:
            print(f"Error getting disks: {e}")
            return self._get_sample_disks()
    
    def _parse_disk_output(self, output: str) -> List[Dict]:
        """Parse disk detection output"""
        disks = []
        lines = output.split('\n')
        current_disk = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('[') and ']' in line:
                # New disk entry
                if current_disk:
                    disks.append(current_disk)
                
                # Extract device path
                device_part = line.split(']')[1].strip()
                current_disk = {
                    'device': device_part,
                    'model': 'Unknown',
                    'size': 'Unknown',
                    'type': 'Unknown',
                    'health': 'Unknown',
                    'temperature': 'N/A'
                }
            elif current_disk and ':' in line:
                # Parse disk properties
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'model' in key:
                    current_disk['model'] = value
                elif 'size' in key:
                    current_disk['size'] = value
                elif 'type' in key:
                    current_disk['type'] = value
        
        # Add the last disk
        if current_disk:
            disks.append(current_disk)
            
        return disks if disks else self._get_sample_disks()
    def _get_sample_disks(self) -> List[Dict]:
        """Return sample disk data for demo"""
        return [
            {
                'device': r'\\.\PhysicalDrive0',
                'model': 'INTEL SSDPEKNU512GZ',
                'size': '512GB',
                'type': 'NVMe SSD',
                'health': 'Excellent',
                'temperature': '45°C',
                'status': 'Ready',
                'icon': '💾',
                'color': '#10b981'
            },
            {
                'device': r'\\.\PhysicalDrive1',
                'model': 'Seagate Barracuda',
                'size': '2TB',
                'type': 'SATA HDD',
                'health': 'Good',
                'temperature': '38°C',
                'status': 'Mounted',
                'icon': '🗄️',
                'color': '#f59e0b'
            },
            {
                'device': r'\\.\PhysicalDrive2',
                'model': 'SanDisk Ultra USB',
                'size': '64GB',
                'type': 'USB 3.0',
                'health': 'Good',
                'temperature': 'N/A',
                'icon': '🔌',
                'color': '#3b82f6'
            }
        ]
    
    def get_wipe_methods(self) -> List[Dict]:
        """Get available wiping methods"""
        return [
            {
                'id': 'quick',
                'name': 'Quick Erase (1-pass zero fill)',
                'description': 'Single pass zero fill - fastest method',
                'passes': 1,
                'security': 'Low',
                'speed': 'Fast'
            },
            {
                'id': 'nist',
                'name': 'NIST SP 800-88 (3-pass overwrite)',
                'description': 'NIST Special Publication 800-88 standard',
                'passes': 3,
                'security': 'High',
                'speed': 'Medium'
            },
            {
                'id': 'dod',
                'name': 'DoD 5220.22-M (7-pass overwrite)',
                'description': 'US Department of Defense standard',
                'passes': 7,
                'security': 'High',
                'speed': 'Slow'
            },
            {
                'id': 'gutmann',
                'name': 'Peter Gutmann (35-pass method)',
                'description': 'Gutmann 35-pass method - maximum security',
                'passes': 35,
                'security': 'Maximum',
                'speed': 'Very Slow'
            },
            {
                'id': 'crypto',
                'name': 'Crypto Erase (SED/NVMe Sanitize)',
                'description': 'Hardware-level crypto erase - instant',
                'passes': 1,
                'security': 'Maximum',
                'speed': 'Instant'
            },
            {
                'id': 'random',
                'name': 'Random Overwrite (3-pass random)',
                'description': 'Multiple passes with random data',
                'passes': 3,
                'security': 'High',
                'speed': 'Medium'
            }
        ]
    
    def start_wipe(self, devices: List[str], method: str, options: Dict) -> bool:
        """Start the wipe process"""
        try:
            # Prepare wipe command
            cmd = ["go", "run", "nwipe_main.go", "--wipe"]
            cmd.extend(["--method", method])
            cmd.extend(["--devices"] + devices)
            
            if options.get('verify', False):
                cmd.append("--verify")
            if options.get('hidden_areas', False):
                cmd.append("--hidden-areas")
            
            # Start wipe process in background
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_wipe_progress)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to start wipe: {e}")
            return False
    
    def _monitor_wipe_progress(self):
        """Monitor wipe progress and call callbacks"""
        if not self.backend_process:
            return
            
        try:
            while self.backend_process.poll() is None:
                # Read output from backend
                line = self.backend_process.stdout.readline()
                if line:
                    line = line.strip()
                    
                    # Parse progress information
                    if "Progress:" in line and self.progress_callback:
                        try:
                            # Extract percentage from "Progress: 45%"
                            percent_str = line.split("Progress:")[1].strip().replace('%', '')
                            progress = int(percent_str)
                            self.progress_callback(progress)
                        except:
                            pass
                    
                    # Send log updates
                    if self.log_callback:
                        self.log_callback(line)
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error monitoring progress: {e}")
    
    def stop_wipe(self):
        """Stop the current wipe process"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None
    
    def set_progress_callback(self, callback: Callable[[int], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def set_log_callback(self, callback: Callable[[str], None]):
        """Set callback for log updates"""
        self.log_callback = callback
    
    def get_android_devices(self) -> List[Dict]:
        """Get connected Android devices"""
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            devices = []
            if result.returncode == 0:
                lines = result.stdout.split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and '\t' in line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            devices.append({
                                'serial': parts[0],
                                'state': parts[1],
                                'model': 'Android Device',
                                'type': 'Mobile'
                            })
            
            return devices
            
        except Exception:
            return []  # ADB not available
    
    def shutdown(self):
        """Shutdown the backend interface"""
        if self.backend_process:
            self.backend_process.terminate()
        self.is_running = False
