# ZeroTrace Pro - Advanced Cross-Platform Data Erasure

A comprehensive, professional-grade data erasure solution supporting Windows, Linux, macOS, and Android devices. ZeroTrace Pro combines traditional overwriting methods with modern hardware-based secure erase techniques for maximum data security.

## Features

### 🖥️ **Cross-Platform Support**
- **Windows**: PowerShell-based disk detection, NVMe sanitize, BitLocker integration
- **Linux**: lsblk integration, nwipe wrapper, hdparm secure erase
- **macOS**: diskutil integration, APFS secure erase
- **Android**: ADB/Fastboot support for mobile device wiping

### 🔒 **Advanced Wiping Methods**
- **Quick Erase**: Single-pass zero fill (fastest)
- **NIST SP 800-88**: 3-pass overwrite (recommended standard)
- **DoD 5220.22-M**: 7-pass Department of Defense standard
- **Peter Gutmann**: 35-pass method for maximum legacy drive security
- **Random Overwrite**: Cryptographically secure random data
- **Crypto Erase**: SED (Self-Encrypting Drive) instant crypto erase
- **NVMe Sanitize**: Hardware-level NVMe sanitize commands
- **Custom Patterns**: User-defined overwrite patterns

### 🛡️ **Enterprise Features**
- **hdparm Integration**: Hardware secure erase commands
- **NVMe Sanitize**: Block erase, crypto erase, overwrite sanitize
- **SED Support**: Self-Encrypting Drive crypto erase
- **HPA/DCO**: Hidden Protected Area and Device Configuration Overlay wiping
- **SMART Monitoring**: Disk health and temperature monitoring
- **Parallel Processing**: Multi-threaded wiping for faster completion

### 📱 **Android Device Support**
- **ADB Integration**: Factory reset via Android Debug Bridge
- **Fastboot Format**: Bootloader-level partition formatting
- **Root Secure Wipe**: Direct block device overwriting (requires root)
- **Encryption Detection**: Automatic detection of device encryption status

### 🔐 **Security & Compliance**
- **Cryptographic Certificates**: ECDSA-signed completion certificates
- **PDF Reports**: Professional compliance documentation
- **Audit Trails**: Comprehensive logging and verification
- **Hash Verification**: Post-wipe integrity verification
- **Standards Compliance**: NIST, DoD, and industry standards

## Requirements

### 🖥️ **System Requirements**
- **Operating Systems**: Windows 10/11, Linux (any distribution), macOS 10.15+
- **Privileges**: Administrator/root access required
- **Architecture**: x64, ARM64 supported

### 🛠️ **Dependencies**
- **Go**: 1.21 or later for compilation
- **Python**: 3.8+ for GUI (optional)

### 📦 **Platform-Specific Tools**

#### Linux
- `lsblk`, `smartctl`, `hdparm` (usually pre-installed)
- `nwipe` (auto-installed on Arch-based systems)
- `nvme-cli` (for NVMe sanitize support)
- `sedutil-cli` (for SED crypto erase)

#### Windows
- PowerShell 5.0+ (built-in)
- Windows Management Instrumentation (WMI)
- Optional: `sdelete`, `cipher` for additional methods

#### macOS
- `diskutil` (built-in)
- `system_profiler` (built-in)
- Optional: `gshred` via Homebrew

