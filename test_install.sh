#!/bin/bash

# ZeroTrace Installation Test Script
# This script tests the installation and basic functionality

set -e

echo "=== ZeroTrace Installation Test ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK")
            echo -e "${GREEN}[OK]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        "INFO")
            echo -e "[INFO] $message"
            ;;
    esac
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_status "WARN" "Running as root - this is required for disk operations"
        return 0
    else
        print_status "INFO" "Not running as root - some tests will be skipped"
        return 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "INFO" "Checking system requirements..."
    
    # Check Go installation
    if command -v go &> /dev/null; then
        GO_VERSION=$(go version | awk '{print $3}')
        print_status "OK" "Go is installed: $GO_VERSION"
    else
        print_status "ERROR" "Go is not installed"
        return 1
    fi
    
    # Check required system tools
    local tools=("lsblk" "udevadm" "blockdev" "mount" "umount")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            print_status "OK" "$tool is available"
        else
            print_status "ERROR" "$tool is not available"
            return 1
        fi
    done
    
    # Check nwipe (optional, will be installed automatically)
    if command -v nwipe &> /dev/null; then
        NWIPE_VERSION=$(nwipe --version 2>&1 | head -n1 || echo "unknown")
        print_status "OK" "nwipe is installed: $NWIPE_VERSION"
    else
        print_status "WARN" "nwipe is not installed (will be installed automatically)"
    fi
    
    return 0
}

# Test Go module
test_go_module() {
    print_status "INFO" "Testing Go module..."
    
    if [[ -f "go.mod" ]]; then
        print_status "OK" "go.mod found"
    else
        print_status "ERROR" "go.mod not found"
        return 1
    fi
    
    # Test module dependencies
    if go mod tidy; then
        print_status "OK" "Go dependencies resolved"
    else
        print_status "ERROR" "Failed to resolve Go dependencies"
        return 1
    fi
    
    return 0
}

# Test build process
test_build() {
    print_status "INFO" "Testing build process..."
    
    if make build; then
        print_status "OK" "Build successful"
    else
        print_status "ERROR" "Build failed"
        return 1
    fi
    
    # Check if binary was created
    if [[ -f "build/zerotrace" ]]; then
        print_status "OK" "Binary created: build/zerotrace"
    else
        print_status "ERROR" "Binary not found"
        return 1
    fi
    
    return 0
}

# Test configuration
test_configuration() {
    print_status "INFO" "Testing configuration..."
    
    if [[ -f "config/zerotrace.json" ]]; then
        print_status "OK" "Configuration file found"
        
        # Test JSON validity
        if python3 -m json.tool config/zerotrace.json > /dev/null 2>&1; then
            print_status "OK" "Configuration file is valid JSON"
        else
            print_status "ERROR" "Configuration file is invalid JSON"
            return 1
        fi
    else
        print_status "WARN" "Configuration file not found (will be created automatically)"
    fi
    
    return 0
}

# Test disk listing (requires root)
test_disk_listing() {
    if ! check_root; then
        print_status "INFO" "Skipping disk listing test (requires root)"
        return 0
    fi
    
    print_status "INFO" "Testing disk listing..."
    
    # Test lsblk JSON output
    if lsblk -J -o NAME,SIZE,MODEL,SERIAL,TYPE,RM,MOUNTPOINT > /dev/null 2>&1; then
        print_status "OK" "lsblk JSON output works"
    else
        print_status "ERROR" "lsblk JSON output failed"
        return 1
    fi
    
    return 0
}

# Test output directory creation
test_output_directory() {
    print_status "INFO" "Testing output directory creation..."
    
    if mkdir -p output; then
        print_status "OK" "Output directory created"
    else
        print_status "ERROR" "Failed to create output directory"
        return 1
    fi
    
    return 0
}

# Test certificate generation (basic)
test_certificate_generation() {
    print_status "INFO" "Testing certificate generation..."
    
    # This would require running the actual binary with mock data
    # For now, just check if the crypto libraries are available
    if go list crypto/ecdsa crypto/x509 > /dev/null 2>&1; then
        print_status "OK" "Cryptographic libraries available"
    else
        print_status "ERROR" "Cryptographic libraries not available"
        return 1
    fi
    
    return 0
}

# Main test execution
main() {
    local failed_tests=0
    
    echo "Starting ZeroTrace installation tests..."
    echo
    
    # Run all tests
    check_requirements || ((failed_tests++))
    test_go_module || ((failed_tests++))
    test_build || ((failed_tests++))
    test_configuration || ((failed_tests++))
    test_disk_listing || ((failed_tests++))
    test_output_directory || ((failed_tests++))
    test_certificate_generation || ((failed_tests++))
    
    echo
    echo "=== Test Summary ==="
    
    if [[ $failed_tests -eq 0 ]]; then
        print_status "OK" "All tests passed! ZeroTrace is ready to use."
        echo
        echo "To run ZeroTrace:"
        echo "  sudo ./build/zerotrace"
        echo
        echo "Or install system-wide:"
        echo "  make install"
        echo "  sudo zerotrace"
        exit 0
    else
        print_status "ERROR" "$failed_tests test(s) failed. Please fix the issues above."
        exit 1
    fi
}

# Run main function
main "$@"
