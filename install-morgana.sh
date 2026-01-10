#!/bin/bash
#
# Morgana Arsenal - Complete Fresh Installation Script
# For Ubuntu 22.04/24.04 LTS (AWS or any cloud/VM)
#
# This script installs Morgana Arsenal from the public repository
# with nginx, SSL certificates, and optionally MISP
#
# Usage: 
#   curl -sSL https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-morgana.sh | sudo bash
#   or
#   sudo ./install-morgana.sh [OPTIONS]
#
# Options:
#   --with-misp     Also install MISP (requires more time and resources)
#   --ip IP_ADDR    Use specific IP address (default: auto-detect)
#   --user USER     Install for specific user (default: ubuntu or morgana)
#

set -e

# ============================================
# Configuration
# ============================================
MORGANA_REPO="https://github.com/x3m-ai/morgana-arsenal.git"
MORGANA_BRANCH="main"
INSTALL_MISP=false
SERVER_IP=""
MORGANA_USER=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================
# Parse Arguments
# ============================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-misp)
            INSTALL_MISP=true
            shift
            ;;
        --ip)
            SERVER_IP="$2"
            shift 2
            ;;
        --user)
            MORGANA_USER="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================
# Helper Functions
# ============================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# ============================================
# Pre-flight Checks
# ============================================
log_section "Morgana Arsenal Installation"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root: sudo $0"
    exit 1
fi

# Detect user if not specified
if [ -z "$MORGANA_USER" ]; then
    if id "ubuntu" &>/dev/null; then
        MORGANA_USER="ubuntu"
    elif id "morgana" &>/dev/null; then
        MORGANA_USER="morgana"
    else
        MORGANA_USER=$(logname 2>/dev/null || echo "root")
    fi
fi

MORGANA_HOME="/home/${MORGANA_USER}"
MORGANA_DIR="${MORGANA_HOME}/morgana-arsenal"

# Detect IP if not specified
if [ -z "$SERVER_IP" ]; then
    # Try to get public IP (for AWS)
    SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || \
                curl -s https://ipinfo.io/ip 2>/dev/null || \
                hostname -I | awk '{print $1}')
fi

log_info "Installation User: ${MORGANA_USER}"
log_info "Installation Directory: ${MORGANA_DIR}"
log_info "Server IP: ${SERVER_IP}"
log_info "Install MISP: ${INSTALL_MISP}"
echo ""

# ============================================
# Step 1: System Update and Dependencies
# ============================================
log_section "Step 1: Installing System Dependencies"

apt-get update
apt-get install -y \
    git curl wget vim htop \
    python3 python3-pip python3-venv \
    build-essential libssl-dev libffi-dev \
    nginx \
    openssl \
    software-properties-common

log_info "System dependencies installed"

# ============================================
# Step 2: Clone Morgana Arsenal
# ============================================
log_section "Step 2: Cloning Morgana Arsenal"

if [ -d "${MORGANA_DIR}" ]; then
    log_warn "Directory exists, updating..."
    cd "${MORGANA_DIR}"
    sudo -u ${MORGANA_USER} git fetch origin
    sudo -u ${MORGANA_USER} git reset --hard origin/${MORGANA_BRANCH}
    sudo -u ${MORGANA_USER} git pull origin ${MORGANA_BRANCH}
else
    sudo -u ${MORGANA_USER} git clone ${MORGANA_REPO} "${MORGANA_DIR}"
    cd "${MORGANA_DIR}"
    sudo -u ${MORGANA_USER} git checkout ${MORGANA_BRANCH}
fi

log_info "Morgana Arsenal cloned/updated"

# ============================================
# Step 3: Python Virtual Environment
# ============================================
log_section "Step 3: Setting up Python Environment"

cd "${MORGANA_DIR}"

if [ ! -d "venv" ]; then
    sudo -u ${MORGANA_USER} python3 -m venv venv
fi

sudo -u ${MORGANA_USER} bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

log_info "Python environment ready"

# ============================================
# Step 4: SSL Certificates
# ============================================
log_section "Step 4: Generating SSL Certificates"

mkdir -p /etc/nginx/ssl
chmod 700 /etc/nginx/ssl

# Generate certificate for the server IP and localhost
openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
    -keyout /etc/nginx/ssl/caldera.key \
    -out /etc/nginx/ssl/caldera.crt \
    -subj "/C=US/ST=Cloud/L=AWS/O=Morgana/OU=Security/CN=${SERVER_IP}" \
    -addext "subjectAltName=DNS:localhost,IP:${SERVER_IP},IP:127.0.0.1"

chmod 644 /etc/nginx/ssl/caldera.crt
chmod 600 /etc/nginx/ssl/caldera.key

log_info "SSL certificates generated for ${SERVER_IP}"

# ============================================
# Step 5: Nginx Configuration
# ============================================
log_section "Step 5: Configuring Nginx"

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Morgana Arsenal HTTPS (443)
cat > /etc/nginx/sites-available/caldera-proxy << EOF
# Nginx Reverse Proxy Configuration for Morgana Arsenal
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${SERVER_IP} localhost;
    
    ssl_certificate /etc/nginx/ssl/caldera.crt;
    ssl_certificate_key /etc/nginx/ssl/caldera.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    location / {
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, KEY, Authorization, X-Requested-With, Accept, Origin' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, KEY, Authorization, X-Requested-With, Accept, Origin' always;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' '0';
            return 204;
        }
        
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }
    
    location /nginx-health {
        access_log off;
        return 200 "Nginx OK\n";
        add_header Content-Type text/plain;
    }
    
    access_log /var/log/nginx/morgana-access.log;
    error_log /var/log/nginx/morgana-error.log warn;
}
EOF

