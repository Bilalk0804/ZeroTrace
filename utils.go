package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"syscall"
)

// Logger provides structured logging
type Logger struct {
	level string
}

// NewLogger creates a new logger
func NewLogger(level string) *Logger {
	return &Logger{level: level}
}

// Info logs info messages
func (l *Logger) Info(msg string) {
	fmt.Printf("[INFO] %s\n", msg)
}

// Warn logs warning messages
func (l *Logger) Warn(msg string) {
	fmt.Printf("[WARN] %s\n", msg)
}

// Error logs error messages
func (l *Logger) Error(msg string) {
	fmt.Printf("[ERROR] %s\n", msg)
}

// Fatal logs fatal messages and exits
func (l *Logger) Fatal(msg string) {
	fmt.Printf("[FATAL] %s\n", msg)
	os.Exit(1)
}

// PromptUser prompts user for input with a message
func PromptUser(message string) string {
	fmt.Print(message)
	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	return strings.TrimSpace(input)
}

// PromptConfirm prompts user for yes/no confirmation
func PromptConfirm(message string) bool {
	response := strings.ToLower(PromptUser(message + " (y/n): "))
	return response == "y" || response == "yes"
}

// CheckRoot verifies the program is running as root
func CheckRoot() bool {
	return os.Geteuid() == 0
}

// CheckCommand checks if a command exists in PATH
func CheckCommand(command string) bool {
	_, err := exec.LookPath(command)
	return err == nil
}

// RunCommand executes a command and returns output
func RunCommand(name string, args ...string) (string, error) {
	cmd := exec.Command(name, args...)
	output, err := cmd.Output()
	return string(output), err
}

// RunCommandInteractive runs a command with interactive output
func RunCommandInteractive(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}

// GetProcessStatus checks if a process is running
func GetProcessStatus(pid int) bool {
	process, err := os.FindProcess(pid)
	if err != nil {
		return false
	}
	
	err = process.Signal(syscall.Signal(0))
	return err == nil
}

// CreateProgressBar creates a simple progress bar
func CreateProgressBar(current, total int, width int) string {
	if total == 0 {
		return "[" + strings.Repeat(" ", width) + "] 0%"
	}
	
	percentage := float64(current) / float64(total)
	filled := int(percentage * float64(width))
	
	bar := "["
	bar += strings.Repeat("=", filled)
	bar += strings.Repeat(" ", width-filled)
	bar += fmt.Sprintf("] %.1f%%", percentage*100)
	
	return bar
}

// ValidateDevice checks if a device path is valid
func ValidateDevice(device string) error {
	if !strings.HasPrefix(device, "/dev/") {
		return fmt.Errorf("invalid device path: %s", device)
	}
	
	if _, err := os.Stat(device); os.IsNotExist(err) {
		return fmt.Errorf("device does not exist: %s", device)
	}
	
	return nil
}

// GetDeviceInfo retrieves basic device information
func GetDeviceInfo(device string) (map[string]string, error) {
	info := make(map[string]string)
	
	// Get device size using blockdev
	if output, err := RunCommand("blockdev", "--getsize64", device); err == nil {
		info["size"] = strings.TrimSpace(output)
	}
	
	// Get device model using udevadm
	if output, err := RunCommand("udevadm", "info", "--query=property", "--name="+device); err == nil {
		lines := strings.Split(output, "\n")
		for _, line := range lines {
			if strings.HasPrefix(line, "ID_MODEL=") {
				info["model"] = strings.TrimPrefix(line, "ID_MODEL=")
			}
			if strings.HasPrefix(line, "ID_SERIAL_SHORT=") {
				info["serial"] = strings.TrimPrefix(line, "ID_SERIAL_SHORT=")
			}
		}
	}
	
	return info, nil
}

// IsBlockDevice checks if a path is a block device
func IsBlockDevice(path string) bool {
	stat, err := os.Stat(path)
	if err != nil {
		return false
	}
	
	return stat.Mode()&os.ModeDevice != 0 && stat.Mode()&os.ModeCharDevice == 0
}

// GetMountedPartitions returns mounted partitions for a device
func GetMountedPartitions(device string) ([]string, error) {
	var partitions []string
	
	output, err := RunCommand("mount")
	if err != nil {
		return partitions, err
	}
	
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		if strings.Contains(line, device) {
			parts := strings.Fields(line)
			if len(parts) >= 3 {
				partitions = append(partitions, parts[2]) // mount point
			}
		}
	}
	
	return partitions, nil
}

// UnmountDevice unmounts all partitions on a device
func UnmountDevice(device string) error {
	partitions, err := GetMountedPartitions(device)
	if err != nil {
		return err
	}
	
	for _, partition := range partitions {
		fmt.Printf("Unmounting %s...\n", partition)
		if err := RunCommandInteractive("umount", partition); err != nil {
			// Try force unmount
			if err := RunCommandInteractive("umount", "-f", partition); err != nil {
				return fmt.Errorf("failed to unmount %s: %v", partition, err)
			}
		}
	}
	
	return nil
}

// BackupMBR creates a backup of the Master Boot Record
func BackupMBR(device, backupPath string) error {
	fmt.Printf("Creating MBR backup: %s\n", backupPath)
	return RunCommandInteractive("dd", "if="+device, "of="+backupPath, "bs=512", "count=1")
}

// SecureDelete securely deletes a file
func SecureDelete(filePath string) error {
	if CheckCommand("shred") {
		return RunCommandInteractive("shred", "-vfz", "-n", "3", filePath)
	} else if CheckCommand("rm") {
		return RunCommandInteractive("rm", "-f", filePath)
	}
	return os.Remove(filePath)
}

// GetSystemInfo returns basic system information
func GetSystemInfo() map[string]string {
	info := make(map[string]string)
	
	// Get OS info
	if output, err := RunCommand("uname", "-a"); err == nil {
		info["uname"] = strings.TrimSpace(output)
	}
	
	// Get distribution info
	if output, err := RunCommand("lsb_release", "-d"); err == nil {
		info["distribution"] = strings.TrimSpace(output)
	} else if data, err := os.ReadFile("/etc/os-release"); err == nil {
		lines := strings.Split(string(data), "\n")
		for _, line := range lines {
			if strings.HasPrefix(line, "PRETTY_NAME=") {
				info["distribution"] = strings.Trim(strings.TrimPrefix(line, "PRETTY_NAME="), "\"")
				break
			}
		}
	}
	
	// Get uptime
	if output, err := RunCommand("uptime"); err == nil {
		info["uptime"] = strings.TrimSpace(output)
	}
	
	return info
}
