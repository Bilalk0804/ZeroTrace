# ZeroTrace Pro Bootable OS Deployment Guide

## Overview

This guide covers deploying ZeroTrace Pro as a bootable operating system based on Tiny Core Linux. This creates a dedicated data erasure appliance that boots directly into the ZeroTrace interface.

## Benefits of Bootable OS

### Security Advantages
- **Isolated Environment**: No host OS interference or data leakage
- **Direct Hardware Access**: Full control over storage devices
- **Memory Security**: RAM is cleared on shutdown
- **No Persistence**: No traces left on the host system
- **Compliance Ready**: Meets strict data destruction standards

### Operational Advantages
- **Fast Boot**: Boots in under 30 seconds
- **Consistent Environment**: Same interface across all hardware
- **No Dependencies**: Self-contained with all required tools
- **Portable**: Single ISO works on any x86_64 system
- **Offline Capable**: No network required for operation

## System Requirements

### Minimum Hardware
- **CPU**: x86_64 (64-bit) processor
- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: USB drive (4GB+) or CD/DVD for booting
- **Display**: VGA/HDMI output for GUI

### Recommended Hardware
- **CPU**: Multi-core x86_64 processor
- **RAM**: 2GB+ for better performance
- **Storage**: USB 3.0 drive for faster boot
- **Network**: Ethernet (optional, for updates)

## Building the Bootable OS

### Prerequisites (Build System)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y squashfs-tools genisoimage syslinux-utils \
                    python3 golang-go wget git qemu-system-x86

# CentOS/RHEL/Fedora
sudo dnf install -y squashfs-tools genisoimage syslinux \
                    python3 golang wget git qemu-system-x86
```

### Build Process

1. **Clone Repository**
```bash
git clone <zerotrace-repo>
cd ZeroTracePro/bootable-os/build
```

2. **Build ISO**
```bash
# Quick build
make all

# Or step by step
make check-deps
make extensions
make iso
```

3. **Test in Virtual Machine**
```bash
make test-vm
```

## Deployment Methods

### Method 1: USB Drive (Recommended)

1. **Create USB Installer**
```bash
# Find USB device
lsblk

# Write ISO to USB (replace /dev/sdX with your USB device)
sudo dd if=build-output/zerotrace-pro-1.0.iso of=/dev/sdX bs=4M status=progress

# Sync and eject
sync
sudo eject /dev/sdX
```

2. **Boot from USB**
- Insert USB drive into target system
- Boot from USB (F12/F2/DEL during startup)
- ZeroTrace Pro will start automatically

### Method 2: CD/DVD

1. **Burn ISO to Disc**
```bash
# Using command line
wodim -v zerotrace-pro-1.0.iso

# Or use GUI tools like Brasero, K3b, etc.
```

2. **Boot from Disc**
- Insert CD/DVD into target system
- Boot from optical drive
- ZeroTrace Pro will start automatically

### Method 3: Network Boot (PXE)

1. **Setup PXE Server**
```bash
# Extract kernel and initramfs
mkdir pxe-files
mount -o loop zerotrace-pro-1.0.iso /mnt
cp /mnt/boot/vmlinuz64 pxe-files/
cp /mnt/boot/core.gz pxe-files/
umount /mnt
```

2. **Configure PXE Menu**
```
LABEL zerotrace
    MENU LABEL ZeroTrace Pro Data Erasure
    KERNEL vmlinuz64
    APPEND initrd=core.gz quiet
```

### Method 4: Virtual Machine Deployment

1. **VMware/VirtualBox**
- Create new VM with 1GB+ RAM
- Mount ISO as CD/DVD
- Boot from CD/DVD
- Configure VM for hardware passthrough if needed

2. **QEMU/KVM**
```bash
qemu-system-x86_64 -cdrom zerotrace-pro-1.0.iso -m 1024 -enable-kvm
```

## Usage Instructions

### First Boot

1. **System Startup**
   - System boots automatically to ZeroTrace Pro
   - Hardware detection runs automatically
   - GUI starts in fullscreen mode

2. **Interface Navigation**
   - Press `F11` to toggle fullscreen
   - Press `Escape` to exit fullscreen
   - Use mouse and keyboard normally

3. **Device Detection**
   - All connected storage devices are detected automatically
   - Devices show real-time status and health information
   - USB devices can be hot-plugged

### Operating the System

1. **Device Selection**
   - Check boxes next to devices to wipe
   - Review device information carefully
   - System warns about mounted/system devices

2. **Method Selection**
   - Choose appropriate wiping method
   - Configure verification options
   - Review security warnings

3. **Wipe Process**
   - Confirm operation (multiple confirmations for safety)
   - Monitor progress in real-time
   - View detailed logs

4. **Completion**
   - Generate compliance certificates
   - Export reports (if USB drive available)
   - Secure shutdown when complete

### Power Management

- **Shutdown**: Click "🔌 Shutdown" in sidebar
- **Reboot**: Click "🔄 Reboot" in sidebar
- **Emergency**: Hold power button (hardware reset)

## Security Features

### Memory Protection
- All sensitive data cleared on shutdown
- No swap files or persistent storage
- RAM-based temporary files only

### Hardware Access
- Direct disk access bypassing OS layers
- Raw device access for thorough wiping
- Hardware-level secure erase commands

### Audit Trail
- Complete operation logging
- Cryptographically signed certificates
- Compliance with data destruction standards

## Troubleshooting

### Boot Issues

**Problem**: System won't boot from USB
- **Solution**: Check BIOS/UEFI boot order
- **Solution**: Disable Secure Boot if enabled
- **Solution**: Try different USB port

**Problem**: Kernel panic on boot
- **Solution**: Check hardware compatibility
- **Solution**: Try safe mode boot options
- **Solution**: Update system firmware

### Hardware Issues

**Problem**: Devices not detected
- **Solution**: Check cable connections
- **Solution**: Try different SATA/USB ports
- **Solution**: Update device drivers

**Problem**: GUI not starting
- **Solution**: Check display connections
- **Solution**: Try different video output
- **Solution**: Boot in text mode for debugging

### Performance Issues

**Problem**: Slow wipe speeds
- **Solution**: Check device health
- **Solution**: Use faster connection (SATA vs USB)
- **Solution**: Ensure adequate cooling

## Customization

### Custom Boot Options

Edit `isolinux.cfg` to add custom boot parameters:
```
LABEL zerotrace-safe
    KERNEL /boot/vmlinuz64
    APPEND initrd=/boot/core.gz quiet acpi=off noapic
```

### Additional Software

Add custom extensions to `/cde/optional/` directory:
```bash
# Example: Add network tools
cp network-tools.tcz /path/to/iso/cde/optional/
```

### Branding

Customize splash screen and boot messages:
- Replace `isolinux.bin` for boot loader branding
- Modify `core.gz` for system messages
- Update GUI colors and logos

## Support and Updates

### Getting Help
- Check logs in `/tmp/zerotrace-startup.log`
- Review hardware compatibility lists
- Contact support with system information

### Updates
- Download new ISO releases
- Rebuild USB/CD with new version
- No in-place updates (security by design)

### Backup and Recovery
- Export certificates before shutdown
- Save logs to external media
- Document hardware configurations

## Compliance and Certification

### Standards Supported
- NIST SP 800-88 Rev. 1
- DoD 5220.22-M
- Common Criteria
- FIPS 140-2

### Audit Requirements
- Complete operation logging
- Cryptographic signatures
- Chain of custody documentation
- Hardware verification

### Reporting
- PDF certificate generation
- QR code verification
- Digital signatures
- Compliance templates
