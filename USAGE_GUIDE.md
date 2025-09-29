# ZeroTrace Usage Guide

## Quick Start

1. **Build the application**:
   ```bash
   make build
   ```

2. **Run the application**:
   ```bash
   sudo ./build/zerotrace
   ```

3. **Follow the interactive prompts** to select and wipe a disk.

## Step-by-Step Usage

### 1. Preparation

Before running ZeroTrace, ensure:
- You have root/sudo access
- All important data is backed up
- You know which disk you want to wipe
- The target disk is not currently in use by the system

### 2. Running ZeroTrace

```bash
sudo ./build/zerotrace
```

The application will:
1. Check for root privileges
2. Install nwipe if not present
3. Initialize the wrapper with cryptographic keys

### 3. Disk Selection

The tool will display all available disks:

```
Available disk devices:
=======================
[0] /dev/sda
    Model: Samsung SSD 970 EVO Plus 1TB
    Serial: S4EWNX0N123456
    Size: 1.0 TB
    Type: disk
    Removable: false
    Mounted: true
    Mount Points: /, /boot

[1] /dev/sdb
    Model: WDC WD10EZEX-08WN4A0
    Serial: WD-WCC6Y7123456
    Size: 1.0 TB
    Type: disk
    Removable: false
    Mounted: false
```

Enter the number corresponding to the disk you want to wipe.

### 4. Safety Checks

The tool performs several safety checks:

- **Mount Check**: Detects if the disk has mounted partitions
- **System Disk Check**: Warns if the disk contains system partitions (/, /boot, /home)
- **Confirmation Prompts**: Multiple confirmation steps

Example safety check:
```
=== Safety Checks for /dev/sdb ===
WARNING: /dev/sdb has mounted partitions: /mnt/data
Do you want to unmount all partitions? (yes/no): yes
Safety checks passed.
```

### 5. Wipe Configuration

Choose your wiping method:

```
=== Wipe Configuration ===
Available methods:
1. zero - Fill with zeros (fastest)
2. random - Fill with random data
3. dod - DoD 5220.22-M (3 passes)
4. gutmann - Gutmann method (35 passes)
5. custom - Custom number of random passes

Select method (1-5) [default: 3]: 3
Verify after wipe? (y/n) [default: y]: y
```

### 6. Final Confirmation

The tool shows a final summary:

```
=== FINAL CONFIRMATION ===
Device: /dev/sdb
Model: WDC WD10EZEX-08WN4A0
Size: 1.0 TB
Method: dod
Rounds: 1
Verify: true

WARNING: This operation will PERMANENTLY DESTROY all data on the selected disk!
This action cannot be undone!

Type 'WIPE_DISK_NOW' to proceed: WIPE_DISK_NOW
```

### 7. Wiping Process

The tool executes nwipe and shows progress:

```
Starting nwipe with command: nwipe --logfile=output/wipe_log__dev_sdb_20240923_160027.log --method=dod --verify /dev/sdb
This may take several hours depending on disk size and method...

nwipe 0.34
Device: /dev/sdb
Method: DoD 5220.22-M
Progress: [████████████████████████████████████████] 100%
Verification: [████████████████████████████████████████] 100%
```

### 8. Certificate Generation

After completion, the tool generates:

```
nwipe completed successfully!
Certificate saved: output/wipe_certificate__dev_sdb.json
PDF certificate saved: output/wipe_certificate__dev_sdb.pdf

=== Wipe Operation Completed ===
Certificate saved to: output/wipe_certificate__dev_sdb.json
```

## Output Files

### JSON Certificate
Contains machine-readable wipe information:
```json
{
  "tool_name": "ZeroTrace-nwipe-wrapper",
  "tool_version": "1.0.0",
  "device": "/dev/sdb",
  "model": "WDC WD10EZEX-08WN4A0",
  "timestamp_start": "2024-09-23T10:30:27Z",
  "timestamp_end": "2024-09-23T14:45:33Z",
  "method": "dod",
  "success": true,
  "signature": "MEUCIQDx..."
}
```

### PDF Certificate
Professional certificate suitable for compliance and auditing.

### Log File
Detailed nwipe operation log with all output and progress information.

## Advanced Usage

### Custom Configuration

Edit `config/zerotrace.json` to customize default behavior:

```json
{
  "default_method": "gutmann",
  "default_verify": true,
  "allow_system_disk_wipe": true,
  "auto_unmount": true
}
```

### Batch Operations

For multiple disks, run the tool multiple times or modify the source code to support batch operations.

### Certificate Verification

To verify a certificate signature:

1. Extract the public key from the certificate
2. Use the signature verification tools provided
3. Check the post-wipe hash for verification

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Solution: Run with `sudo`

2. **Device Busy**
   - Solution: Unmount all partitions first
   - Command: `sudo umount /dev/sdX*`

3. **nwipe Not Found**
   - Solution: Install manually: `sudo pacman -S nwipe`

4. **System Disk Warning**
   - Solution: Verify you're selecting the correct disk
   - Use `lsblk` to confirm disk layout

### Getting Help

1. Check the log files in `output/`
2. Run the test script: `./test_install.sh`
3. Review the README.md for detailed information
4. Check system requirements and dependencies

## Best Practices

1. **Always backup important data** before wiping
2. **Verify disk selection** multiple times
3. **Use appropriate wiping method** for your security needs
4. **Keep certificates** for compliance and auditing
5. **Test the process** on non-critical disks first
6. **Ensure physical security** during the wiping process

## Security Notes

- Certificates are cryptographically signed for authenticity
- Private keys are stored securely with proper permissions
- Post-wipe hashes provide verification of data destruction
- All operations are logged for audit trails
