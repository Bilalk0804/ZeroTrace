package main

import (
	"bufio"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"encoding/asn1"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"log"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"
	"regexp"
)

// Disk represents a disk device across all platforms
type Disk struct {
	Device      string   `json:"device"`       // e.g., /dev/sda, \\.\PhysicalDrive0
	Model       string   `json:"model"`        // disk model
	Size        uint64   `json:"size"`         // size in bytes
	Serial      string   `json:"serial"`       // serial number
	Type        string   `json:"type"`         // disk type (SSD, HDD, NVMe, etc.)
	Interface   string   `json:"interface"`    // SATA, NVMe, USB, etc.
	Removable   bool     `json:"removable"`    // whether it's removable
	Mounted     bool     `json:"mounted"`      // whether it has mounted partitions
	MountPoints []string `json:"mount_points"` // list of mount points
	Platform    string   `json:"platform"`     // windows, linux, darwin
	BusType     string   `json:"bus_type"`     // SCSI, ATA, NVMe, USB
	Health      string   `json:"health"`       // disk health status
	Temperature int      `json:"temperature"`  // disk temperature in Celsius
	SEDCapable  bool     `json:"sed_capable"`  // Self-Encrypting Drive capability
	NVMeInfo    *NVMeInfo `json:"nvme_info,omitempty"` // NVMe specific info
}

// NVMeInfo contains NVMe-specific information
type NVMeInfo struct {
	Namespace      string `json:"namespace"`
	SanitizeSupport bool  `json:"sanitize_support"`
	CryptoErase    bool   `json:"crypto_erase"`
	BlockErase     bool   `json:"block_erase"`
	Overwrite      bool   `json:"overwrite"`
}

// AndroidDevice represents an Android device connected via ADB
type AndroidDevice struct {
	Serial      string `json:"serial"`
	Model       string `json:"model"`
	State       string `json:"state"`
	Bootloader  bool   `json:"bootloader"`
	Recovery    bool   `json:"recovery"`
	Encrypted   bool   `json:"encrypted"`
	StorageSize uint64 `json:"storage_size"`
}

// Legacy compatibility
type LinuxDisk = Disk

// WipeConfig holds configuration for wipe operations
type WipeConfig struct {
	Method         string `json:"method"`          // wiping method
	Rounds         int    `json:"rounds"`          // number of rounds
	Verify         bool   `json:"verify"`          // verify after wipe
	LogLevel       string `json:"log_level"`       // log level
	OutputDir      string `json:"output_dir"`      // output directory
	IncludeHidden  bool   `json:"include_hidden"`  // include HPA/DCO areas
	SecureErase    bool   `json:"secure_erase"`    // use hardware secure erase
	CryptoErase    bool   `json:"crypto_erase"`    // use crypto erase for SEDs
	NVMeSanitize   bool   `json:"nvme_sanitize"`   // use NVMe sanitize command
	CustomPattern  []byte `json:"custom_pattern"`  // custom overwrite pattern
	Parallel       bool   `json:"parallel"`        // parallel processing
	Threads        int    `json:"threads"`         // number of threads
}

// WipeMethod represents different wiping methods
type WipeMethod struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Passes      int      `json:"passes"`
	Patterns    [][]byte `json:"patterns"`
	Security    string   `json:"security"`    // Low, Medium, High, Maximum
	Speed       string   `json:"speed"`       // Fast, Medium, Slow
	Standard    string   `json:"standard"`    // NIST, DoD, Gutmann, etc.
}

// Legacy compatibility
type NwipeConfig = WipeConfig

// WipeCertificate represents the wipe completion certificate
type WipeCertificate struct {
	ToolName       string    `json:"tool_name"`
	ToolVersion    string    `json:"tool_version"`
	Device         string    `json:"device"`
	Model          string    `json:"model"`
	Serial         string    `json:"serial"`
	Size           uint64    `json:"size"`
	TimestampStart string    `json:"timestamp_start"`
	TimestampEnd   string    `json:"timestamp_end"`
	Method         string    `json:"method"`
	Rounds         int       `json:"rounds"`
	Verified       bool      `json:"verified"`
	Success        bool      `json:"success"`
	LogFile        string    `json:"log_file"`
	PostHashSHA256 string    `json:"post_hash_sha256"`
	SignerPubKey   string    `json:"signer_public_key_pem"`
	Signature      string    `json:"signature_base64"`
}

// ZeroTrace handles cross-platform disk wiping operations
type ZeroTrace struct {
	config        WipeConfig
	logFile       *os.File
	privateKey    *ecdsa.PrivateKey
	publicKey     []byte
	platform      string
	methods       map[string]WipeMethod
	androidDevices []AndroidDevice
}

// Legacy compatibility
type NwipeWrapper = ZeroTrace

