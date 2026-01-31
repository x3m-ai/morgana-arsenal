#!/bin/bash
#
# Morgana Arsenal - Update Script
# ================================
# This script updates ONLY Morgana Arsenal code.
# It does NOT touch: Nginx, SSL certificates, MISP, or system packages.
#
# Usage:
#   curl -sL https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-update/update-morgana.sh | sudo bash
#   # Or locally:
#   sudo ./update-morgana.sh
#
# Version History:
# ----------------
#   1.5.0.0 (2026-01-31) - Agent timeout, Skip Link, super-reliable agent
#   1.3.0.0 (2026-01-29) - Initial release
#
# Copyright (c) 2026 x3m-ai / Morgana Arsenal
# License: Apache 2.0
#

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_VERSION="1.5.0.0"
MORGANA_VERSION="1.5.0.0"
PREVIOUS_VERSION="1.3.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Paths
MORGANA_DIR="/home/morgana/morgana-arsenal"
BACKUP_DIR="/home/morgana/morgana-backup-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="/tmp/morgana-update-$(date +%Y%m%d-%H%M%S).log"

# =============================================================================
# CHANGELOG
# =============================================================================

CHANGELOG="
=============================================================================
 CHANGELOG: ${PREVIOUS_VERSION} -> ${MORGANA_VERSION}
=============================================================================

[NEW FEATURES]
  - Agent timeout parameter: -timeout (default 30 seconds)
  - Agent log file named after executable (e.g., Merlino-PC01.log)
  - Skip Link button in Operations view (bypasses stuck commands)
  - Agent process tree killing with taskkill /F /T

[IMPROVEMENTS]
  - Agent super-reliable: never crashes, try-catch everywhere
  - Merlino deploy command includes all parameters (-group, -sleep, -timeout)
  - Dynamic log file path (no more hardcoded paths)

[BUG FIXES]
  - Fixed agent blocking indefinitely on stuck commands (reg save, etc.)
  - Fixed 502 Bad Gateway on EC2 (hardcoded log path)
  - Fixed operation state calculation

[TECHNICAL]
  - Agent compiled with timeout mechanism
  - KillProcessTree using taskkill /F /T /PID
  - Skip Link sets status to -2 (discarded)
"

# =============================================================================
# FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log_step() {
    echo -e "\n${BOLD}${BLUE}>>> $1${NC}"
    echo "[STEP] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

