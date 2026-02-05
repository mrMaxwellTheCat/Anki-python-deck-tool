#!/usr/bin/env bash
# Bash script to install anki-yaml-tool system-wide on Linux/macOS
# This script copies the built executable to ~/.local/bin and ensures it's in PATH

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Define installation directory
INSTALL_DIR="$HOME/.local/bin"
EXE_NAME="anki-yaml-tool"

# Get the project root directory (parent of scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
EXE_PATH="$DIST_DIR/$EXE_NAME"

echo "==================================="
echo "Anki YAML Tool System-Wide Installer"
echo "==================================="
echo ""

# Check if executable exists
if [ ! -f "$EXE_PATH" ]; then
    echo -e "${RED}Error: Executable not found at: $EXE_PATH${NC}"
    echo -e "${YELLOW}Please build the executable first using: make build-exe${NC}"
    echo -e "${YELLOW}Or run the VS Code task: 'Build Executable (Local)'${NC}"
    exit 1
fi

echo -e "${GREEN}Found executable: $EXE_PATH${NC}"

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

# Copy executable to installation directory
echo "Copying executable to: $INSTALL_DIR"
cp -f "$EXE_PATH" "$INSTALL_DIR/$EXE_NAME"
chmod +x "$INSTALL_DIR/$EXE_NAME"

echo ""

# Check if directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}Adding installation directory to PATH...${NC}"
    echo ""

    # Detect shell and add to appropriate config file
    SHELL_CONFIG=""
    if [ -n "$BASH_VERSION" ]; then
        if [ -f "$HOME/.bashrc" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            SHELL_CONFIG="$HOME/.bash_profile"
        fi
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -f "$HOME/.profile" ]; then
        SHELL_CONFIG="$HOME/.profile"
    fi

    if [ -n "$SHELL_CONFIG" ]; then
        # Check if the PATH export already exists in the config file
        if ! grep -q "export PATH=\"\$HOME/.local/bin:\$PATH\"" "$SHELL_CONFIG"; then
            echo "" >> "$SHELL_CONFIG"
            echo "# Added by anki-yaml-tool installer" >> "$SHELL_CONFIG"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_CONFIG"
            echo -e "${GREEN}Added to PATH in: $SHELL_CONFIG${NC}"
            echo ""
            echo -e "${CYAN}IMPORTANT: Run the following command to reload your shell configuration:${NC}"
            echo -e "${CYAN}  source $SHELL_CONFIG${NC}"
            echo ""
            echo -e "${CYAN}Or open a new terminal window.${NC}"
        else
            echo -e "${GREEN}PATH export already exists in $SHELL_CONFIG${NC}"
        fi
    else
        echo -e "${YELLOW}Could not detect shell configuration file.${NC}"
        echo -e "${YELLOW}Please manually add the following to your shell configuration:${NC}"
        echo -e "${CYAN}  export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi
else
    echo -e "${GREEN}Installation directory is already in PATH.${NC}"
fi

echo ""
echo "==================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "==================================="
echo ""
echo "Executable location: $INSTALL_DIR/$EXE_NAME"
echo ""
echo "To test, run:"
echo -e "${CYAN}  anki-yaml-tool --help${NC}"
echo ""