#### Android Support
- `adb` (Android Debug Bridge)
- `fastboot` (for bootloader operations)
- USB debugging enabled on target devices

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ZeroTrace
   ```

2. **Install Go dependencies**:
   ```bash
   go mod tidy
   ```

3. **Build the application**:
   ```bash
   go build -o zerotrace nwipe_main.go config.go utils.go
   ```

4. **Make executable**:
   ```bash
   chmod +x zerotrace
   ```

## Usage

### Basic Usage

Run the tool with root privileges:

```bash
sudo ./zerotrace
```

### Command Line Options

The tool provides an interactive interface that guides you through:

1. **Disk Selection**: Lists all available disks with detailed information
2. **Safety Checks**: Verifies the selected disk and handles mounted partitions
3. **Wipe Configuration**: Choose wiping method, rounds, and verification options
4. **Final Confirmation**: Multiple confirmation steps to prevent accidents

### 🔄 **Wiping Methods**

#### Traditional Overwriting
- **Quick Erase**: Single zero-fill pass (fastest, basic security)
- **NIST SP 800-88**: 3-pass overwrite (recommended for most use cases)
- **DoD 5220.22-M**: 7-pass DoD standard (high security)
- **Peter Gutmann**: 35-pass method (maximum security for legacy drives)
- **Random Overwrite**: Multiple passes with cryptographically secure random data
- **Custom Pattern**: User-defined patterns and pass counts

#### Hardware-Based Methods
- **NVMe Sanitize**: 
  - Crypto Erase: Instant encryption key destruction
  - Block Erase: Physical block-level erasure
  - Overwrite: Hardware-accelerated overwriting
- **SED Crypto Erase**: Self-Encrypting Drive key destruction
- **ATA Secure Erase**: Hardware-level secure erase command
- **Enhanced Secure Erase**: Time-optimized hardware erase

#### Mobile Device Methods
- **Factory Reset**: Standard Android factory reset
- **Fastboot Format**: Bootloader-level partition formatting
- **Secure Wipe**: Direct block device overwriting (root required)
- **Encryption Wipe**: Encryption key destruction on encrypted devices

### 🛡️ **Safety Features**

#### Pre-Wipe Validation
- **Privilege Verification**: Ensures administrator/root access
- **System Disk Protection**: Prevents accidental OS disk wiping
- **Mount Point Detection**: Identifies and safely handles mounted filesystems
- **Device Accessibility**: Validates device paths and permissions
- **Hardware Compatibility**: Checks for supported erase methods

#### Interactive Safeguards
- **Multiple Confirmations**: Step-by-step confirmation process
- **Device Information Display**: Shows detailed disk information before wiping
- **Method Explanation**: Clear description of selected wiping method
- **Time Estimation**: Provides estimated completion time
- **Abort Capability**: Allows safe cancellation during operation

#### Monitoring & Logging
- **Real-time Progress**: Live progress monitoring with ETA
- **Health Monitoring**: SMART data and temperature tracking
- **Comprehensive Logging**: Detailed operation logs for audit trails
- **Error Detection**: Automatic detection and reporting of issues
- **Verification**: Post-wipe verification and integrity checking

## Configuration

ZeroTrace Pro creates a configuration file at `config/zerotrace.json` with comprehensive options:

```json
{
  "default_method": "nist",
  "default_rounds": 3,
  "default_verify": true,
  "require_root_confirmation": true,
  "allow_system_disk_wipe": false,
  "auto_unmount": false,
  "output_directory": "output",
  "log_level": "info",
  "create_pdf": true,
  "sign_certificates": true,
  "key_path": "output/signer_key.pem",
  "parallel_processing": true,
  "max_threads": 4,
  "include_hidden_areas": false,
  "prefer_hardware_erase": true,
  "nvme_sanitize_method": "crypto",
  "android_adb_timeout": 300,
  "smart_monitoring": true,
  "temperature_threshold": 70,
  "gui_theme": "fleet_dark",
  "auto_detect_methods": true,
  "compliance_mode": "nist"
}
```

### Configuration Options

- **default_method**: Default wiping method (quick, nist, dod, gutmann, crypto, nvme_sanitize)
- **parallel_processing**: Enable multi-threaded operations
- **include_hidden_areas**: Wipe HPA/DCO areas
- **prefer_hardware_erase**: Use hardware methods when available
- **nvme_sanitize_method**: NVMe sanitize type (crypto, block, overwrite)
- **smart_monitoring**: Enable SMART health monitoring
- **compliance_mode**: Compliance standard (nist, dod, custom)

## Output Files

ZeroTrace Pro generates comprehensive documentation in the `output/` directory:

### 📋 **Certificates & Reports**
- **JSON Certificate**: `wipe_certificate_<device>.json` - Machine-readable certificate
- **PDF Certificate**: `wipe_certificate_<device>.pdf` - Professional compliance report
- **QR Verification**: Embedded QR codes for third-party verification
- **Audit Summary**: `audit_summary_<timestamp>.json` - Batch operation summary

### 📊 **Logs & Monitoring**
- **Operation Log**: `wipe_log_<device>_<timestamp>.log` - Detailed operation log
- **SMART Data**: `smart_data_<device>_<timestamp>.json` - Pre/post-wipe SMART data
- **Performance Metrics**: `performance_<device>_<timestamp>.json` - Speed and efficiency data
- **Error Log**: `errors_<timestamp>.log` - Error and warning log

### 🔐 **Security Files**
- **Signing Key**: `signer_key.pem` - ECDSA private key for certificate signing
- **Public Key**: `public_key.pem` - Public key for certificate verification
- **Hash Verification**: `verification_hashes_<device>.json` - Post-wipe hash verification

### 📱 **Android-Specific**
- **Device Info**: `android_device_<serial>.json` - Device information and capabilities
- **ADB Log**: `adb_operations_<timestamp>.log` - ADB command log
- **Fastboot Log**: `fastboot_operations_<timestamp>.log` - Fastboot operation log

## Certificate Verification

Certificates are cryptographically signed using ECDSA P-256. To verify a certificate:

1. Extract the public key from the certificate
2. Verify the signature against the certificate data
3. Check the post-wipe hash for data destruction verification

## Security Considerations

- **Run as Root**: Required for direct disk access
- **Backup Important Data**: All data will be permanently destroyed
- **Verify Certificates**: Always verify certificate signatures
- **Secure Key Storage**: Protect the signing key file
- **Physical Security**: Ensure physical access control during wiping

## Troubleshooting

### Common Issues

1. **Permission Denied**:
   ```bash
   sudo ./zerotrace
   ```

2. **nwipe Not Found**:
   The tool will automatically install nwipe, but you can also install manually:
   ```bash
   sudo pacman -S nwipe
   ```

3. **Device Busy**:
   Unmount all partitions on the target device:
   ```bash
   sudo umount /dev/sdX*
   ```

4. **Build Errors**:
   Ensure Go 1.21+ is installed and dependencies are available:
   ```bash
   go mod tidy
   go build
   ```

### Log Files

Check the log files in the `output/` directory for detailed error information and operation progress.

## Legal and Compliance

### ⚖️ **Legal Considerations**
- **Data Destruction**: This tool permanently destroys data and cannot be undone
- **Authorization**: Users must ensure proper authorization before wiping any device
- **Liability**: Users are responsible for compliance with local laws and regulations
- **Chain of Custody**: Maintain proper documentation for legal proceedings

### 📜 **Compliance Standards**
- **NIST SP 800-88**: Guidelines for Media Sanitization
- **DoD 5220.22-M**: Department of Defense clearing and sanitizing standard
- **GDPR**: European General Data Protection Regulation compliance
- **HIPAA**: Health Insurance Portability and Accountability Act
- **SOX**: Sarbanes-Oxley Act compliance
- **PCI DSS**: Payment Card Industry Data Security Standard

### 🔍 **Verification & Audit**
- **Cryptographic Signatures**: ECDSA-signed certificates for authenticity
- **Third-Party Verification**: QR codes for independent verification
- **Audit Trails**: Comprehensive logging for compliance audits
- **Hash Verification**: Post-wipe integrity verification
- **Time Stamping**: RFC 3161 compliant timestamps

### 🌍 **International Standards**
- **ISO/IEC 27001**: Information security management
- **Common Criteria**: International security evaluation standard
- **FIPS 140-2**: Federal Information Processing Standard
- **BSI-GSK**: German Federal Office for Information Security guidelines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

**WARNING**: This tool permanently destroys data. Always ensure you have proper authorization and backups before using this tool. The authors are not responsible for any data loss or misuse of this software.

## Support

For issues, questions, or contributions, please:

1. Check the troubleshooting section
2. Review existing issues on GitHub
3. Create a new issue with detailed information
4. Include log files and system information

## Version History

### 🚀 **v2.0.0 - ZeroTrace Pro** (Current)
- **Cross-Platform Support**: Windows, Linux, macOS, Android
- **Advanced Methods**: NVMe sanitize, crypto erase, SED support
- **Fleet-Style GUI**: Modern dark theme interface
- **Android Integration**: ADB/Fastboot device wiping
- **Enterprise Features**: hdparm, parallel processing, SMART monitoring
- **Enhanced Security**: Multi-standard compliance, advanced verification

### 📈 **Previous Versions**
- **v1.2.0**: Added Gutmann method and custom patterns
- **v1.1.0**: GUI integration and progress monitoring
- **v1.0.2**: Enhanced safety checks and logging
- **v1.0.1**: Added configuration file support
- **v1.0.0**: Initial release with nwipe integration

### 🔮 **Roadmap**
- **v2.1.0**: Cloud integration and remote monitoring
- **v2.2.0**: AI-powered disk health prediction
- **v2.3.0**: Blockchain-based certificate verification
- **v3.0.0**: Quantum-resistant cryptographic signatures

## 🤝 **Contributing**

We welcome contributions to ZeroTrace Pro! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### 🐛 **Bug Reports**
- Use the GitHub issue tracker
- Include system information and logs
- Provide steps to reproduce
- Attach relevant configuration files

### 💡 **Feature Requests**
- Check existing issues first
- Provide detailed use case descriptions
- Consider security and compliance implications

## 📞 **Support**

- **Documentation**: Check the comprehensive docs in `/docs`
- **Issues**: GitHub issue tracker for bugs and features
- **Security**: Report security issues privately to security@zerotrace.dev
- **Commercial**: Enterprise support available

## 📄 **License**

ZeroTrace Pro is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
---

## ⚠️ **CRITICAL WARNING**

**ZeroTrace Pro permanently destroys data and cannot be undone. Always ensure you have proper authorization and verified backups before wiping any device. The authors are not responsible for any data loss or misuse of this software.**

### 🔒 **Security Notice**
- Always verify certificates and signatures
- Keep signing keys secure and backed up
- Regularly update to the latest version

---

*ZeroTrace Pro - Professional Data Erasure for the Modern World* 🌟