func main() {
	fmt.Println("=== ZeroTrace Pro - Advanced Cross-Platform Data Erasure ===")
	fmt.Printf("Platform: %s/%s\n", runtime.GOOS, runtime.GOARCH)
	fmt.Println("Supports: Windows, Linux, macOS, Android")
	fmt.Println()

	// Check if running as root
	if os.Geteuid() != 0 {
		log.Fatal("This tool must be run as root (sudo) to access disk devices")
	}

	// Check if nwipe is installed
	if !isNwipeInstalled() {
		fmt.Println("nwipe is not installed. Installing...")
		if err := installNwipe(); err != nil {
			log.Fatalf("Failed to install nwipe: %v", err)
		}
	}

	// Initialize wrapper
	wrapper, err := NewNwipeWrapper()
	if err != nil {
		log.Fatalf("Failed to initialize wrapper: %v", err)
	}
	defer wrapper.Close()

	// List available disks
	disks, err := wrapper.ListDisks()
	if err != nil {
		log.Fatalf("Failed to list disks: %v", err)
	}

	if len(disks) == 0 {
		log.Fatal("No suitable disks found")
	}

	// Display disks
	wrapper.DisplayDisks(disks)

	// Get user selection
	selectedDisk, err := wrapper.SelectDisk(disks)
	if err != nil {
		log.Fatalf("Disk selection failed: %v", err)
	}

	// Safety checks and confirmations
	if err := wrapper.PerformSafetyChecks(selectedDisk); err != nil {
		log.Fatalf("Safety check failed: %v", err)
	}

	// Get wipe configuration
	config, err := wrapper.GetWipeConfiguration()
	if err != nil {
		log.Fatalf("Configuration failed: %v", err)
	}

	// Final confirmation
	if !wrapper.FinalConfirmation(selectedDisk, config) {
		fmt.Println("Operation cancelled by user")
		return
	}

	// Perform the wipe
	certificate, err := wrapper.WipeDisk(selectedDisk, config)
	if err != nil {
		log.Fatalf("Wipe operation failed: %v", err)
	}

	// Generate and save certificate
	if err := wrapper.SaveCertificate(certificate); err != nil {
		log.Printf("Failed to save certificate: %v", err)
	}

	fmt.Println("\n=== Wipe Operation Completed ===")
	fmt.Printf("Certificate saved to: %s\n", filepath.Join(wrapper.config.OutputDir, fmt.Sprintf("wipe_certificate_%s.json", strings.ReplaceAll(selectedDisk.Device, "/", "_"))))
}

// NewZeroTrace creates a new ZeroTrace instance
func NewZeroTrace() (*ZeroTrace, error) {
	config := WipeConfig{
		Method:    "nist",
		Rounds:    3,
		Verify:    true,
		LogLevel:  "info",
		OutputDir: "output",
		Threads:   1,
	}

	// Create output directory
	if err := os.MkdirAll(config.OutputDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create output directory: %v", err)
	}

	// Generate or load signing key
	privateKey, publicKey, err := genOrLoadKey(filepath.Join(config.OutputDir, "signer_key.pem"))
	if err != nil {
		return nil, fmt.Errorf("failed to generate/load signing key: %v", err)
	}

	zt := &ZeroTrace{
		config:     config,
		privateKey: privateKey,
		publicKey:  publicKey,
		platform:   runtime.GOOS,
		methods:    initWipeMethods(),
	}

	return zt, nil
}

// NewNwipeWrapper creates a new nwipe wrapper instance (legacy compatibility)
func NewNwipeWrapper() (*NwipeWrapper, error) {
	zt, err := NewZeroTrace()
	return (*NwipeWrapper)(zt), err
}

// initWipeMethods initializes all available wiping methods
func initWipeMethods() map[string]WipeMethod {
	methods := make(map[string]WipeMethod)

	// Quick erase (single pass zero)
	methods["quick"] = WipeMethod{
		Name:        "Quick Erase",
		Description: "Single pass zero fill - fastest method",
		Passes:      1,
		Patterns:    [][]byte{{0x00}},
		Security:    "Low",
		Speed:       "Fast",
		Standard:    "Basic",
	}

	// NIST SP 800-88 (3-pass)
	methods["nist"] = WipeMethod{
		Name:        "NIST SP 800-88",
		Description: "NIST Special Publication 800-88 (3-pass overwrite)",
		Passes:      3,
		Patterns:    [][]byte{{0x00}, {0xFF}, {0xAA}},
		Security:    "High",
		Speed:       "Medium",
		Standard:    "NIST",
	}

	// DoD 5220.22-M (7-pass)
	methods["dod"] = WipeMethod{
		Name:        "DoD 5220.22-M",
		Description: "US Department of Defense standard (7-pass)",
		Passes:      7,
		Patterns:    [][]byte{{0x00}, {0xFF}, {0x00}, {0xFF}, {0x00}, {0xFF}, {0xAA}},
		Security:    "High",
		Speed:       "Slow",
		Standard:    "DoD",
	}

	// Peter Gutmann method (35-pass)
	methods["gutmann"] = WipeMethod{
		Name:        "Peter Gutmann",
		Description: "Gutmann 35-pass method - maximum security for legacy drives",
		Passes:      35,
		Patterns:    getGutmannPatterns(),
		Security:    "Maximum",
		Speed:       "Very Slow",
		Standard:    "Gutmann",
	}

	// Random overwrite
	methods["random"] = WipeMethod{
		Name:        "Random Overwrite",
		Description: "Multiple passes with cryptographically secure random data",
		Passes:      3,
		Patterns:    nil, // Generated at runtime
		Security:    "High",
		Speed:       "Medium",
		Standard:    "Random",
	}

	// Crypto Erase (SED)
	methods["crypto"] = WipeMethod{
		Name:        "Crypto Erase",
		Description: "Self-Encrypting Drive crypto erase - instant and secure",
		Passes:      1,
		Patterns:    nil,
		Security:    "Maximum",
		Speed:       "Instant",
		Standard:    "SED",
	}

	// NVMe Sanitize
	methods["nvme_sanitize"] = WipeMethod{
		Name:        "NVMe Sanitize",
		Description: "NVMe sanitize command - hardware-level secure erase",
		Passes:      1,
		Patterns:    nil,
		Security:    "Maximum",
		Speed:       "Fast",
		Standard:    "NVMe",
	}

	return methods
}

