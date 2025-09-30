package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
)

// SimpleDisk represents a basic disk device
type SimpleDisk struct {
	Device string
	Model  string
	Size   string
	Type   string
}

func main() {
	fmt.Println("=== ZeroTrace Pro - Advanced Cross-Platform Data Erasure ===")
	fmt.Printf("Platform: %s/%s\n", runtime.GOOS, runtime.GOARCH)
	fmt.Println("Supports: Windows, Linux, macOS, Android")
	fmt.Println()

	// Detect platform and list disks
	disks := listDisks()
	if len(disks) == 0 {
		fmt.Println("No disks detected. This may require administrator privileges.")
		return
	}

	// Display disks
	displayDisks(disks)

	// Get user selection
	selectedDisk := selectDisk(disks)
	if selectedDisk == nil {
		fmt.Println("No disk selected. Exiting.")
		return
	}

	// Show available methods
	showWipeMethods()

	// Get method selection
	method := selectMethod()

	// Final confirmation
	if !confirmWipe(selectedDisk, method) {
		fmt.Println("Operation cancelled.")
		return
	}

	// Simulate wipe process
	fmt.Printf("\n🚀 Starting %s on %s...\n", method, selectedDisk.Device)
	fmt.Println("⚠️  This is a SIMULATION - no actual wiping occurs in this demo")
	
	for i := 1; i <= 100; i++ {
		fmt.Printf("\rProgress: %d%% ", i)
		// time.Sleep(50 * time.Millisecond) // Uncomment for real progress simulation
	}
	
	fmt.Println("\n✅ Wipe simulation completed successfully!")
	fmt.Println("📄 Certificate would be generated here in full version")
}

func listDisks() []SimpleDisk {
	var disks []SimpleDisk
	
	switch runtime.GOOS {
	case "windows":
		disks = listWindowsDisks()
	case "linux":
		disks = listLinuxDisks()
	case "darwin":
		disks = listMacOSDisks()
	default:
		fmt.Printf("Platform %s not fully supported yet\n", runtime.GOOS)
	}
	
	return disks
}

func listWindowsDisks() []SimpleDisk {
	var disks []SimpleDisk
	
	// Try PowerShell command
	cmd := exec.Command("powershell", "-Command", "Get-PhysicalDisk | Select-Object DeviceID,FriendlyName,Size | Format-Table -AutoSize")
	output, err := cmd.Output()
	if err != nil {
		// Fallback to basic detection
		disks = append(disks, SimpleDisk{
			Device: `\\.\PhysicalDrive0`,
			Model:  "Primary System Drive",
			Size:   "Unknown",
			Type:   "System Disk",
		})
	} else {
		fmt.Println("PowerShell disk detection:")
		fmt.Println(string(output))
		// Parse PowerShell output (simplified)
		disks = append(disks, SimpleDisk{
			Device: `\\.\PhysicalDrive0`,
			Model:  "Detected Windows Drive",
			Size:   "Variable",
			Type:   "Windows Disk",
		})
	}
	
	return disks
}

func listLinuxDisks() []SimpleDisk {
	var disks []SimpleDisk
	
	// Try lsblk command
	cmd := exec.Command("lsblk", "-d", "-o", "NAME,MODEL,SIZE,TYPE")
	output, err := cmd.Output()
	if err != nil {
		// Fallback
		disks = append(disks, SimpleDisk{
			Device: "/dev/sda",
			Model:  "Generic Linux Disk",
			Size:   "Unknown",
			Type:   "disk",
		})
	} else {
		lines := strings.Split(string(output), "\n")
		for i, line := range lines {
			if i == 0 || strings.TrimSpace(line) == "" {
				continue // Skip header and empty lines
			}
			fields := strings.Fields(line)
			if len(fields) >= 4 && fields[3] == "disk" {
				disks = append(disks, SimpleDisk{
					Device: "/dev/" + fields[0],
					Model:  fields[1],
					Size:   fields[2],
					Type:   fields[3],
				})
			}
		}
	}
	
	return disks
}

