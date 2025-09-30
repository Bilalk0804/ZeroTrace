#!/bin/bash
# ZeroTrace Pro Bootable OS Builder
# Creates a custom Tiny Core Linux ISO with ZeroTrace Pro

set -e

# Configuration
ZEROTRACE_VERSION="1.0"
TCL_VERSION="15.x"
BUILD_DIR="$(pwd)/build-output"
ISO_NAME="zerotrace-pro-${ZEROTRACE_VERSION}.iso"
WORK_DIR="${BUILD_DIR}/work"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check dependencies
check_dependencies() {
    log "Checking build dependencies..."
    
    local deps=("squashfs-tools" "genisoimage" "syslinux" "wget" "git" "python3" "go")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing dependencies: ${missing[*]}"
    fi
    
    log "All dependencies satisfied"
}

# Download Tiny Core Linux
download_tcl() {
    log "Downloading Tiny Core Linux ${TCL_VERSION}..."
    
    local tcl_url="http://tinycorelinux.net/15.x/x86_64/release/TinyCorePure64-15.0.iso"
    local tcl_iso="${WORK_DIR}/tinycore.iso"
    
    mkdir -p "${WORK_DIR}"
    
    if [[ ! -f "$tcl_iso" ]]; then
        wget -O "$tcl_iso" "$tcl_url" || error "Failed to download Tiny Core Linux"
    fi
    
    log "Tiny Core Linux downloaded"
}