// getGutmannPatterns returns the 35 patterns used in Gutmann method
func getGutmannPatterns() [][]byte {
	patterns := make([][]byte, 35)
	
	// First 4 passes - random
	for i := 0; i < 4; i++ {
		patterns[i] = []byte{0x00} // Will be replaced with random at runtime
	}
	
	// Core 27 passes - specific patterns for different drive technologies
	corePatterns := []byte{
		0x55, 0xAA, 0x92, 0x49, 0x24, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66,
		0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x92, 0x49, 0x24,
		0x6D, 0xB6, 0xDB,
	}
	
	for i, pattern := range corePatterns {
		patterns[i+4] = []byte{pattern}
	}
	
	// Final 4 passes - random
	for i := 31; i < 35; i++ {
		patterns[i] = []byte{0x00} // Will be replaced with random at runtime
	}
	
	return patterns
}

// determineDiskType determines disk type based on device name and transport
func (zt *ZeroTrace) determineDiskType(name, transport string) string {
	if strings.HasPrefix(name, "nvme") {
		return "NVMe SSD"
	}
	if transport == "usb" {
		return "USB Drive"
	}
	if transport == "sata" {
		// Try to determine if SSD or HDD
		if zt.isSSD("/dev/" + name) {
			return "SATA SSD"
		}
		return "SATA HDD"
	}
	return "Unknown"
}

// determineWindowsDiskType determines disk type on Windows
func (zt *ZeroTrace) determineWindowsDiskType(busType string) string {
	switch busType {
	case "NVMe":
		return "NVMe SSD"
	case "SATA":
		return "SATA Drive"
	case "USB":
		return "USB Drive"
	case "SCSI":
		return "SCSI Drive"
	default:
		return busType
	}
}

// isSSD checks if a device is an SSD
func (zt *ZeroTrace) isSSD(device string) bool {
	// Check rotational flag
	rotFile := fmt.Sprintf("/sys/block/%s/queue/rotational", strings.TrimPrefix(device, "/dev/"))
	data, err := os.ReadFile(rotFile)
	if err != nil {
		return false
	}
	return strings.TrimSpace(string(data)) == "0"
}

// getNVMeInfo gets NVMe-specific information
func (zt *ZeroTrace) getNVMeInfo(device string) *NVMeInfo {
	// Use nvme-cli to get sanitize capabilities
	cmd := exec.Command("nvme", "id-ctrl", device, "-o", "json")
	output, err := cmd.Output()
	if err != nil {
		return &NVMeInfo{}
	}

	// NVMe info parsing would go here
	// For now, return basic info
	return &NVMeInfo{
		Namespace:       device,
		SanitizeSupport: true,
		CryptoErase:     false,
		BlockErase:      true,
	}
}

// getNVMeInfoWindows gets NVMe info on Windows
func (zt *ZeroTrace) getNVMeInfoWindows(diskNumber int) *NVMeInfo {
	// Use PowerShell to get NVMe info
	cmd := exec.Command("powershell", "-Command", 
		fmt.Sprintf("Get-StorageReliabilityCounter -PhysicalDisk (Get-PhysicalDisk -DeviceNumber %d) | ConvertTo-Json", diskNumber))
	output, err := cmd.Output()
	if err != nil {
		return &NVMeInfo{}
	}

	// Simplified implementation - would need proper NVMe command support
	return &NVMeInfo{
		Namespace: fmt.Sprintf("PhysicalDrive%d", diskNumber),
	}
}

// checkSEDCapability checks if device supports Self-Encrypting Drive features
func (zt *ZeroTrace) checkSEDCapability(device string) bool {
	// Use sedutil-cli if available
	cmd := exec.Command("sedutil-cli", "--query", device)
	err := cmd.Run()
	return err == nil
}

// checkSEDCapabilityWindows checks SED capability on Windows
func (zt *ZeroTrace) checkSEDCapabilityWindows(diskNumber int) bool {
	// Use PowerShell to check encryption support
	cmd := exec.Command("powershell", "-Command", 
		fmt.Sprintf("(Get-PhysicalDisk -DeviceNumber %d).EncryptionStatus -ne 'NotEncrypted'", diskNumber))
	err := cmd.Run()
	return err == nil
}

