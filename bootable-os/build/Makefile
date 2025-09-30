# ZeroTrace Pro Bootable OS Makefile
# Builds a complete bootable ISO based on Tiny Core Linux

# Configuration
ZEROTRACE_VERSION := 1.0
TCL_VERSION := 15.0
BUILD_DIR := build-output
ISO_NAME := zerotrace-pro-$(ZEROTRACE_VERSION).iso
WORK_DIR := $(BUILD_DIR)/work

# Directories
SRC_DIR := ..
BOOTABLE_DIR := $(SRC_DIR)/bootable-os
CONFIG_DIR := $(BOOTABLE_DIR)/config
SCRIPTS_DIR := $(BOOTABLE_DIR)/scripts
ZEROTRACE_DIR := $(BOOTABLE_DIR)/zerotrace

# Tools
MKSQUASHFS := mksquashfs
GENISOIMAGE := genisoimage
ISOHYBRID := isohybrid

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Default target
.PHONY: all
all: iso

# Help target
.PHONY: help
help:
	@echo "ZeroTrace Pro Bootable OS Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Build complete ISO (default)"
	@echo "  iso          - Build bootable ISO"
	@echo "  extensions   - Build ZeroTrace extensions only"
	@echo "  clean        - Clean build directory"
	@echo "  test-vm      - Test ISO in QEMU"
	@echo "  usb          - Create USB installer"
	@echo "  help         - Show this help"
	@echo ""
	@echo "Configuration:"
	@echo "  ZEROTRACE_VERSION = $(ZEROTRACE_VERSION)"
	@echo "  TCL_VERSION = $(TCL_VERSION)"
	@echo "  BUILD_DIR = $(BUILD_DIR)"

# Check dependencies
.PHONY: check-deps
check-deps:
	@echo -e "$(GREEN)Checking dependencies...$(NC)"
	@command -v $(MKSQUASHFS) >/dev/null || (echo -e "$(RED)Error: squashfs-tools not found$(NC)" && exit 1)
	@command -v $(GENISOIMAGE) >/dev/null || (echo -e "$(RED)Error: genisoimage not found$(NC)" && exit 1)
	@command -v python3 >/dev/null || (echo -e "$(RED)Error: python3 not found$(NC)" && exit 1)
	@command -v go >/dev/null || (echo -e "$(RED)Error: go not found$(NC)" && exit 1)
	@echo -e "$(GREEN)All dependencies satisfied$(NC)"

# Create build directories
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)
	@mkdir -p $(WORK_DIR)

# Download Tiny Core Linux
$(WORK_DIR)/tinycore.iso: | $(BUILD_DIR)
	@echo -e "$(GREEN)Downloading Tiny Core Linux $(TCL_VERSION)...$(NC)"
	@wget -O $@ "http://tinycorelinux.net/$(TCL_VERSION)/x86_64/release/TinyCorePure64-$(TCL_VERSION).iso"

