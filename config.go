package main

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// Config represents the application configuration
type Config struct {
	// Wipe settings
	DefaultMethod    string `json:"default_method"`
	DefaultRounds    int    `json:"default_rounds"`
	DefaultVerify    bool   `json:"default_verify"`
	
	// Safety settings
	RequireRootConfirmation bool `json:"require_root_confirmation"`
	AllowSystemDiskWipe     bool `json:"allow_system_disk_wipe"`
	AutoUnmount             bool `json:"auto_unmount"`
	
	// Output settings
	OutputDirectory string `json:"output_directory"`
	LogLevel        string `json:"log_level"`
	CreatePDF       bool   `json:"create_pdf"`
	
	// Security settings
	SignCertificates bool   `json:"sign_certificates"`
	KeyPath          string `json:"key_path"`
	
	// Nwipe settings
	NwipeLogLevel string `json:"nwipe_log_level"`
	NwipeTimeout  int    `json:"nwipe_timeout_hours"`
}

// DefaultConfig returns the default configuration
func DefaultConfig() *Config {
	return &Config{
		DefaultMethod:           "dod",
		DefaultRounds:           1,
		DefaultVerify:           true,
		RequireRootConfirmation: true,
		AllowSystemDiskWipe:     false,
		AutoUnmount:             false,
		OutputDirectory:         "output",
		LogLevel:                "info",
		CreatePDF:               true,
		SignCertificates:        true,
		KeyPath:                 "output/signer_key.pem",
		NwipeLogLevel:           "info",
		NwipeTimeout:            24,
	}
}

// LoadConfig loads configuration from file or creates default
func LoadConfig(configPath string) (*Config, error) {
	// If config file doesn't exist, create default
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		config := DefaultConfig()
		if err := config.Save(configPath); err != nil {
			return nil, err
		}
		return config, nil
	}
	
	// Load existing config
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}
	
	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, err
	}
	
	return &config, nil
}

// Save saves the configuration to file
func (c *Config) Save(configPath string) error {
	// Create directory if it doesn't exist
	dir := filepath.Dir(configPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	
	data, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(configPath, data, 0644)
}

// Validate validates the configuration
func (c *Config) Validate() error {
	// Validate method
	validMethods := map[string]bool{
		"zero":     true,
		"random":   true,
		"dod":      true,
		"gutmann":  true,
		"custom":   true,
	}
	
	if !validMethods[c.DefaultMethod] {
		c.DefaultMethod = "dod"
	}
	
	// Validate rounds
	if c.DefaultRounds < 1 {
		c.DefaultRounds = 1
	}
	
	// Validate timeout
	if c.NwipeTimeout < 1 {
		c.NwipeTimeout = 24
	}
	
	// Ensure output directory exists
	if err := os.MkdirAll(c.OutputDirectory, 0755); err != nil {
		return err
	}
	
	return nil
}