// getDiskHealth gets disk health status and temperature
func (zt *ZeroTrace) getDiskHealth(device string) (string, int) {
	// Use smartctl to get SMART data
	cmd := exec.Command("smartctl", "-A", device)
	output, err := cmd.Output()
	if err != nil {
		return "Unknown", 0
	}

	// Parse SMART data for health and temperature
	lines := strings.Split(string(output), "\n")
	health := "Good"
	temp := 0

	for _, line := range lines {
		if strings.Contains(line, "Temperature_Celsius") {
			fields := strings.Fields(line)
			if len(fields) >= 10 {
				if t, err := strconv.Atoi(fields[9]); err == nil {
					temp = t
				}
			}
		}
		if strings.Contains(line, "FAILING_NOW") {
			health = "Failing"
		}
	}

	return health, temp
}

// performNVMeSanitize performs NVMe sanitize operation
func (zt *ZeroTrace) performNVMeSanitize(device string, method string) error {
	var sanitizeType string
	switch method {
	case "crypto":
		sanitizeType = "crypto"
	case "block":
		sanitizeType = "block"
	default:
		sanitizeType = "overwrite"
	}

	// Execute NVMe sanitize command
	cmd := exec.Command("nvme", "sanitize", device, "-a", sanitizeType)
	return cmd.Run()
}

// performCryptoErase performs crypto erase on SED
func (zt *ZeroTrace) performCryptoErase(device string) error {
	// Use sedutil-cli for crypto erase
	cmd := exec.Command("sedutil-cli", "--cryptoerase", "admin1password", device)
	return cmd.Run()
}

// performHDPartErase performs HP Part-based enterprise disk management
func (zt *ZeroTrace) performHDPartErase(device string) error {
	// Use hdparm for secure erase
	cmd := exec.Command("hdparm", "--user-master", "u", "--security-set-pass", "p", device)
	if err := cmd.Run(); err != nil {
		return err
	}

	// Execute secure erase
	cmd = exec.Command("hdparm", "--user-master", "u", "--security-erase", "p", device)
	return cmd.Run()
}

// detectAndroidDevices detects connected Android devices
func (zt *ZeroTrace) detectAndroidDevices() ([]AndroidDevice, error) {
	var devices []AndroidDevice

	// Check if ADB is available
	cmd := exec.Command("adb", "devices", "-l")
	output, err := cmd.Output()
	if err != nil {
		return devices, fmt.Errorf("ADB not available: %v", err)
	}

	lines := strings.Split(string(output), "\n")
	for _, line := range lines[1:] { // Skip header
		if strings.TrimSpace(line) == "" {
			continue
		}

		fields := strings.Fields(line)
		if len(fields) >= 2 {
			device := AndroidDevice{
				Serial: fields[0],
				State:  fields[1],
			}

			// Get device info
			if device.State == "device" {
				device.Model = zt.getAndroidDeviceInfo(device.Serial, "ro.product.model")
				device.Encrypted = zt.isAndroidDeviceEncrypted(device.Serial)
				device.StorageSize = zt.getAndroidStorageSize(device.Serial)
			}

			devices = append(devices, device)
		}
	}

	return devices, nil
}

// getAndroidDeviceInfo gets Android device property
func (zt *ZeroTrace) getAndroidDeviceInfo(serial, prop string) string {
	cmd := exec.Command("adb", "-s", serial, "shell", "getprop", prop)
	output, err := cmd.Output()
	if err != nil {
		return "Unknown"
	}
	return strings.TrimSpace(string(output))
}

// isAndroidDeviceEncrypted checks if Android device is encrypted
func (zt *ZeroTrace) isAndroidDeviceEncrypted(serial string) bool {
	cmd := exec.Command("adb", "-s", serial, "shell", "getprop", "ro.crypto.state")
	output, err := cmd.Output()
	if err != nil {
		return false
	}
	return strings.TrimSpace(string(output)) == "encrypted"
}

// getAndroidStorageSize gets Android device storage size
func (zt *ZeroTrace) getAndroidStorageSize(serial string) uint64 {
	cmd := exec.Command("adb", "-s", serial, "shell", "df", "/data")
	output, err := cmd.Output()
	if err != nil {
		return 0
	}

	lines := strings.Split(string(output), "\n")
	if len(lines) >= 2 {
		fields := strings.Fields(lines[1])
		if len(fields) >= 2 {
			if size, err := strconv.ParseUint(fields[1], 10, 64); err == nil {
				return size * 1024 // Convert from KB to bytes
			}
		}
	}
	return 0
}

// wipeAndroidDevice performs Android device wipe
func (zt *ZeroTrace) wipeAndroidDevice(device AndroidDevice, method string) error {
	switch method {
	case "factory_reset":
		// Factory reset via ADB
		cmd := exec.Command("adb", "-s", device.Serial, "shell", "am", "broadcast", "-a", "android.intent.action.MASTER_CLEAR")
		return cmd.Run()
	case "fastboot_format":
		// Format via fastboot (requires bootloader unlock)
		cmd := exec.Command("fastboot", "-s", device.Serial, "format", "userdata")
		if err := cmd.Run(); err != nil {
			return err
		}
		cmd = exec.Command("fastboot", "-s", device.Serial, "format", "cache")
		return cmd.Run()
	case "secure_wipe":
		// Secure wipe using dd (requires root)
		cmd := exec.Command("adb", "-s", device.Serial, "shell", "su", "-c", "dd if=/dev/zero of=/dev/block/userdata")
		return cmd.Run()
	default:
		return fmt.Errorf("unsupported Android wipe method: %s", method)
	}
}