# Extract TCL ISO
extract_tcl() {
    log "Extracting Tiny Core Linux..."
    
    local tcl_iso="${WORK_DIR}/tinycore.iso"
    local extract_dir="${WORK_DIR}/tcl-extract"
    
    mkdir -p "$extract_dir"
    
    # Mount and copy ISO contents
    sudo mkdir -p /mnt/tcl-iso
    sudo mount -o loop "$tcl_iso" /mnt/tcl-iso
    sudo cp -r /mnt/tcl-iso/* "$extract_dir/"
    sudo umount /mnt/tcl-iso
    sudo rmdir /mnt/tcl-iso
    
    # Fix permissions
    sudo chown -R $(whoami):$(whoami) "$extract_dir"
    
    log "Tiny Core Linux extracted"
}

# Build ZeroTrace extensions
build_zerotrace_extensions() {
    log "Building ZeroTrace extensions..."
    
    local ext_dir="${WORK_DIR}/extensions"
    mkdir -p "$ext_dir"
    
    # Create Python extension with ZeroTrace
    create_python_extension "$ext_dir"
    
    # Create Go backend extension
    create_go_extension "$ext_dir"
    
    # Create ZeroTrace GUI extension
    create_zerotrace_extension "$ext_dir"
    
    log "ZeroTrace extensions built"
}

# Create Python extension
create_python_extension() {
    local ext_dir="$1"
    local python_dir="${WORK_DIR}/python-build"
    
    log "Creating Python extension..."
    
    mkdir -p "$python_dir"
    
    # Download and build Python with Tkinter
    cd "$python_dir"
    
    # Create extension structure
    mkdir -p usr/local/bin usr/local/lib
    
    # Copy system Python (simplified approach)
    cp -r /usr/bin/python3* usr/local/bin/ 2>/dev/null || true
    cp -r /usr/lib/python3* usr/local/lib/ 2>/dev/null || true
    
    # Create TCZ package
    mksquashfs usr "${ext_dir}/python3-zerotrace.tcz" -comp xz
    
    # Create dependency file
    echo "tk.tcz" > "${ext_dir}/python3-zerotrace.tcz.dep"
    
    cd - > /dev/null
}

# Create Go backend extension
create_go_extension() {
    local ext_dir="$1"
    local go_dir="${WORK_DIR}/go-build"
    
    log "Creating Go backend extension..."
    
    mkdir -p "$go_dir/usr/local/bin"
    
    # Build Go backend
    cd "$(dirname "$0")/../../"
    go build -o "${go_dir}/usr/local/bin/zerotrace-backend" nwipe_main.go
    
    # Create TCZ package
    cd "$go_dir"
    mksquashfs usr "${ext_dir}/zerotrace-backend.tcz" -comp xz
    
    cd - > /dev/null
}

# Create ZeroTrace GUI extension
create_zerotrace_extension() {
    local ext_dir="$1"
    local zt_dir="${WORK_DIR}/zerotrace-build"
    
    log "Creating ZeroTrace GUI extension..."
    
    mkdir -p "$zt_dir/usr/local/share/zerotrace"
    mkdir -p "$zt_dir/usr/local/bin"
    
    # Copy ZeroTrace files
    cp "$(dirname "$0")/../../gui.py" "$zt_dir/usr/local/share/zerotrace/"
    cp "$(dirname "$0")/../../backend_interface.py" "$zt_dir/usr/local/share/zerotrace/"
    cp "$(dirname "$0")/../../gui_integration.py" "$zt_dir/usr/local/share/zerotrace/"
    
    # Create launcher script
    cat > "$zt_dir/usr/local/bin/zerotrace" << 'EOF'
#!/bin/sh
cd /usr/local/share/zerotrace
python3 gui_integration.py
EOF
    chmod +x "$zt_dir/usr/local/bin/zerotrace"
    
    # Create TCZ package
    cd "$zt_dir"
    mksquashfs usr "${ext_dir}/zerotrace-gui.tcz" -comp xz
    
    # Create dependency file
    echo -e "python3-zerotrace.tcz\nzerotrace-backend.tcz" > "${ext_dir}/zerotrace-gui.tcz.dep"
    
    cd - > /dev/null
}

# Create custom initramfs
create_initramfs() {
    log "Creating custom initramfs..."
    
    local initramfs_dir="${WORK_DIR}/initramfs"
    local tcl_extract="${WORK_DIR}/tcl-extract"
    
    mkdir -p "$initramfs_dir"
    
    # Extract original initramfs
    cd "$initramfs_dir"
    zcat "${tcl_extract}/boot/core.gz" | cpio -idmv
    
    # Add ZeroTrace startup script
    cat > etc/init.d/zerotrace << 'EOF'
#!/bin/sh
# ZeroTrace Pro startup script

# Load extensions
tce-load -i python3-zerotrace
tce-load -i zerotrace-backend
tce-load -i zerotrace-gui

# Start X server
startx /usr/local/bin/zerotrace &

# Wait for X to start
sleep 5

# Auto-login and start ZeroTrace
su tc -c "DISPLAY=:0 /usr/local/bin/zerotrace" &
EOF
    chmod +x etc/init.d/zerotrace
    
    # Add to startup
    echo "/etc/init.d/zerotrace" >> etc/init.d/rcS
    
    # Repack initramfs
    find . | cpio -o -H newc | gzip > "${WORK_DIR}/core-zerotrace.gz"
    
    cd - > /dev/null
}

# Create bootable ISO
create_iso() {
    log "Creating bootable ISO..."
    
    local iso_dir="${WORK_DIR}/iso"
    local tcl_extract="${WORK_DIR}/tcl-extract"
    
    mkdir -p "$iso_dir"
    
    # Copy TCL ISO structure
    cp -r "$tcl_extract"/* "$iso_dir/"
    
    # Replace initramfs
    cp "${WORK_DIR}/core-zerotrace.gz" "$iso_dir/boot/core.gz"
    
    # Copy extensions
    cp "${WORK_DIR}/extensions"/*.tcz "$iso_dir/cde/"
    
    # Update boot configuration
    cat > "$iso_dir/boot/isolinux/isolinux.cfg" << EOF
DEFAULT zerotrace
LABEL zerotrace
    KERNEL /boot/vmlinuz64
    APPEND initrd=/boot/core.gz quiet tce=sda1 opt=sda1 home=sda1 restore=sda1
TIMEOUT 30
EOF
    
    # Create ISO
    genisoimage -l -J -R -V "ZeroTrace Pro" \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -b boot/isolinux/isolinux.bin \
        -c boot/isolinux/boot.cat \
        -o "${BUILD_DIR}/${ISO_NAME}" \
        "$iso_dir"
    
    log "ISO created: ${BUILD_DIR}/${ISO_NAME}"
}

# Make ISO hybrid (USB bootable)
make_hybrid() {
    log "Making ISO hybrid (USB bootable)..."
    
    isohybrid "${BUILD_DIR}/${ISO_NAME}"
    
    log "ISO is now USB bootable"
}

# Cleanup
cleanup() {
    log "Cleaning up temporary files..."
    
    # Remove work directory (optional)
    # rm -rf "$WORK_DIR"
    
    log "Build complete!"
    log "ISO file: ${BUILD_DIR}/${ISO_NAME}"
    log "Size: $(du -h "${BUILD_DIR}/${ISO_NAME}" | cut -f1)"
}

# Main build process
main() {
    log "Starting ZeroTrace Pro Bootable OS build..."
    
    check_root
    check_dependencies
    download_tcl
    extract_tcl
    build_zerotrace_extensions
    create_initramfs
    create_iso
    make_hybrid
    cleanup
    
    log "Build completed successfully!"
    log "You can now boot from: ${BUILD_DIR}/${ISO_NAME}"
}

# Run main function
main "$@"