# HTTP redirect to HTTPS (80)
cat > /etc/nginx/sites-available/morgana-redirect << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_IP} localhost _;
    
    # Health check endpoint (for load balancers)
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

# Enable sites
ln -sf /etc/nginx/sites-available/caldera-proxy /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/morgana-redirect /etc/nginx/sites-enabled/

# Test and reload nginx
nginx -t
systemctl reload nginx
systemctl enable nginx

log_info "Nginx configured and running"

# ============================================
# Step 6: Systemd Service
# ============================================
log_section "Step 6: Creating Systemd Service"

cat > /etc/systemd/system/morgana-arsenal.service << EOF
[Unit]
Description=Morgana Arsenal C2 Framework
After=network.target nginx.service
Wants=nginx.service

[Service]
Type=simple
User=${MORGANA_USER}
Group=${MORGANA_USER}
WorkingDirectory=${MORGANA_DIR}
Environment="PATH=${MORGANA_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=${MORGANA_DIR}/venv/bin/python3 ${MORGANA_DIR}/server.py --insecure --log DEBUG
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=morgana-arsenal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable morgana-arsenal
systemctl start morgana-arsenal

log_info "Morgana Arsenal service created and started"

# ============================================
# Step 7: MISP Installation (Optional)
# ============================================
if [ "$INSTALL_MISP" = true ]; then
    log_section "Step 7: Installing MISP"
    
    # Install MISP dependencies
    apt-get install -y \
        mariadb-server mariadb-client \
        redis-server \
        php php-fpm php-cli php-dev \
        php-json php-xml php-mysql php-opcache \
        php-readline php-mbstring php-zip php-curl \
        php-redis php-gd php-gnupg php-intl php-bcmath \
        zip unzip
    
    # Enable services
    systemctl enable mariadb redis-server php*-fpm
    systemctl start mariadb redis-server php*-fpm
    
    # MISP installation would go here
    # For now, just install misp-modules
    log_warn "Full MISP installation requires manual steps"
    log_info "Installing MISP modules..."
    
    pip3 install misp-modules --break-system-packages --ignore-installed typing-extensions || true
    
    # Create misp-modules service
    cat > /etc/systemd/system/misp-modules.service << EOF
[Unit]
Description=MISP Modules
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
ExecStart=/usr/local/bin/misp-modules -l 127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable misp-modules
    systemctl start misp-modules || log_warn "MISP modules failed to start (MISP may not be installed)"
    
    log_info "MISP modules installed"
else
    log_info "Skipping MISP installation (use --with-misp to install)"
fi

# ============================================
# Step 8: Firewall Configuration
# ============================================
log_section "Step 8: Configuring Firewall"

if command -v ufw &> /dev/null; then
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw --force enable || true
    log_info "UFW firewall configured"
else
    log_warn "UFW not found, please configure firewall manually"
fi

# ============================================
# Step 9: Final Verification
# ============================================
log_section "Step 9: Verification"

sleep 3  # Wait for services to fully start

# Check services
echo "Service Status:"
systemctl is-active --quiet nginx && echo -e "  Nginx: ${GREEN}Running${NC}" || echo -e "  Nginx: ${RED}Stopped${NC}"
systemctl is-active --quiet morgana-arsenal && echo -e "  Morgana Arsenal: ${GREEN}Running${NC}" || echo -e "  Morgana Arsenal: ${RED}Stopped${NC}"

# Check endpoints
echo ""
echo "Endpoint Tests:"
curl -sk https://localhost/nginx-health && echo -e "  ${GREEN}Nginx HTTPS OK${NC}" || echo -e "  ${RED}Nginx HTTPS Failed${NC}"
curl -sk https://localhost/api/v2/health 2>/dev/null && echo -e "  ${GREEN}Morgana API OK${NC}" || echo -e "  ${YELLOW}Morgana API starting...${NC}"

# ============================================
# Complete
# ============================================
log_section "Installation Complete!"

echo -e "
${GREEN}Morgana Arsenal has been installed successfully!${NC}

${CYAN}Access URLs:${NC}
  - HTTPS: https://${SERVER_IP}
  - HTTP:  http://${SERVER_IP} (redirects to HTTPS)

${CYAN}Default Credentials:${NC}
  - Username: admin
  - Password: admin

${CYAN}Useful Commands:${NC}
  - View logs:     sudo journalctl -u morgana-arsenal -f
  - Restart:       sudo systemctl restart morgana-arsenal
  - Stop:          sudo systemctl stop morgana-arsenal
  - Status:        sudo systemctl status morgana-arsenal

${CYAN}Files:${NC}
  - Installation:  ${MORGANA_DIR}
  - Nginx config:  /etc/nginx/sites-available/caldera-proxy
  - SSL cert:      /etc/nginx/ssl/caldera.crt
  - Service:       /etc/systemd/system/morgana-arsenal.service

${YELLOW}Note:${NC} The SSL certificate is self-signed. Browsers will show a warning.
"

if [ "$INSTALL_MISP" = true ]; then
    echo -e "
${CYAN}MISP:${NC}
  MISP modules are installed but full MISP requires additional setup.
  See: https://misp.github.io/MISP/
"
fi