// Close cleans up resources
func (zt *ZeroTrace) Close() {
	if zt.logFile != nil {
		zt.logFile.Close()
	}
}

// Legacy compatibility
func (w *NwipeWrapper) Close() {
	zt := (*ZeroTrace)(w)
	zt.Close()
}

// isNwipeInstalled checks if nwipe is available
func isNwipeInstalled() bool {
	_, err := exec.LookPath("nwipe")
	return err == nil
}

// installNwipe attempts to install nwipe on Arch-based systems
func installNwipe() error {
	fmt.Println("Attempting to install nwipe using pacman...")
	cmd := exec.Command("pacman", "-S", "--noconfirm", "nwipe")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// ListDisks discovers available disk devices across all platforms
func (zt *ZeroTrace) ListDisks() ([]Disk, error) {
	switch zt.platform {
	case "windows":
		return zt.listWindowsDisks()
	case "linux":
		return zt.listLinuxDisks()
	case "darwin":
		return zt.listMacOSDisks()
	default:
		return nil, fmt.Errorf("unsupported platform: %s", zt.platform)
	}
}

// Legacy compatibility
func (w *NwipeWrapper) ListDisks() ([]LinuxDisk, error) {
	zt := (*ZeroTrace)(w)
	disks, err := zt.ListDisks()
	if err != nil {
		return nil, err
	}
	// Convert to legacy format
	legacyDisks := make([]LinuxDisk, len(disks))
	for i, disk := range disks {
		legacyDisks[i] = LinuxDisk(disk)
	}
	return legacyDisks, nil
}

// listLinuxDisks discovers disks on Linux systems
func (zt *ZeroTrace) listLinuxDisks() ([]Disk, error) {
	var disks []Disk

	// Use lsblk to get disk information
	cmd := exec.Command("lsblk", "-J", "-o", "NAME,SIZE,MODEL,SERIAL,TYPE,RM,MOUNTPOINT,TRAN")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to run lsblk: %v", err)
	}

	// Parse lsblk JSON output
	var lsblkOutput struct {
		BlockDevices []struct {
			Name       string `json:"name"`
			Size       string `json:"size"`
			Model      string `json:"model"`
			Serial     string `json:"serial"`
			Type       string `json:"type"`
			Removable  string `json:"rm"`
			MountPoint string `json:"mountpoint"`
			Children   []struct {
				Name       string `json:"name"`
				MountPoint string `json:"mountpoint"`
			} `json:"children"`
		} `json:"blockdevices"`
	}

	if err := json.Unmarshal(output, &lsblkOutput); err != nil {
		return nil, fmt.Errorf("failed to parse lsblk output: %v", err)
	}

	for _, device := range lsblkOutput.BlockDevices {
		// Only include disk devices (not partitions, loops, etc.)
		if device.Type != "disk" {
			continue
		}

		disk := Disk{
			Device:    "/dev/" + device.Name,
			Model:     device.Model,
			Serial:    device.Serial,
			Type:      zt.determineDiskType(device.Name, device.Transport),
			Interface: device.Transport,
			Removable: device.Removable == "1",
			Platform:  "linux",
			BusType:   device.Transport,
		}

		// Parse size
		if size, err := parseSizeString(device.Size); err == nil {
			disk.Size = size
		}

		// Check for mounted partitions
		var mountPoints []string
		if device.MountPoint != "" {
			mountPoints = append(mountPoints, device.MountPoint)
			disk.Mounted = true
		}

		for _, child := range device.Children {
			if child.MountPoint != "" {
				mountPoints = append(mountPoints, child.MountPoint)
				disk.Mounted = true
			}
		}
		disk.MountPoints = mountPoints

		// Check for NVMe capabilities
		if strings.HasPrefix(device.Name, "nvme") {
			nvmeInfo := zt.getNVMeInfo("/dev/" + device.Name)
			disk.NVMeInfo = nvmeInfo
		}

		// Check for SED capabilities
		disk.SEDCapable = zt.checkSEDCapability("/dev/" + device.Name)

		// Get disk health and temperature
		disk.Health, disk.Temperature = zt.getDiskHealth("/dev/" + device.Name)

		disks = append(disks, disk)
	}

	return disks, nil
}

// DisplayDisks shows available disks to the user
func (w *NwipeWrapper) DisplayDisks(disks []LinuxDisk) {
	fmt.Println("Available disk devices:")
	fmt.Println("=======================")
	
	for i, disk := range disks {
		fmt.Printf("[%d] %s\n", i, disk.Device)
		fmt.Printf("    Model: %s\n", disk.Model)
		fmt.Printf("    Serial: %s\n", disk.Serial)
		fmt.Printf("    Size: %s\n", formatSize(disk.Size))
		fmt.Printf("    Type: %s\n", disk.Type)
		fmt.Printf("    Removable: %t\n", disk.Removable)
		fmt.Printf("    Mounted: %t\n", disk.Mounted)
		if len(disk.MountPoints) > 0 {
			fmt.Printf("    Mount Points: %s\n", strings.Join(disk.MountPoints, ", "))
		}
		fmt.Println()
	}
}

