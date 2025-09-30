# ZeroTrace Makefile

# Variables
BINARY_NAME=zerotrace
MAIN_FILES=nwipe_main.go config.go utils.go
BUILD_DIR=build
OUTPUT_DIR=output
CONFIG_DIR=config

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
GOGET=$(GOCMD) get
GOMOD=$(GOCMD) mod

# Build flags
LDFLAGS=-ldflags "-X main.Version=1.0.0 -X main.BuildTime=$(shell date -u '+%Y-%m-%d_%H:%M:%S')"

.PHONY: all build clean test deps install uninstall help

# Default target
all: deps build

# Build the binary
build:
	@echo "Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME) $(MAIN_FILES)
	@echo "Build complete: $(BUILD_DIR)/$(BINARY_NAME)"

# Build for production (optimized)
build-prod:
	@echo "Building $(BINARY_NAME) for production..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(LDFLAGS) -a -installsuffix cgo -o $(BUILD_DIR)/$(BINARY_NAME) $(MAIN_FILES)
	@echo "Production build complete: $(BUILD_DIR)/$(BINARY_NAME)"

# Install dependencies
deps:
	@echo "Installing dependencies..."
	$(GOMOD) tidy
	$(GOMOD) download

# Clean build artifacts
clean:
	@echo "Cleaning..."
	$(GOCLEAN)
	@rm -rf $(BUILD_DIR)
	@rm -rf $(OUTPUT_DIR)
	@echo "Clean complete"

# Run tests
test:
	@echo "Running tests..."
	$(GOTEST) -v ./...

# Install the binary system-wide
install: build
	@echo "Installing $(BINARY_NAME) to /usr/local/bin..."
	@sudo cp $(BUILD_DIR)/$(BINARY_NAME) /usr/local/bin/
	@sudo chmod +x /usr/local/bin/$(BINARY_NAME)
	@echo "Installation complete"

# Uninstall the binary
uninstall:
	@echo "Uninstalling $(BINARY_NAME)..."
	@sudo rm -f /usr/local/bin/$(BINARY_NAME)
	@echo "Uninstall complete"

# Create directories
dirs:
	@mkdir -p $(BUILD_DIR)
	@mkdir -p $(OUTPUT_DIR)
	@mkdir -p $(CONFIG_DIR)

# Format code
fmt:
	@echo "Formatting code..."
	@go fmt ./...

# Lint code
lint:
	@echo "Linting code..."
	@golangci-lint run

# Check for security issues
security:
	@echo "Running security checks..."
	@gosec ./...

# Create release package
package: build-prod
	@echo "Creating release package..."
	@mkdir -p release
	@cp $(BUILD_DIR)/$(BINARY_NAME) release/
	@cp README.md release/
	@cp LICENSE release/ 2>/dev/null || echo "LICENSE file not found, skipping..."
	@tar -czf release/$(BINARY_NAME)-v1.0.0-linux-amd64.tar.gz -C release $(BINARY_NAME) README.md
	@echo "Release package created: release/$(BINARY_NAME)-v1.0.0-linux-amd64.tar.gz"

# Development build with debug info
dev: 
	@echo "Building development version..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) -gcflags="all=-N -l" -o $(BUILD_DIR)/$(BINARY_NAME)-dev $(MAIN_FILES)
	@echo "Development build complete: $(BUILD_DIR)/$(BINARY_NAME)-dev"

# Run the application (requires sudo)
run: build
	@echo "Running $(BINARY_NAME) (requires sudo)..."
	@sudo $(BUILD_DIR)/$(BINARY_NAME)

# Check system requirements
check-deps:
	@echo "Checking system dependencies..."
	@command -v go >/dev/null 2>&1 || { echo "Go is not installed"; exit 1; }
	@command -v nwipe >/dev/null 2>&1 || echo "nwipe not found - will be installed automatically"
	@command -v lsblk >/dev/null 2>&1 || { echo "lsblk is required but not found"; exit 1; }
	@command -v udevadm >/dev/null 2>&1 || { echo "udevadm is required but not found"; exit 1; }
	@echo "System dependencies check complete"

# Show help
help:
	@echo "ZeroTrace Build System"
	@echo "====================="
	@echo ""
	@echo "Available targets:"
	@echo "  all          - Install dependencies and build (default)"
	@echo "  build        - Build the binary"
	@echo "  build-prod   - Build optimized production binary"
	@echo "  deps         - Install Go dependencies"
	@echo "  clean        - Clean build artifacts"
	@echo "  test         - Run tests"
	@echo "  install      - Install binary system-wide (requires sudo)"
	@echo "  uninstall    - Remove installed binary (requires sudo)"
	@echo "  fmt          - Format Go code"
	@echo "  lint         - Lint Go code (requires golangci-lint)"
	@echo "  security     - Run security checks (requires gosec)"
	@echo "  package      - Create release package"
	@echo "  dev          - Build development version with debug info"
	@echo "  run          - Build and run (requires sudo)"
	@echo "  check-deps   - Check system dependencies"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make build          # Build the binary"
	@echo "  make install        # Install system-wide"
	@echo "  sudo make run       # Build and run"
	@echo "  make package        # Create release package"
