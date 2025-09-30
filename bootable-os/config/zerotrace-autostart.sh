#!/bin/sh
# ZeroTrace Pro Auto-start Script for Tiny Core Linux
# This script automatically starts ZeroTrace Pro on boot

# Configuration
ZEROTRACE_USER="tc"
DISPLAY_NUM=":0"
LOG_FILE="/tmp/zerotrace-startup.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Wait for system to be ready
wait_for_system() {
    log "Waiting for system to be ready..."
    
    # Wait for filesystem
    while [ ! -d "/tmp" ]; do
        sleep 1
    done
    
    # Wait for basic commands
    while ! command -v python3 >/dev/null 2>&1; do
        log "Waiting for Python3..."
        sleep 2
    done
    
    log "System ready"
}

# Load ZeroTrace extensions
load_extensions() {
    log "Loading ZeroTrace extensions..."
    
    # Load in correct order (dependencies first)
    tce-load -i python3-zerotrace.tcz || error_exit "Failed to load Python extension"
    tce-load -i zerotrace-backend.tcz || error_exit "Failed to load backend extension"
    tce-load -i zerotrace-gui.tcz || error_exit "Failed to load GUI extension"
    
    log "Extensions loaded successfully"
}

# Setup X11 environment
setup_x11() {
    log "Setting up X11 environment..."
    
    # Start X server if not running
    if ! pgrep Xorg >/dev/null; then
        log "Starting X server..."
        startx &
        
        # Wait for X to start
        local count=0
        while [ $count -lt 30 ]; do
            if xdpyinfo -display $DISPLAY_NUM >/dev/null 2>&1; then
                log "X server started successfully"
                break
            fi
            sleep 1
            count=$((count + 1))
        done
        
        if [ $count -eq 30 ]; then
            error_exit "X server failed to start"
        fi
    else
        log "X server already running"
    fi
}

# Configure hardware access
setup_hardware() {
    log "Configuring hardware access..."
    
    # Add user to necessary groups
    adduser $ZEROTRACE_USER disk 2>/dev/null || true
    adduser $ZEROTRACE_USER storage 2>/dev/null || true
    
    # Set permissions for disk access
    chmod 666 /dev/sd* 2>/dev/null || true
    chmod 666 /dev/nvme* 2>/dev/null || true
    
    # Load necessary kernel modules
    modprobe sg 2>/dev/null || true
    modprobe sd_mod 2>/dev/null || true
    
    log "Hardware access configured"
}

# Start ZeroTrace GUI
start_zerotrace() {
    log "Starting ZeroTrace Pro GUI..."
    
    # Set environment variables
    export DISPLAY=$DISPLAY_NUM
    export PYTHONPATH="/usr/local/share/zerotrace:$PYTHONPATH"
    
    # Change to ZeroTrace directory
    cd /usr/local/share/zerotrace || error_exit "ZeroTrace directory not found"
    
    # Start ZeroTrace as the tc user
    su $ZEROTRACE_USER -c "
        export DISPLAY=$DISPLAY_NUM
        export PYTHONPATH=/usr/local/share/zerotrace:\$PYTHONPATH
        cd /usr/local/share/zerotrace
        python3 gui_integration.py 2>&1 | tee -a $LOG_FILE
    " &
    
    local zerotrace_pid=$!
    log "ZeroTrace started with PID: $zerotrace_pid"
    
    # Monitor the process
    while kill -0 $zerotrace_pid 2>/dev/null; do
        sleep 10
    done
    
    log "ZeroTrace process ended"
}

# Cleanup on exit
cleanup() {
    log "Performing cleanup..."
    
    # Kill any remaining ZeroTrace processes
    pkill -f "python3.*gui" 2>/dev/null || true
    pkill -f "zerotrace" 2>/dev/null || true
    
    # Clear sensitive data from memory (security measure)
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    
    log "Cleanup completed"
}

# Signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    log "=== ZeroTrace Pro Auto-start ==="
    log "Starting ZeroTrace Pro bootable environment..."
    
    wait_for_system
    load_extensions
    setup_hardware
    setup_x11
    start_zerotrace
    
    log "ZeroTrace Pro session ended"
}

# Run main function
main "$@"