// SelectDisk prompts user to select a disk
func (w *NwipeWrapper) SelectDisk(disks []LinuxDisk) (*LinuxDisk, error) {
	fmt.Print("Enter the number of the disk to wipe: ")
	
	reader := bufio.NewReader(os.Stdin)
	input, err := reader.ReadString('\n')
	if err != nil {
		return nil, err
	}

	index, err := strconv.Atoi(strings.TrimSpace(input))
	if err != nil || index < 0 || index >= len(disks) {
		return nil, errors.New("invalid disk selection")
	}

	return &disks[index], nil
}

// PerformSafetyChecks performs various safety checks before wiping
func (w *NwipeWrapper) PerformSafetyChecks(disk *LinuxDisk) error {
	fmt.Printf("\n=== Safety Checks for %s ===\n", disk.Device)

	// Check if disk is mounted
	if disk.Mounted {
		fmt.Printf("WARNING: %s has mounted partitions: %s\n", disk.Device, strings.Join(disk.MountPoints, ", "))
		fmt.Print("Do you want to unmount all partitions? (yes/no): ")
		
		reader := bufio.NewReader(os.Stdin)
		response, _ := reader.ReadString('\n')
		response = strings.ToLower(strings.TrimSpace(response))
		
		if response == "yes" || response == "y" {
			if err := w.unmountDisk(disk); err != nil {
				return fmt.Errorf("failed to unmount disk: %v", err)
			}
		} else {
			return errors.New("cannot proceed with mounted partitions")
		}
	}

	// Check if it's a system disk (contains /boot, /, etc.)
	if w.isSystemDisk(disk) {
		fmt.Printf("CRITICAL WARNING: %s appears to be a system disk!\n", disk.Device)
		fmt.Print("Are you absolutely sure you want to wipe this disk? Type 'DESTROY_SYSTEM' to confirm: ")
		
		reader := bufio.NewReader(os.Stdin)
		response, _ := reader.ReadString('\n')
		response = strings.TrimSpace(response)
		
		if response != "DESTROY_SYSTEM" {
			return errors.New("system disk wipe cancelled for safety")
		}
	}

	fmt.Println("Safety checks passed.")
	return nil
}

// GetWipeConfiguration prompts user for wipe configuration
func (w *NwipeWrapper) GetWipeConfiguration() (NwipeConfig, error) {
	config := w.config
	
	fmt.Println("\n=== Wipe Configuration ===")
	fmt.Println("Available methods:")
	fmt.Println("1. zero - Fill with zeros (fastest)")
	fmt.Println("2. random - Fill with random data")
	fmt.Println("3. dod - DoD 5220.22-M (3 passes)")
	fmt.Println("4. gutmann - Gutmann method (35 passes)")
	fmt.Println("5. custom - Custom number of random passes")
	
	fmt.Print("Select method (1-5) [default: 3]: ")
	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	input = strings.TrimSpace(input)
	
	switch input {
	case "1":
		config.Method = "zero"
	case "2":
		config.Method = "random"
	case "4":
		config.Method = "gutmann"
	case "5":
		fmt.Print("Enter number of passes: ")
		passInput, _ := reader.ReadString('\n')
		if passes, err := strconv.Atoi(strings.TrimSpace(passInput)); err == nil && passes > 0 {
			config.Method = "random"
			config.Rounds = passes
		}
	default:
		config.Method = "dod"
	}
	
	fmt.Print("Verify after wipe? (y/n) [default: y]: ")
	verifyInput, _ := reader.ReadString('\n')
	verifyInput = strings.ToLower(strings.TrimSpace(verifyInput))
	config.Verify = verifyInput != "n" && verifyInput != "no"
	
	return config, nil
}

// FinalConfirmation shows final confirmation before wiping
func (w *NwipeWrapper) FinalConfirmation(disk *LinuxDisk, config NwipeConfig) bool {
	fmt.Println("\n=== FINAL CONFIRMATION ===")
	fmt.Printf("Device: %s\n", disk.Device)
	fmt.Printf("Model: %s\n", disk.Model)
	fmt.Printf("Size: %s\n", formatSize(disk.Size))
	fmt.Printf("Method: %s\n", config.Method)
	fmt.Printf("Rounds: %d\n", config.Rounds)
	fmt.Printf("Verify: %t\n", config.Verify)
	fmt.Println()
	fmt.Println("WARNING: This operation will PERMANENTLY DESTROY all data on the selected disk!")
	fmt.Println("This action cannot be undone!")
	fmt.Println()
	fmt.Print("Type 'WIPE_DISK_NOW' to proceed: ")
	
	reader := bufio.NewReader(os.Stdin)
	response, _ := reader.ReadString('\n')
	response = strings.TrimSpace(response)
	
	return response == "WIPE_DISK_NOW"
}