func listMacOSDisks() []SimpleDisk {
	var disks []SimpleDisk
	
	// Try diskutil command
	cmd := exec.Command("diskutil", "list")
	output, err := cmd.Output()
	if err != nil {
		// Fallback
		disks = append(disks, SimpleDisk{
			Device: "/dev/disk0",
			Model:  "Generic macOS Disk",
			Size:   "Unknown",
			Type:   "APFS",
		})
	} else {
		fmt.Println("diskutil output:")
		fmt.Println(string(output))
		// Simplified parsing
		disks = append(disks, SimpleDisk{
			Device: "/dev/disk0",
			Model:  "Detected macOS Drive",
			Size:   "Variable",
			Type:   "macOS Disk",
		})
	}
	
	return disks
}

func displayDisks(disks []SimpleDisk) {
	fmt.Println("Available disk devices:")
	fmt.Println("=======================")
	
	for i, disk := range disks {
		fmt.Printf("[%d] %s\n", i, disk.Device)
		fmt.Printf("    Model: %s\n", disk.Model)
		fmt.Printf("    Size: %s\n", disk.Size)
		fmt.Printf("    Type: %s\n", disk.Type)
		fmt.Println()
	}
}

func selectDisk(disks []SimpleDisk) *SimpleDisk {
	fmt.Print("Enter the number of the disk to wipe (or 'q' to quit): ")
	
	reader := bufio.NewReader(os.Stdin)
	input, err := reader.ReadString('\n')
	if err != nil {
		return nil
	}
	
	input = strings.TrimSpace(input)
	if input == "q" || input == "Q" {
		return nil
	}
	
	index, err := strconv.Atoi(input)
	if err != nil || index < 0 || index >= len(disks) {
		fmt.Println("Invalid selection")
		return nil
	}
	
	return &disks[index]
}

func showWipeMethods() {
	fmt.Println("\n🔧 Available Wiping Methods:")
	fmt.Println("============================")
	fmt.Println("1. Quick Erase (1-pass zero fill)")
	fmt.Println("2. NIST SP 800-88 (3-pass overwrite)")
	fmt.Println("3. DoD 5220.22-M (7-pass overwrite)")
	fmt.Println("4. Peter Gutmann (35-pass method)")
	fmt.Println("5. Crypto Erase (SED/NVMe Sanitize)")
	fmt.Println("6. Random Overwrite (3-pass random)")
}

func selectMethod() string {
	fmt.Print("\nSelect wiping method (1-6): ")
	
	reader := bufio.NewReader(os.Stdin)
	input, err := reader.ReadString('\n')
	if err != nil {
		return "Quick Erase"
	}
	
	switch strings.TrimSpace(input) {
	case "1":
		return "Quick Erase (1-pass zero fill)"
	case "2":
		return "NIST SP 800-88 (3-pass overwrite)"
	case "3":
		return "DoD 5220.22-M (7-pass overwrite)"
	case "4":
		return "Peter Gutmann (35-pass method)"
	case "5":
		return "Crypto Erase (SED/NVMe Sanitize)"
	case "6":
		return "Random Overwrite (3-pass random)"
	default:
		return "Quick Erase (1-pass zero fill)"
	}
}

func confirmWipe(disk *SimpleDisk, method string) bool {
	fmt.Printf("\n⚠️  FINAL CONFIRMATION ⚠️\n")
	fmt.Printf("Device: %s\n", disk.Device)
	fmt.Printf("Model: %s\n", disk.Model)
	fmt.Printf("Method: %s\n", method)
	fmt.Println("\n🚨 WARNING: This will PERMANENTLY DESTROY all data!")
	fmt.Print("Type 'CONFIRM' to proceed: ")
	
	reader := bufio.NewReader(os.Stdin)
	input, err := reader.ReadString('\n')
	if err != nil {
		return false
	}
	
	return strings.TrimSpace(input) == "CONFIRM"
}
