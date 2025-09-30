"""
Backend Interface for ZeroTrace Pro
Handles communication between Flask GUI and Go backend
"""

import subprocess
import json
import threading
import time
import os
import platform
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
        # 1) Prefer native Linux detection (no root needed)
        try:
            if platform.system().lower() == 'linux':
                linux_disks = self._get_linux_disks_lsblk()
                if linux_disks:
                    return linux_disks
        except Exception as e:
            print(f"Linux disk detection failed: {e}")

        # 2) Fallback to Go backend JSON (if available)
        try:
            result = subprocess.run(
                ["./zerotrace", "--list-devices"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                # Try parsing as JSON first (newer path)
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, list) and data:
                        # Map to common format
                        mapped: List[Dict] = []
                        for d in data:
                            mapped.append({
                                'device': d.get('device') or d.get('path') or '',
                                'model': d.get('model', 'Unknown'),
                                'size': self._format_size_bytes(d.get('size')) if isinstance(d.get('size'), int) else d.get('size', 'Unknown'),
                                'type': d.get('type', 'Unknown'),
                                'health': d.get('health', 'Unknown'),
                                'temperature': d.get('temperature', 'N/A'),
                                'status': d.get('status', 'Ready'),
                                'icon': d.get('icon', '💾'),
                                'color': d.get('color', '#58a6ff')
                            })
                        if mapped:
                            return mapped
                except json.JSONDecodeError:
                    # Not JSON; try legacy text format
                    pass

                parsed = self._parse_disk_output(result.stdout)
                if parsed:
                    return parsed
        except Exception as e:
            print(f"Go backend disk detection failed: {e}")

        # 3) Final fallback: sample data
        return self._get_sample_disks()

    def _get_linux_disks_lsblk(self) -> List[Dict]:
        """Detect disks using lsblk -J and map to GUI format."""
        result = subprocess.run(
            [
                "lsblk", "-J", "-o",
                "NAME,TYPE,SIZE,MODEL,PATH,TRAN,HOTPLUG,ROTA,MOUNTPOINT,VENDOR,SERIAL"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return []

        data = json.loads(result.stdout)
        blockdevices = data.get('blockdevices') or []
        disks: List[Dict] = []

        for dev in blockdevices:
            if dev.get('type') != 'disk':
                continue

            device_path = dev.get('path') or f"/dev/{dev.get('name', '')}"
            size_str = dev.get('size') or 'Unknown'
            model = (dev.get('model') or '').strip() or 'Unknown Device'
            tran = (dev.get('tran') or '').upper()
            rotational = bool(dev.get('rota'))

            # Derive friendly type
            if tran == 'NVME':
                dtype = 'NVMe SSD'
            elif not rotational:
                dtype = 'SSD'
            elif tran in ('USB', 'SATA', 'ATA'):
                dtype = f"{tran} HDD" if rotational else f"{tran} SSD"
            else:
                dtype = 'Disk'

            disks.append({
                'device': device_path,
                'model': model,
                'size': size_str,
                'type': dtype,
                'health': 'Good',
                'temperature': 'N/A',
                'status': 'Ready',
                'icon': '💾',
                'color': '#58a6ff'
            })

        return disks

    def _format_size_bytes(self, value: Optional[int]) -> str:
        if value is None:
            return 'Unknown'
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        size = float(value)
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024.0
            idx += 1
        if idx == 0:
            return f"{int(size)}{units[idx]}"
        return f"{size:.0f}{units[idx]}"
    
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
            # Build a minimal GUI-mode config file for the Go backend
            output_dir = os.path.abspath(os.path.join(os.getcwd(), "output"))
            os.makedirs(output_dir, exist_ok=True)

            cfg = {
                "devices": devices,
                "method": method,
                "verify": bool(options.get("verify", False)),
                "auto_unmount": False,
                "output_dir": output_dir,
            }

            tmp_dir = os.path.join("/tmp", "zerotrace_gui")
            os.makedirs(tmp_dir, exist_ok=True)
            cfg_path = os.path.join(tmp_dir, "session_config.json")
            with open(cfg_path, "w") as f:
                json.dump(cfg, f)

            # Prefer compiled binary (faster startup) and GUI mode which emits Progress lines
            cmd = [
                os.path.abspath("./zerotrace"),
                "--gui-mode",
                "--config", cfg_path,
            ]

            # Start wipe process in background
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
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
            stdout = self.backend_process.stdout
            while True:
                line = stdout.readline()
                if not line:
                    # If process has exited and no more output, stop
                    if self.backend_process.poll() is not None:
                        # Drain any remaining buffered data
                        remaining = stdout.read()
                        if remaining:
                            for extra in remaining.splitlines():
                                self._emit_progress_and_log(extra)
                        break
                    time.sleep(0.05)
                    continue

                self._emit_progress_and_log(line)
                time.sleep(0.02)

        except Exception as e:
            print(f"Error monitoring progress: {e}")

    def _emit_progress_and_log(self, raw_line: str):
        line = raw_line.strip()
        if not line:
            return

        # Progress pattern: "Progress: 45%"
        if "Progress:" in line and self.progress_callback:
            try:
                percent_str = line.split("Progress:")[1].strip().replace('%', '')
                progress = int(percent_str)
                self.progress_callback(progress)
            except Exception:
                pass

        if self.log_callback:
            self.log_callback(line)
    
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