print_banner() {
    echo -e "${CYAN}"
    echo "  __  __                                      "
    echo " |  \/  | ___  _ __ __ _  __ _ _ __   __ _    "
    echo " | |\/| |/ _ \| '__/ _\` |/ _\` | '_ \ / _\` |   "
    echo " | |  | | (_) | | | (_| | (_| | | | | (_| |   "
    echo " |_|  |_|\___/|_|  \__, |\__,_|_| |_|\__,_|   "
    echo "                   |___/                      "
    echo "           Arsenal Update Script              "
    echo -e "${NC}"
    echo -e "${BOLD}Version: ${SCRIPT_VERSION}${NC}"
    echo -e "${BOLD}Updating to: ${MORGANA_VERSION}${NC}"
    echo ""
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

detect_user() {
    if [ -d "/home/morgana/morgana-arsenal" ]; then
        INSTALL_USER="morgana"
    elif [ -d "/home/ubuntu/morgana-arsenal" ]; then
        INSTALL_USER="ubuntu"
        MORGANA_DIR="/home/ubuntu/morgana-arsenal"
        BACKUP_DIR="/home/ubuntu/morgana-backup-$(date +%Y%m%d-%H%M%S)"
    else
        log_error "Morgana Arsenal not found in /home/morgana or /home/ubuntu"
        exit 1
    fi
    log_info "Detected user: ${INSTALL_USER}"
    log_info "Morgana directory: ${MORGANA_DIR}"
}

check_morgana_exists() {
    if [ ! -d "$MORGANA_DIR" ]; then
        log_error "Morgana Arsenal not found at $MORGANA_DIR"
        log_error "Please run the full installation script first."
        exit 1
    fi
    
    if [ ! -f "$MORGANA_DIR/server.py" ]; then
        log_error "Invalid Morgana Arsenal installation (server.py not found)"
        exit 1
    fi
}

backup_config() {
    log_step "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup important files
    if [ -f "$MORGANA_DIR/conf/local.yml" ]; then
        cp "$MORGANA_DIR/conf/local.yml" "$BACKUP_DIR/"
        log_info "Backed up: conf/local.yml"
    fi
    
    if [ -f "$MORGANA_DIR/conf/default.yml" ]; then
        cp "$MORGANA_DIR/conf/default.yml" "$BACKUP_DIR/"
        log_info "Backed up: conf/default.yml"
    fi
    
    # Backup data directory (agents, operations, etc.)
    if [ -d "$MORGANA_DIR/data" ]; then
        cp -r "$MORGANA_DIR/data" "$BACKUP_DIR/"
        log_info "Backed up: data/ directory"
    fi
    
    log_info "Backup created at: $BACKUP_DIR"
}

stop_service() {
    log_step "Stopping Morgana Arsenal service..."
    
    if systemctl is-active --quiet morgana-arsenal 2>/dev/null; then
        systemctl stop morgana-arsenal
        log_info "Service stopped"
    else
        log_warn "Service was not running"
    fi
    
    # Kill any remaining processes
    pkill -f "python3.*server.py" 2>/dev/null || true
    sleep 2
}

update_code() {
    log_step "Updating Morgana Arsenal code..."
    
    cd "$MORGANA_DIR"
    
    # Check if it's a git repository
    if [ -d ".git" ]; then
        log_info "Pulling latest code from GitHub..."
        
        # Stash any local changes
        sudo -u "$INSTALL_USER" git stash 2>/dev/null || true
        
        # Pull latest
        sudo -u "$INSTALL_USER" git fetch origin
        sudo -u "$INSTALL_USER" git reset --hard origin/main
        
        log_info "Code updated from GitHub"
    else
        log_error "Not a git repository. Please clone Morgana Arsenal properly."
        exit 1
    fi
}

restore_config() {
    log_step "Restoring configuration..."
    
    # Restore local.yml if it existed
    if [ -f "$BACKUP_DIR/local.yml" ]; then
        cp "$BACKUP_DIR/local.yml" "$MORGANA_DIR/conf/"
        log_info "Restored: conf/local.yml"
    fi
    
    # Restore data directory
    if [ -d "$BACKUP_DIR/data" ]; then
        # Only restore object_store (keeps agents, operations)
        if [ -f "$BACKUP_DIR/data/object_store" ]; then
            cp "$BACKUP_DIR/data/object_store" "$MORGANA_DIR/data/"
            log_info "Restored: data/object_store (agents, operations)"
        fi
    fi
}

update_python_deps() {
    log_step "Updating Python dependencies..."
    
    cd "$MORGANA_DIR"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        pip install -r requirements.txt --quiet --upgrade
        deactivate
        log_info "Python dependencies updated"
    else
        log_warn "Virtual environment not found, creating..."
        sudo -u "$INSTALL_USER" python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt --quiet
        deactivate
        log_info "Virtual environment created and dependencies installed"
    fi
}

build_frontend() {
    log_step "Building frontend (Magma plugin)..."
    
    cd "$MORGANA_DIR/plugins/magma"
    
    if [ ! -d "node_modules" ]; then
        log_info "Installing npm dependencies..."
        sudo -u "$INSTALL_USER" npm install --silent 2>/dev/null
    fi
    
    log_info "Building Vue 3 frontend..."
    sudo -u "$INSTALL_USER" npm run build --silent 2>/dev/null
    
    log_info "Frontend built successfully"
}

compile_merlino() {
    log_step "Compiling Merlino agent..."
    
    cd "$MORGANA_DIR"
    
    if command -v mcs &> /dev/null; then
        mcs -out:data/payloads/Merlino.exe \
            -target:winexe \
            -platform:x64 \
            -optimize+ \
            agent-sharp/Agent.cs 2>/dev/null
        
        if [ -f "data/payloads/Merlino.exe" ]; then
            local size=$(stat -c%s "data/payloads/Merlino.exe" 2>/dev/null || echo "unknown")
            log_info "Merlino.exe compiled successfully (${size} bytes)"
        else
            log_warn "Merlino.exe compilation may have failed"
        fi
    else
        log_warn "mono-mcs not installed, skipping Merlino compilation"
        log_warn "Install with: sudo apt install mono-mcs"
    fi
}

fix_permissions() {
    log_step "Fixing file permissions..."
    
    chown -R "$INSTALL_USER:$INSTALL_USER" "$MORGANA_DIR"
    chmod +x "$MORGANA_DIR/server.py"
    chmod +x "$MORGANA_DIR"/*.sh 2>/dev/null || true
    
    log_info "Permissions fixed"
}

start_service() {
    log_step "Starting Morgana Arsenal service..."
    
    if systemctl is-enabled --quiet morgana-arsenal 2>/dev/null; then
        systemctl start morgana-arsenal
        sleep 3
        
        if systemctl is-active --quiet morgana-arsenal; then
            log_info "Service started successfully"
        else
            log_error "Service failed to start. Check: journalctl -u morgana-arsenal -n 50"
            exit 1
        fi
    else
        log_warn "Systemd service not configured. Start manually:"
        log_warn "  cd $MORGANA_DIR && python3 server.py --insecure --log DEBUG"
    fi
}

verify_update() {
    log_step "Verifying update..."
    
    # Check if server is responding
    sleep 2
    
    if curl -s -k https://localhost/api/v2/health > /dev/null 2>&1; then
        log_info "API is responding (HTTPS)"
    elif curl -s http://localhost:8888/api/v2/health > /dev/null 2>&1; then
        log_info "API is responding (HTTP:8888)"
    else
        log_warn "Could not verify API. Check server logs."
    fi
    
    # Show version
    if [ -f "$MORGANA_DIR/plugins/magma/src/App.vue" ]; then
        local ui_version=$(grep -o 'Version [0-9.]*' "$MORGANA_DIR/plugins/magma/src/App.vue" | head -1)
        log_info "UI $ui_version"
    fi
}

print_summary() {
    echo ""
    echo -e "${BOLD}${GREEN}==============================================================================${NC}"
    echo -e "${BOLD}${GREEN}  UPDATE COMPLETE!${NC}"
    echo -e "${BOLD}${GREEN}==============================================================================${NC}"
    echo ""
    echo -e "${BOLD}Version:${NC} ${MORGANA_VERSION}"
    echo -e "${BOLD}Backup:${NC} ${BACKUP_DIR}"
    echo -e "${BOLD}Log:${NC} ${LOG_FILE}"
    echo ""
    echo -e "${BOLD}Access Morgana Arsenal:${NC}"
    echo -e "  https://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "$CHANGELOG"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    print_banner
    check_root
    detect_user
    check_morgana_exists
    
    echo -e "${YELLOW}This will update Morgana Arsenal to version ${MORGANA_VERSION}${NC}"
    echo -e "${YELLOW}Press Ctrl+C to cancel, or wait 5 seconds to continue...${NC}"
    sleep 5
    
    backup_config
    stop_service
    update_code
    restore_config
    update_python_deps
    build_frontend
    compile_merlino
    fix_permissions
    start_service
    verify_update
    print_summary
    
    log_info "Update completed successfully!"
}

# Run main
main "$@"