# Extract TCL ISO
$(WORK_DIR)/tcl-extract: $(WORK_DIR)/tinycore.iso
	@echo -e "$(GREEN)Extracting Tiny Core Linux...$(NC)"
	@mkdir -p $@
	@sudo mkdir -p /mnt/tcl-iso
	@sudo mount -o loop $< /mnt/tcl-iso
	@sudo cp -r /mnt/tcl-iso/* $@/
	@sudo umount /mnt/tcl-iso
	@sudo rmdir /mnt/tcl-iso
	@sudo chown -R $(USER):$(USER) $@

# Build Go backend
$(WORK_DIR)/zerotrace-backend: $(SRC_DIR)/nwipe_main.go
	@echo -e "$(GREEN)Building Go backend...$(NC)"
	@cd $(SRC_DIR) && go build -o $(abspath $@) nwipe_main.go

# Build ZeroTrace extensions
.PHONY: extensions
extensions: $(WORK_DIR)/extensions/zerotrace-gui.tcz

$(WORK_DIR)/extensions/zerotrace-gui.tcz: $(WORK_DIR)/zerotrace-backend | $(BUILD_DIR)
	@echo -e "$(GREEN)Building ZeroTrace extensions...$(NC)"
	@mkdir -p $(WORK_DIR)/extensions
	@mkdir -p $(WORK_DIR)/ext-build
	
	# Build Python extension
	@$(MAKE) -s build-python-ext
	
	# Build Go backend extension
	@$(MAKE) -s build-go-ext
	
	# Build ZeroTrace GUI extension
	@$(MAKE) -s build-gui-ext

# Build Python extension
.PHONY: build-python-ext
build-python-ext:
	@echo -e "$(GREEN)Building Python extension...$(NC)"
	@mkdir -p $(WORK_DIR)/python-ext/usr/local
	@cp -r /usr/lib/python3* $(WORK_DIR)/python-ext/usr/local/ 2>/dev/null || true
	@cd $(WORK_DIR)/python-ext && $(MKSQUASHFS) usr $(WORK_DIR)/extensions/python3-zerotrace.tcz -comp xz
	@echo "tk.tcz" > $(WORK_DIR)/extensions/python3-zerotrace.tcz.dep

# Build Go backend extension
.PHONY: build-go-ext
build-go-ext:
	@echo -e "$(GREEN)Building Go backend extension...$(NC)"
	@mkdir -p $(WORK_DIR)/go-ext/usr/local/bin
	@cp $(WORK_DIR)/zerotrace-backend $(WORK_DIR)/go-ext/usr/local/bin/
	@cd $(WORK_DIR)/go-ext && $(MKSQUASHFS) usr $(WORK_DIR)/extensions/zerotrace-backend.tcz -comp xz

# Build GUI extension
.PHONY: build-gui-ext
build-gui-ext:
	@echo -e "$(GREEN)Building GUI extension...$(NC)"
	@mkdir -p $(WORK_DIR)/gui-ext/usr/local/share/zerotrace
	@mkdir -p $(WORK_DIR)/gui-ext/usr/local/bin
	@mkdir -p $(WORK_DIR)/gui-ext/etc/init.d
	
	# Copy ZeroTrace files
	@cp $(SRC_DIR)/gui.py $(WORK_DIR)/gui-ext/usr/local/share/zerotrace/
	@cp $(SRC_DIR)/backend_interface.py $(WORK_DIR)/gui-ext/usr/local/share/zerotrace/
	@cp $(SRC_DIR)/gui_integration.py $(WORK_DIR)/gui-ext/usr/local/share/zerotrace/
	@cp $(ZEROTRACE_DIR)/gui_linux.py $(WORK_DIR)/gui-ext/usr/local/share/zerotrace/
	
	# Copy startup script
	@cp $(CONFIG_DIR)/zerotrace-autostart.sh $(WORK_DIR)/gui-ext/etc/init.d/zerotrace
	@chmod +x $(WORK_DIR)/gui-ext/etc/init.d/zerotrace
	
	# Create launcher
	@echo '#!/bin/sh' > $(WORK_DIR)/gui-ext/usr/local/bin/zerotrace
	@echo 'cd /usr/local/share/zerotrace' >> $(WORK_DIR)/gui-ext/usr/local/bin/zerotrace
	@echo 'python3 gui_linux.py' >> $(WORK_DIR)/gui-ext/usr/local/bin/zerotrace
	@chmod +x $(WORK_DIR)/gui-ext/usr/local/bin/zerotrace
	
	# Create extension
	@cd $(WORK_DIR)/gui-ext && $(MKSQUASHFS) . $(WORK_DIR)/extensions/zerotrace-gui.tcz -comp xz
	@echo -e "python3-zerotrace.tcz\nzerotrace-backend.tcz" > $(WORK_DIR)/extensions/zerotrace-gui.tcz.dep

# Create custom initramfs
$(WORK_DIR)/core-zerotrace.gz: $(WORK_DIR)/tcl-extract extensions
	@echo -e "$(GREEN)Creating custom initramfs...$(NC)"
	@mkdir -p $(WORK_DIR)/initramfs
	@cd $(WORK_DIR)/initramfs && zcat $(WORK_DIR)/tcl-extract/boot/core.gz | cpio -idmv
	
	# Add ZeroTrace to startup
	@echo '/etc/init.d/zerotrace' >> $(WORK_DIR)/initramfs/opt/bootlocal.sh
	
	# Repack initramfs
	@cd $(WORK_DIR)/initramfs && find . | cpio -o -H newc | gzip > $(WORK_DIR)/core-zerotrace.gz

# Create bootable ISO
.PHONY: iso
iso: $(BUILD_DIR)/$(ISO_NAME)

$(BUILD_DIR)/$(ISO_NAME): $(WORK_DIR)/core-zerotrace.gz $(WORK_DIR)/tcl-extract extensions
	@echo -e "$(GREEN)Creating bootable ISO...$(NC)"
	@mkdir -p $(WORK_DIR)/iso
	
	# Copy TCL structure
	@cp -r $(WORK_DIR)/tcl-extract/* $(WORK_DIR)/iso/
	
	# Replace initramfs
	@cp $(WORK_DIR)/core-zerotrace.gz $(WORK_DIR)/iso/boot/core.gz
	
	# Copy extensions
	@cp $(WORK_DIR)/extensions/*.tcz $(WORK_DIR)/iso/cde/ 2>/dev/null || true
	
	# Update boot config
	@echo 'DEFAULT zerotrace' > $(WORK_DIR)/iso/boot/isolinux/isolinux.cfg
	@echo 'LABEL zerotrace' >> $(WORK_DIR)/iso/boot/isolinux/isolinux.cfg
	@echo '    KERNEL /boot/vmlinuz64' >> $(WORK_DIR)/iso/boot/isolinux/isolinux.cfg
	@echo '    APPEND initrd=/boot/core.gz quiet tce=UUID="" opt=UUID="" home=UUID="" restore=UUID=""' >> $(WORK_DIR)/iso/boot/isolinux/isolinux.cfg
	@echo 'TIMEOUT 30' >> $(WORK_DIR)/iso/boot/isolinux/isolinux.cfg
	
	# Create ISO
	@$(GENISOIMAGE) -l -J -R -V "ZeroTrace Pro" \
		-no-emul-boot -boot-load-size 4 -boot-info-table \
		-b boot/isolinux/isolinux.bin \
		-c boot/isolinux/boot.cat \
		-o $@ $(WORK_DIR)/iso
	
	# Make hybrid (USB bootable)
	@$(ISOHYBRID) $@
	
	@echo -e "$(GREEN)ISO created: $@$(NC)"
	@echo -e "$(GREEN)Size: $(shell du -h $@ | cut -f1)$(NC)"

# Test in QEMU
.PHONY: test-vm
test-vm: $(BUILD_DIR)/$(ISO_NAME)
	@echo -e "$(GREEN)Testing ISO in QEMU...$(NC)"
	@qemu-system-x86_64 -cdrom $< -m 1024 -enable-kvm 2>/dev/null || \
	 qemu-system-x86_64 -cdrom $< -m 1024

# Create USB installer
.PHONY: usb
usb: $(BUILD_DIR)/$(ISO_NAME)
	@echo -e "$(YELLOW)To create USB installer:$(NC)"
	@echo "1. Insert USB drive"
	@echo "2. Find device: lsblk"
	@echo "3. Write ISO: sudo dd if=$< of=/dev/sdX bs=4M status=progress"
	@echo -e "$(RED)WARNING: This will erase all data on the USB drive!$(NC)"

# Clean build directory
.PHONY: clean
clean:
	@echo -e "$(GREEN)Cleaning build directory...$(NC)"
	@rm -rf $(BUILD_DIR)

# Show build info
.PHONY: info
info:
	@echo "ZeroTrace Pro Bootable OS Build Information"
	@echo "=========================================="
	@echo "Version: $(ZEROTRACE_VERSION)"
	@echo "TCL Version: $(TCL_VERSION)"
	@echo "Build Directory: $(BUILD_DIR)"
	@echo "ISO Name: $(ISO_NAME)"
	@echo ""
	@echo "Source Files:"
	@echo "  GUI: $(SRC_DIR)/gui.py"
	@echo "  Backend: $(SRC_DIR)/nwipe_main.go"
	@echo "  Integration: $(SRC_DIR)/gui_integration.py"
	@echo ""
	@echo "Build Status:"
	@if [ -f "$(BUILD_DIR)/$(ISO_NAME)" ]; then \
		echo "  ISO: ✅ Built ($(shell du -h $(BUILD_DIR)/$(ISO_NAME) | cut -f1))"; \
	else \
		echo "  ISO: ❌ Not built"; \
	fi