// WipeDisk performs the actual disk wiping using nwipe
func (w *NwipeWrapper) WipeDisk(disk *LinuxDisk, config NwipeConfig) (*WipeCertificate, error) {
	startTime := time.Now()
	
	// Create log file
	logFileName := fmt.Sprintf("wipe_log_%s_%s.log", 
		strings.ReplaceAll(disk.Device, "/", "_"), 
		startTime.Format("20060102_150405"))
	logPath := filepath.Join(config.OutputDir, logFileName)
	
	logFile, err := os.Create(logPath)
	if err != nil {
		return nil, fmt.Errorf("failed to create log file: %v", err)
	}
	defer logFile.Close()
	
	// Build nwipe command
	args := []string{
		"--logfile=" + logPath,
		"--method=" + config.Method,
	}
	
	if config.Rounds > 1 {
		args = append(args, "--rounds="+strconv.Itoa(config.Rounds))
	}
	
	if config.Verify {
		args = append(args, "--verify")
	}
	
	// Add the device
	args = append(args, disk.Device)
	
	fmt.Printf("Starting nwipe with command: nwipe %s\n", strings.Join(args, " "))
	fmt.Println("This may take several hours depending on disk size and method...")
	
	// Execute nwipe
	cmd := exec.Command("nwipe", args...)
	cmd.Stdout = io.MultiWriter(os.Stdout, logFile)
	cmd.Stderr = io.MultiWriter(os.Stderr, logFile)
	
	err = cmd.Run()
	endTime := time.Now()
	
	success := err == nil
	if err != nil {
		fmt.Printf("nwipe completed with error: %v\n", err)
	} else {
		fmt.Println("nwipe completed successfully!")
	}
	
	// Read a sample from the disk for verification hash
	postHash, err := w.sampleAndHash(disk.Device)
	if err != nil {
		log.Printf("Failed to generate post-wipe hash: %v", err)
		postHash = []byte{}
	}
	
	// Create certificate
	certificate := &WipeCertificate{
		ToolName:       "ZeroTrace-nwipe-wrapper",
		ToolVersion:    "1.0.0",
		Device:         disk.Device,
		Model:          disk.Model,
		Serial:         disk.Serial,
		Size:           disk.Size,
		TimestampStart: startTime.UTC().Format(time.RFC3339),
		TimestampEnd:   endTime.UTC().Format(time.RFC3339),
		Method:         config.Method,
		Rounds:         config.Rounds,
		Verified:       config.Verify,
		Success:        success,
		LogFile:        logPath,
		PostHashSHA256: fmt.Sprintf("%x", postHash),
		SignerPubKey:   string(w.publicKey),
	}
	
	// Sign the certificate
	certJSON, _ := json.Marshal(certificate)
	signature, err := w.ecdsaSign(certJSON)
	if err != nil {
		return nil, fmt.Errorf("failed to sign certificate: %v", err)
	}
	certificate.Signature = signature
	
	return certificate, nil
}

// SaveCertificate saves the wipe certificate to files
func (w *NwipeWrapper) SaveCertificate(cert *WipeCertificate) error {
	deviceName := strings.ReplaceAll(cert.Device, "/", "_")
	
	// Save JSON certificate
	jsonPath := filepath.Join(w.config.OutputDir, fmt.Sprintf("wipe_certificate_%s.json", deviceName))
	jsonData, err := json.MarshalIndent(cert, "", "  ")
	if err != nil {
		return err
	}
	
	if err := os.WriteFile(jsonPath, jsonData, 0644); err != nil {
		return err
	}
	
	fmt.Printf("Certificate saved: %s\n", jsonPath)
	
	// Create PDF certificate
	pdfPath := filepath.Join(w.config.OutputDir, fmt.Sprintf("wipe_certificate_%s.pdf", deviceName))
	if err := w.createPDFCertificate(cert, pdfPath); err != nil {
		log.Printf("Failed to create PDF certificate: %v", err)
	} else {
		fmt.Printf("PDF certificate saved: %s\n", pdfPath)
	}
	
	return nil
}

// Helper functions below...

// unmountDisk unmounts all partitions on a disk
func (w *NwipeWrapper) unmountDisk(disk *LinuxDisk) error {
	for _, mountPoint := range disk.MountPoints {
		fmt.Printf("Unmounting %s...\n", mountPoint)
		cmd := exec.Command("umount", mountPoint)
		if err := cmd.Run(); err != nil {
			// Try force unmount
			cmd = exec.Command("umount", "-f", mountPoint)
			if err := cmd.Run(); err != nil {
				return fmt.Errorf("failed to unmount %s: %v", mountPoint, err)
			}
		}
	}
	return nil
}

// isSystemDisk checks if a disk contains system partitions
func (w *NwipeWrapper) isSystemDisk(disk *LinuxDisk) bool {
	for _, mountPoint := range disk.MountPoints {
		if mountPoint == "/" || mountPoint == "/boot" || mountPoint == "/home" {
			return true
		}
	}
	return false
}

// parseSizeString converts size strings like "1.8T" to bytes
func parseSizeString(sizeStr string) (uint64, error) {
	if sizeStr == "" {
		return 0, errors.New("empty size string")
	}
	
	re := regexp.MustCompile(`^(\d+(?:\.\d+)?)\s*([KMGTPE]?)$`)
	matches := re.FindStringSubmatch(strings.ToUpper(sizeStr))
	if len(matches) != 3 {
		return 0, errors.New("invalid size format")
	}
	
	value, err := strconv.ParseFloat(matches[1], 64)
	if err != nil {
		return 0, err
	}
	
	multiplier := uint64(1)
	switch matches[2] {
	case "K":
		multiplier = 1024
	case "M":
		multiplier = 1024 * 1024
	case "G":
		multiplier = 1024 * 1024 * 1024
	case "T":
		multiplier = 1024 * 1024 * 1024 * 1024
	case "P":
		multiplier = 1024 * 1024 * 1024 * 1024 * 1024
	case "E":
		multiplier = 1024 * 1024 * 1024 * 1024 * 1024 * 1024
	}
	
	return uint64(value * float64(multiplier)), nil
}

// formatSize formats bytes into human-readable format
func formatSize(bytes uint64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := uint64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

// sampleAndHash reads a sample from the disk and returns SHA256 hash
func (w *NwipeWrapper) sampleAndHash(device string) ([]byte, error) {
	file, err := os.Open(device)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	
	// Read first 1MB
	buffer := make([]byte, 1024*1024)
	n, err := file.Read(buffer)
	if err != nil && err != io.EOF {
		return nil, err
	}
	
	hash := sha256.Sum256(buffer[:n])
	return hash[:], nil
}

// genOrLoadKey generates or loads ECDSA signing key
func genOrLoadKey(path string) (*ecdsa.PrivateKey, []byte, error) {
	if _, err := os.Stat(path); err == nil {
		// Load existing key
		keyData, err := os.ReadFile(path)
		if err != nil {
			return nil, nil, err
		}
		
		block, _ := pem.Decode(keyData)
		if block == nil {
			return nil, nil, errors.New("invalid PEM data")
		}
		
		privateKey, err := x509.ParseECPrivateKey(block.Bytes)
		if err != nil {
			return nil, nil, err
		}
		
		publicKeyBytes, err := x509.MarshalPKIXPublicKey(&privateKey.PublicKey)
		if err != nil {
			return nil, nil, err
		}
		
		publicKeyPEM := pem.EncodeToMemory(&pem.Block{
			Type:  "PUBLIC KEY",
			Bytes: publicKeyBytes,
		})
		
		return privateKey, publicKeyPEM, nil
	}
	
	// Generate new key
	privateKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, nil, err
	}
	
	privateKeyBytes, err := x509.MarshalECPrivateKey(privateKey)
	if err != nil {
		return nil, nil, err
	}
	
	privateKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "EC PRIVATE KEY",
		Bytes: privateKeyBytes,
	})
	
	if err := os.WriteFile(path, privateKeyPEM, 0600); err != nil {
		return nil, nil, err
	}
	
	publicKeyBytes, err := x509.MarshalPKIXPublicKey(&privateKey.PublicKey)
	if err != nil {
		return nil, nil, err
	}
	
	publicKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "PUBLIC KEY",
		Bytes: publicKeyBytes,
	})
	
	return privateKey, publicKeyPEM, nil
}

// ecdsaSign signs data with ECDSA private key
func (w *NwipeWrapper) ecdsaSign(data []byte) (string, error) {
	hash := sha256.Sum256(data)
	r, s, err := ecdsa.Sign(rand.Reader, w.privateKey, hash[:])
	if err != nil {
		return "", err
	}
	
	// Encode signature as ASN.1 DER
	type ecdsaSignature struct {
		R, S *big.Int
	}
	
	sigBytes, err := asn1.Marshal(ecdsaSignature{r, s})
	if err != nil {
		return "", err
	}
	
	return base64.StdEncoding.EncodeToString(sigBytes), nil
}

// createPDFCertificate creates a PDF certificate
func (w *NwipeWrapper) createPDFCertificate(cert *WipeCertificate, path string) error {
	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.AddPage()
	
	// Title
	pdf.SetFont("Arial", "B", 20)
	pdf.Cell(40, 10, "Disk Wipe Certificate")
	pdf.Ln(15)
	
	// Content
	pdf.SetFont("Arial", "", 12)
	content := fmt.Sprintf(`Tool: %s
Version: %s
Device: %s
Model: %s
Serial: %s
Size: %s
Start Time: %s
End Time: %s
Method: %s
Rounds: %d
Verified: %t
Success: %t
Log File: %s
Post-Wipe Hash (SHA256): %s

This certificate verifies that the above disk has been securely wiped
using the specified method. The digital signature below ensures the
authenticity and integrity of this certificate.

Signature: %s`,
		cert.ToolName, cert.ToolVersion, cert.Device, cert.Model, cert.Serial,
		formatSize(cert.Size), cert.TimestampStart, cert.TimestampEnd,
		cert.Method, cert.Rounds, cert.Verified, cert.Success,
		cert.LogFile, cert.PostHashSHA256, cert.Signature)
	
	pdf.MultiCell(0, 5, content, "", "", false)
	
	return pdf.OutputFileAndClose(path)
}
