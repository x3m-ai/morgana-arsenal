#!/bin/bash
#
# Morgana Arsenal + MISP - Complete Installation Script
# For Ubuntu 22.04/24.04 (AWS, local VM, or bare metal)
#
# - If Morgana Arsenal not found: Full installation from scratch
# - If Morgana Arsenal exists: Update and install MISP
#
# Usage: curl -sL https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-morgana-misp.sh | sudo bash
#    or: sudo ./install-morgana-misp.sh [--user ubuntu] [--ip 1.2.3.4]
# last

set -e

# ============================================
# Configuration
# ============================================
MORGANA_REPO="https://github.com/x3m-ai/morgana-arsenal.git"
MISP_REPO="https://github.com/MISP/MISP.git"

# Local DNS domains
MORGANA_DOMAIN="morgana.merlino.local"
MISP_DOMAIN="misp.merlino.local"
LAUNCHER_DOMAIN="launcher.merlino.local"
LOCAL_DOMAIN="merlino.local"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${CYAN}════════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}════════════════════════════════════════${NC}\n"; }

# ============================================
# Parse Arguments
# ============================================
MORGANA_USER=""
SERVER_IP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            MORGANA_USER="$2"
            shift 2
            ;;
        --ip)
            SERVER_IP="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# ============================================
# Pre-flight Checks
# ============================================
log_section "Pre-flight Checks"

# Check root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root: sudo $0"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
    OS_VERSION=$VERSION_ID
else
    log_error "Cannot detect OS. This script requires Ubuntu 22.04 or 24.04"
    exit 1
fi

log_info "OS: ${OS_NAME} ${OS_VERSION}"

if [[ ! "$ID" =~ ^(ubuntu|debian)$ ]]; then
    log_warn "This script is designed for Ubuntu. Proceeding anyway..."
fi

# Detect user if not specified
if [ -z "$MORGANA_USER" ]; then
    if [ -d "/home/ubuntu" ]; then
        MORGANA_USER="ubuntu"
    elif [ -d "/home/morgana" ]; then
        MORGANA_USER="morgana"
    else
        # Get the user who called sudo
        MORGANA_USER="${SUDO_USER:-$(whoami)}"
        if [ "$MORGANA_USER" = "root" ]; then
            MORGANA_USER="ubuntu"
        fi
    fi
fi

MORGANA_HOME="/home/${MORGANA_USER}"
MORGANA_DIR="${MORGANA_HOME}/morgana-arsenal"

log_info "User: ${MORGANA_USER}"
log_info "Home: ${MORGANA_HOME}"

# Create user if doesn't exist
if ! id "$MORGANA_USER" &>/dev/null; then
    log_info "Creating user ${MORGANA_USER}..."
    useradd -m -s /bin/bash "$MORGANA_USER"
fi

# Detect server IP if not specified
if [ -z "$SERVER_IP" ]; then
    # Prefer private/local IP for LAN DNS (most common use case)
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    # If no local IP, try AWS metadata
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP=$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
    fi
    
    # Last resort: external IP service
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP=$(curl -s --connect-timeout 5 https://ipinfo.io/ip 2>/dev/null || true)
    fi
fi

log_info "Server IP: ${SERVER_IP}"

# ============================================
# Detect Installation Mode
# ============================================
FRESH_INSTALL=false

if [ -d "${MORGANA_DIR}" ] && [ -f "${MORGANA_DIR}/server.py" ]; then
    log_info "Morgana Arsenal found at ${MORGANA_DIR}"
    log_info "Mode: UPDATE + MISP Installation"
else
    log_info "Morgana Arsenal not found"
    log_info "Mode: FRESH Installation + MISP"
    FRESH_INSTALL=true
fi

# ============================================
# Step 1: System Dependencies
# ============================================
log_section "Step 1: Installing System Dependencies"

apt-get update

# Common dependencies
apt-get install -y \
    git curl wget gnupg \
    python3 python3-pip python3-venv python3-dev \
    build-essential libssl-dev libffi-dev \
    nginx \
    mariadb-server mariadb-client \
    redis-server \
    zip unzip jq \
    dnsmasq

# PHP and extensions for MISP
apt-get install -y \
    php php-fpm php-cli php-dev \
    php-json php-xml php-mysql php-opcache \
    php-readline php-mbstring php-zip php-curl \
    php-redis php-gd php-gnupg php-intl php-bcmath \
    php-apcu php-bz2 2>/dev/null || true

# Detect PHP version
PHP_VERSION=$(php -r "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;" 2>/dev/null || echo "8.1")
log_info "PHP Version: ${PHP_VERSION}"

# Enable services
systemctl enable mariadb redis-server nginx php${PHP_VERSION}-fpm 2>/dev/null || true
systemctl start mariadb redis-server php${PHP_VERSION}-fpm 2>/dev/null || true

log_info "System dependencies installed"

# ============================================
# Step 2: Morgana Arsenal (Install or Update)
# ============================================
log_section "Step 2: Morgana Arsenal"

if [ "$FRESH_INSTALL" = true ]; then
    # Fresh installation
    log_info "Cloning Morgana Arsenal from ${MORGANA_REPO}..."
    
    sudo -u ${MORGANA_USER} git clone ${MORGANA_REPO} ${MORGANA_DIR}
    
    cd ${MORGANA_DIR}
    
    # Create Python virtual environment
    log_info "Creating Python virtual environment..."
    sudo -u ${MORGANA_USER} python3 -m venv venv
    sudo -u ${MORGANA_USER} bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    
    # Create local config
    if [ ! -f "conf/local.yml" ]; then
        log_info "Creating local configuration..."
        cat > conf/local.yml << EOF
# Morgana Arsenal Local Configuration
host: 0.0.0.0
port: 8888

users:
  admin:
    password: admin

plugins:
  - magma
  - stockpile
  - sandcat
  - merlino

logging:
  level: DEBUG
EOF
        chown ${MORGANA_USER}:${MORGANA_USER} conf/local.yml
    fi
    
    # Create agents.yml if not exists (required by Caldera)
    if [ ! -f "conf/agents.yml" ]; then
        log_info "Creating agents.yml configuration..."
        if [ -f "plugins/merlino/conf/agents.yml" ]; then
            cp plugins/merlino/conf/agents.yml conf/agents.yml
        else
            cat > conf/agents.yml << EOF
bootstrap_abilities:
- 43b3754c-def4-4699-a673-1d85648fda6a
deployments:
- merlino-1234-5678-90ab-cdef-merlino1
implant_name: svchost
sleep_max: 60
sleep_min: 30
untrusted_timer: 999999999
watchdog: 999999999
EOF
        fi
        chown ${MORGANA_USER}:${MORGANA_USER} conf/agents.yml
    fi
    
    # Create payloads.yml if not exists (required by Caldera)
    if [ ! -f "conf/payloads.yml" ]; then
        log_info "Creating payloads.yml configuration..."
        cat > conf/payloads.yml << EOF
special_payloads: {}
standard_payloads: {}
EOF
        chown ${MORGANA_USER}:${MORGANA_USER} conf/payloads.yml
    fi
    
    # Create caldera log directory (server.py expects this path)
    mkdir -p ${MORGANA_HOME}/caldera
    chown ${MORGANA_USER}:${MORGANA_USER} ${MORGANA_HOME}/caldera
    
    log_info "Morgana Arsenal installed"
    
else
    # Update existing installation
    log_info "Updating Morgana Arsenal..."
    
    cd ${MORGANA_DIR}
    
    # Stop service if running
    systemctl stop morgana-arsenal 2>/dev/null || true
    
    # Backup config
    if [ -f "conf/local.yml" ]; then
        cp conf/local.yml conf/local.yml.backup
        log_info "Backed up conf/local.yml"
    fi
    
    # Update from repo
    sudo -u ${MORGANA_USER} git remote set-url origin ${MORGANA_REPO} 2>/dev/null || \
    sudo -u ${MORGANA_USER} git remote add origin ${MORGANA_REPO} 2>/dev/null || true
    
    sudo -u ${MORGANA_USER} git fetch origin
    sudo -u ${MORGANA_USER} git reset --hard origin/main
    sudo -u ${MORGANA_USER} git pull origin main 2>/dev/null || true
    
    # Restore config
    if [ -f "conf/local.yml.backup" ]; then
        cp conf/local.yml.backup conf/local.yml
        log_info "Restored conf/local.yml"
    fi
    
    # Update venv
    if [ ! -d "venv" ]; then
        sudo -u ${MORGANA_USER} python3 -m venv venv
    fi
    sudo -u ${MORGANA_USER} bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    
    # Ensure agents.yml exists after update (required by Caldera)
    if [ ! -f "conf/agents.yml" ]; then
        log_info "Creating agents.yml configuration..."
        if [ -f "plugins/merlino/conf/agents.yml" ]; then
            cp plugins/merlino/conf/agents.yml conf/agents.yml
        else
            cat > conf/agents.yml << EOF
bootstrap_abilities:
- 43b3754c-def4-4699-a673-1d85648fda6a
deployments:
- merlino-1234-5678-90ab-cdef-merlino1
implant_name: svchost
sleep_max: 60
sleep_min: 30
untrusted_timer: 999999999
watchdog: 999999999
EOF
        fi
        chown ${MORGANA_USER}:${MORGANA_USER} conf/agents.yml
    fi
    
    # Ensure payloads.yml exists after update (required by Caldera)
    if [ ! -f "conf/payloads.yml" ]; then
        log_info "Creating payloads.yml configuration..."
        cat > conf/payloads.yml << EOF
special_payloads: {}
standard_payloads: {}
EOF
        chown ${MORGANA_USER}:${MORGANA_USER} conf/payloads.yml
    fi
    
    # Ensure caldera log directory exists
    mkdir -p ${MORGANA_HOME}/caldera
    chown ${MORGANA_USER}:${MORGANA_USER} ${MORGANA_HOME}/caldera
    
    log_info "Morgana Arsenal updated"
fi

# Build Magma frontend if needed
if [ -d "${MORGANA_DIR}/plugins/magma" ] && [ ! -d "${MORGANA_DIR}/plugins/magma/dist" ]; then
    log_info "Building Magma frontend..."
    cd ${MORGANA_DIR}/plugins/magma
    if command -v npm &> /dev/null; then
        sudo -u ${MORGANA_USER} npm install
        sudo -u ${MORGANA_USER} npm run build
    else
        log_warn "npm not found, installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
        sudo -u ${MORGANA_USER} npm install
        sudo -u ${MORGANA_USER} npm run build
    fi
fi

# ============================================
# Step 3: DNS Configuration (dnsmasq)
# ============================================
log_section "Step 3: Local DNS Configuration (dnsmasq)"

# Stop systemd-resolved if it's blocking port 53
if systemctl is-active --quiet systemd-resolved; then
    log_info "Configuring systemd-resolved to work with dnsmasq..."
    
    # Configure systemd-resolved to not listen on port 53
    mkdir -p /etc/systemd/resolved.conf.d
    cat > /etc/systemd/resolved.conf.d/dnsmasq.conf << 'EOF'
[Resolve]
DNSStubListener=no
EOF
    
    # Point resolv.conf to dnsmasq
    rm -f /etc/resolv.conf
    echo "nameserver 127.0.0.1" > /etc/resolv.conf
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf
    
    systemctl restart systemd-resolved
fi

# Configure dnsmasq
log_info "Configuring dnsmasq for ${LOCAL_DOMAIN}..."

cat > /etc/dnsmasq.d/merlino.conf << EOF
# Merlino Local DNS Configuration
# All *.merlino.local domains resolve to this server

# Listen on all interfaces
listen-address=127.0.0.1
listen-address=${SERVER_IP}

# Don't read /etc/resolv.conf (we'll specify upstream DNS)
no-resolv

# Upstream DNS servers
server=8.8.8.8
server=8.8.4.4

# Local domain configuration
local=/${LOCAL_DOMAIN}/
domain=${LOCAL_DOMAIN}

# A records for local services
address=/${MORGANA_DOMAIN}/${SERVER_IP}
address=/${MISP_DOMAIN}/${SERVER_IP}
address=/${LAUNCHER_DOMAIN}/${SERVER_IP}

# Wildcard for all *.merlino.local
address=/${LOCAL_DOMAIN}/${SERVER_IP}

# Cache size
cache-size=1000

# Don't forward short names
domain-needed
bogus-priv

# Log queries (optional, comment out in production)
# log-queries
EOF

# Also add to /etc/hosts for local resolution
if ! grep -q "${MORGANA_DOMAIN}" /etc/hosts; then
    cat >> /etc/hosts << EOF

# Merlino Local Domains
${SERVER_IP} ${MORGANA_DOMAIN}
${SERVER_IP} ${MISP_DOMAIN}
${SERVER_IP} ${LAUNCHER_DOMAIN}
${SERVER_IP} ${LOCAL_DOMAIN}
EOF
    log_info "Added local domains to /etc/hosts"
fi

# Enable and restart dnsmasq
systemctl enable dnsmasq
systemctl restart dnsmasq

# Verify DNS is working
sleep 2
if host ${MORGANA_DOMAIN} 127.0.0.1 &>/dev/null || nslookup ${MORGANA_DOMAIN} 127.0.0.1 &>/dev/null; then
    log_info "DNS resolution working for ${MORGANA_DOMAIN}"
else
    log_warn "DNS may need manual verification. Check: nslookup ${MORGANA_DOMAIN} 127.0.0.1"
fi

log_info "dnsmasq configured for ${LOCAL_DOMAIN}"

# ============================================
# Step 4: SSL Certificates (with local domains)
# ============================================
log_section "Step 4: SSL Certificates"

mkdir -p /etc/nginx/ssl

# Always regenerate certificates to include local domains
log_info "Generating SSL certificates for local domains..."

# Create OpenSSL config for SAN (Subject Alternative Names)
cat > /tmp/openssl-san.cnf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req
x509_extensions = v3_ca

[dn]
C = IT
ST = Italy
L = Rome
O = Morgana Arsenal
OU = Security
CN = ${MORGANA_DOMAIN}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${MORGANA_DOMAIN}
DNS.2 = ${MISP_DOMAIN}
DNS.3 = ${LAUNCHER_DOMAIN}
DNS.4 = ${LOCAL_DOMAIN}
DNS.5 = *.${LOCAL_DOMAIN}
DNS.6 = localhost
IP.1 = ${SERVER_IP}
IP.2 = 127.0.0.1
EOF

# Generate CA key and certificate (for importing into browsers/systems)
openssl genrsa -out /etc/nginx/ssl/merlino-ca.key 4096
openssl req -x509 -new -nodes -key /etc/nginx/ssl/merlino-ca.key \
    -sha256 -days 3650 -out /etc/nginx/ssl/merlino-ca.crt \
    -subj "/C=IT/ST=Italy/L=Rome/O=Merlino CA/CN=Merlino Root CA"

# Generate server key and CSR
openssl genrsa -out /etc/nginx/ssl/caldera.key 2048
openssl req -new -key /etc/nginx/ssl/caldera.key \
    -out /tmp/caldera.csr \
    -config /tmp/openssl-san.cnf

# Sign the certificate with our CA
openssl x509 -req -in /tmp/caldera.csr \
    -CA /etc/nginx/ssl/merlino-ca.crt \
    -CAkey /etc/nginx/ssl/merlino-ca.key \
    -CAcreateserial \
    -out /etc/nginx/ssl/caldera.crt \
    -days 3650 -sha256 \
    -extfile /tmp/openssl-san.cnf \
    -extensions v3_req

# Cleanup
rm -f /tmp/openssl-san.cnf /tmp/caldera.csr

chmod 600 /etc/nginx/ssl/caldera.key
chmod 600 /etc/nginx/ssl/merlino-ca.key
chmod 644 /etc/nginx/ssl/caldera.crt
chmod 644 /etc/nginx/ssl/merlino-ca.crt

# Copy CA cert to a user-accessible location
cp /etc/nginx/ssl/merlino-ca.crt /var/www/html/merlino-ca.crt 2>/dev/null || true

log_info "SSL certificates generated for:"
log_info "  - ${MORGANA_DOMAIN}"
log_info "  - ${MISP_DOMAIN}"
log_info "  - ${LAUNCHER_DOMAIN}"
log_info "  - *.${LOCAL_DOMAIN}"
log_info "  - ${SERVER_IP}"
log_info ""
log_info "CA Certificate available at: http://${SERVER_IP}/merlino-ca.crt"

# ============================================
# Step 5: Nginx Configuration for Morgana
# ============================================
log_section "Step 5: Nginx Configuration"

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Morgana Arsenal HTTPS (port 443)
cat > /etc/nginx/sites-available/caldera-proxy << EOF
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${MORGANA_DOMAIN} ${SERVER_IP} localhost;

    ssl_certificate /etc/nginx/ssl/caldera.crt;
    ssl_certificate_key /etc/nginx/ssl/caldera.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    access_log /var/log/nginx/morgana-access.log;
    error_log /var/log/nginx/morgana-error.log warn;
}
EOF

# Launcher page (port 80)
cat > /etc/nginx/sites-available/launcher.conf << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${LAUNCHER_DOMAIN} ${SERVER_IP} localhost;

    root /var/www/html;
    index launcher.html index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

# Create launcher page
mkdir -p /var/www/html
cat > /var/www/html/launcher.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morgana Arsenal - Launcher</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #fff;
        }
        .container { text-align: center; padding: 40px; }
        h1 { font-size: 3em; margin-bottom: 10px; color: #e94560; }
        .subtitle { color: #a0a0a0; margin-bottom: 20px; }
        .dns-info { 
            background: rgba(0,0,0,0.3); 
            padding: 15px 25px; 
            border-radius: 10px; 
            margin-bottom: 30px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .dns-info code { color: #4fc3f7; }
        .services { display: flex; gap: 30px; justify-content: center; flex-wrap: wrap; }
        .service-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            width: 280px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            color: #fff;
        }
        .service-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(233, 69, 96, 0.3);
        }
        .service-icon { font-size: 3em; margin-bottom: 15px; }
        .service-name { font-size: 1.3em; font-weight: bold; margin-bottom: 10px; }
        .service-desc { color: #a0a0a0; font-size: 0.9em; margin-bottom: 10px; }
        .service-url { font-family: monospace; font-size: 0.8em; color: #4fc3f7; }
        .morgana-icon { color: #e94560; }
        .misp-icon { color: #4fc3f7; }
        .ca-link { margin-top: 30px; font-size: 0.9em; }
        .ca-link a { color: #4fc3f7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Morgana Arsenal</h1>
        <p class="subtitle">Command & Control Framework</p>
        <div class="dns-info">
            DNS Server: <code id="serverIp"></code> | Domain: <code>*.merlino.local</code>
        </div>
        <div class="services">
            <a href="https://morgana.merlino.local/" class="service-card" id="morganaCard">
                <div class="service-icon morgana-icon">&#9876;</div>
                <div class="service-name">Morgana Arsenal</div>
                <div class="service-desc">C2 Framework</div>
                <div class="service-url">https://morgana.merlino.local</div>
            </a>
            <a href="https://misp.merlino.local:8443/" class="service-card" id="mispCard">
                <div class="service-icon misp-icon">&#128373;</div>
                <div class="service-name">MISP</div>
                <div class="service-desc">Threat Intelligence</div>
                <div class="service-url">https://misp.merlino.local:8443</div>
            </a>
        </div>
        <div class="ca-link">
            <p>To avoid certificate warnings, install the <a href="/merlino-ca.crt">Merlino CA Certificate</a></p>
        </div>
    </div>
    <script>
        document.getElementById('serverIp').textContent = location.hostname;
    </script>
</body>
</html>
HTMLEOF

# Enable Morgana sites
ln -sf /etc/nginx/sites-available/caldera-proxy /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/launcher.conf /etc/nginx/sites-enabled/

log_info "Nginx configured for Morgana Arsenal"

# ============================================
# Step 6: Morgana Systemd Service
# ============================================
log_section "Step 6: Morgana Systemd Service"

cat > /etc/systemd/system/morgana-arsenal.service << EOF
[Unit]
Description=Morgana Arsenal C2 Framework
After=network.target

[Service]
Type=simple
User=${MORGANA_USER}
Group=${MORGANA_USER}
WorkingDirectory=${MORGANA_DIR}
ExecStart=${MORGANA_DIR}/venv/bin/python server.py --insecure --log DEBUG
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable morgana-arsenal

log_info "Morgana Arsenal service configured"

# ============================================
# Step 7: Install MISP
# ============================================
log_section "Step 7: Installing MISP"

MISP_DIR="/var/www/MISP"

if [ -d "${MISP_DIR}" ]; then
    log_info "MISP directory exists, updating..."
    cd ${MISP_DIR}
    git config --global --add safe.directory ${MISP_DIR} 2>/dev/null || true
    sudo -u www-data git fetch origin 2>/dev/null || git fetch origin 2>/dev/null || true
    sudo -u www-data git checkout 2.5 2>/dev/null || git checkout 2.5 2>/dev/null || true
    sudo -u www-data git pull origin 2.5 2>/dev/null || git pull origin 2.5 2>/dev/null || true
else
    log_info "Cloning MISP..."
    mkdir -p /var/www
    git clone ${MISP_REPO} ${MISP_DIR}
    chown -R www-data:www-data ${MISP_DIR}
    cd ${MISP_DIR}
    git config --global --add safe.directory ${MISP_DIR} 2>/dev/null || true
    sudo -u www-data git checkout 2.5 2>/dev/null || git checkout 2.5 2>/dev/null || true
fi

# Update submodules
cd ${MISP_DIR}
sudo -u www-data git submodule update --init --recursive 2>/dev/null || true

# Python venv for MISP
log_info "Setting up MISP Python environment..."
if [ ! -d "${MISP_DIR}/venv" ]; then
    sudo -u www-data python3 -m venv ${MISP_DIR}/venv
fi
sudo -u www-data ${MISP_DIR}/venv/bin/pip install --upgrade pip 2>/dev/null || true
sudo -u www-data ${MISP_DIR}/venv/bin/pip install -r ${MISP_DIR}/requirements.txt 2>/dev/null || true

# Composer dependencies
cd ${MISP_DIR}/app
if [ ! -f "composer.phar" ] && ! command -v composer &> /dev/null; then
    log_info "Installing Composer..."
    curl -sS https://getcomposer.org/installer | php
    mv composer.phar /usr/local/bin/composer
    chmod +x /usr/local/bin/composer
fi

if [ -f "composer.json" ]; then
    sudo -u www-data composer install --no-dev 2>/dev/null || \
    sudo -u www-data php composer.phar install --no-dev 2>/dev/null || true
fi

log_info "MISP installed/updated"

# ============================================
# Step 8: Configure MariaDB for MISP
# ============================================
log_section "Step 8: Configuring MariaDB"

# Ensure MariaDB is running
systemctl start mariadb

# Create MISP database
if ! mysql -e "USE misp" 2>/dev/null; then
    log_info "Creating MISP database..."
    mysql -e "CREATE DATABASE IF NOT EXISTS misp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -e "CREATE USER IF NOT EXISTS 'misp'@'localhost' IDENTIFIED BY 'misp_password';"
    mysql -e "GRANT ALL PRIVILEGES ON misp.* TO 'misp'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    
    # Import schema if exists
    if [ -f "${MISP_DIR}/INSTALL/MYSQL.sql" ]; then
        mysql -u misp -pmisp_password misp < ${MISP_DIR}/INSTALL/MYSQL.sql 2>/dev/null || true
        log_info "Database schema imported"
    fi
else
    log_info "MISP database already exists"
fi

# ============================================
# Step 9: Configure MISP
# ============================================
log_section "Step 9: Configuring MISP"

cd ${MISP_DIR}/app/Config

# Create config files (including bootstrap.php which is required)
for conf in database core config bootstrap; do
    if [ ! -f "${conf}.php" ] && [ -f "${conf}.default.php" ]; then
        cp ${conf}.default.php ${conf}.php
        chown www-data:www-data ${conf}.php
        chmod 770 ${conf}.php
        log_info "Created ${conf}.php"
    fi
done

# Update database config with correct credentials
if [ -f "database.php" ]; then
    # Replace placeholder credentials with actual ones
    sed -i "s/'login' => 'db login'/'login' => 'misp'/" database.php 2>/dev/null || true
    sed -i "s/'password' => 'db password'/'password' => 'misp_password'/" database.php 2>/dev/null || true
    sed -i "s/'password' => ''/'password' => 'misp_password'/" database.php 2>/dev/null || true
    log_info "Database credentials configured"
fi

# Set permissions
chown -R www-data:www-data ${MISP_DIR}
chmod -R 750 ${MISP_DIR}
chmod -R g+ws ${MISP_DIR}/app/tmp 2>/dev/null || true
chmod -R g+ws ${MISP_DIR}/app/files 2>/dev/null || true

log_info "MISP configured"

# ============================================
# Step 10: Install MISP Modules
# ============================================
log_section "Step 10: Installing MISP Modules"

pip3 install misp-modules --break-system-packages --ignore-installed typing-extensions 2>/dev/null || \
pip3 install misp-modules --ignore-installed typing-extensions 2>/dev/null || \
pip3 install misp-modules 2>/dev/null || true

# Systemd service for MISP Modules
cat > /etc/systemd/system/misp-modules.service << 'EOF'
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

log_info "MISP Modules installed"

# ============================================
# Step 11: Nginx for MISP
# ============================================
log_section "Step 11: Nginx for MISP"

# MISP HTTP backend (internal only)
cat > /etc/nginx/sites-available/misp.conf << EOF
server {
    listen 127.0.0.1:8080;
    server_name localhost;
    
    root /var/www/MISP/app/webroot;
    index index.php;
    
    client_max_body_size 50M;
    
    location / {
        try_files \$uri \$uri/ /index.php?\$args;
    }
    
    location ~ \.php\$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php${PHP_VERSION}-fpm.sock;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        include fastcgi_params;
    }
}
EOF

# MISP HTTPS (port 8443)
cat > /etc/nginx/sites-available/misp-https.conf << EOF
server {
    listen 8443 ssl http2;
    listen [::]:8443 ssl http2;
    server_name ${MISP_DOMAIN} ${SERVER_IP} localhost;
    
    ssl_certificate /etc/nginx/ssl/caldera.crt;
    ssl_certificate_key /etc/nginx/ssl/caldera.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    root /var/www/MISP/app/webroot;
    index index.php;
    
    client_max_body_size 50M;
    
    location / {
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, Accept' always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
        
        try_files \$uri \$uri/ /index.php?\$args;
    }
    
    location ~ \.php\$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php${PHP_VERSION}-fpm.sock;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        fastcgi_param HTTPS on;
        include fastcgi_params;
    }
    
    access_log /var/log/nginx/misp-access.log;
    error_log /var/log/nginx/misp-error.log warn;
}
EOF

# Enable MISP sites
ln -sf /etc/nginx/sites-available/misp.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/misp-https.conf /etc/nginx/sites-enabled/

# Test nginx config
nginx -t

log_info "Nginx configured for MISP"

# ============================================
# Step 12: Start All Services
# ============================================
log_section "Step 12: Starting Services"

systemctl restart dnsmasq
systemctl restart php${PHP_VERSION}-fpm
systemctl restart nginx
systemctl start morgana-arsenal
systemctl start misp-modules 2>/dev/null || log_warn "MISP modules may need manual start"
systemctl start redis-server
systemctl start mariadb

# Wait for services to start
sleep 3

log_info "All services started"

# ============================================
# Step 13: Verification
# ============================================
log_section "Step 13: Verification"

echo ""
echo -e "${BOLD}Service Status:${NC}"
echo "────────────────────────────────────"

check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "  $2: ${GREEN}Running${NC}"
    else
        echo -e "  $2: ${RED}Stopped${NC}"
    fi
}

check_service dnsmasq "dnsmasq (DNS)"
check_service nginx "Nginx"
check_service morgana-arsenal "Morgana Arsenal"
check_service php${PHP_VERSION}-fpm "PHP-FPM"
check_service misp-modules "MISP Modules"
check_service mariadb "MariaDB"
check_service redis-server "Redis"

echo ""
echo -e "${BOLD}Port Status:${NC}"
echo "────────────────────────────────────"
ss -tlnp | grep -E ":(80|443|8080|8443|8888|6666) " | awk '{print "  "$4}' || echo "  (check with: ss -tlnp)"

# ============================================
# Complete!
# ============================================
log_section "Installation Complete!"

echo -e "
${GREEN}${BOLD}Morgana Arsenal + MISP installed successfully!${NC}

${CYAN}${BOLD}Local DNS Domains:${NC}
────────────────────────────────────
  DNS Server:      ${SERVER_IP} (use as DNS on client machines)
  Morgana:         ${MORGANA_DOMAIN}
  MISP:            ${MISP_DOMAIN}
  Launcher:        ${LAUNCHER_DOMAIN}

${CYAN}${BOLD}Access URLs (via DNS):${NC}
────────────────────────────────────
  Launcher:        http://${LAUNCHER_DOMAIN}
  Morgana Arsenal: https://${MORGANA_DOMAIN}
  MISP:            https://${MISP_DOMAIN}:8443

${CYAN}${BOLD}Access URLs (via IP):${NC}
────────────────────────────────────
  Launcher:        http://${SERVER_IP}
  Morgana Arsenal: https://${SERVER_IP}
  MISP:            https://${SERVER_IP}:8443

${CYAN}${BOLD}Default Credentials:${NC}
────────────────────────────────────
  Morgana: admin / admin
  MISP:    admin@admin.test / admin

${CYAN}${BOLD}CA Certificate (to avoid browser warnings):${NC}
────────────────────────────────────
  Download: http://${SERVER_IP}/merlino-ca.crt
  Location: /etc/nginx/ssl/merlino-ca.crt

  Install on clients:
    Windows: Double-click > Install > Trusted Root CAs
    macOS:   Double-click > Add to Keychain > Trust
    Linux:   sudo cp merlino-ca.crt /usr/local/share/ca-certificates/
             sudo update-ca-certificates

${CYAN}${BOLD}Client DNS Configuration:${NC}
────────────────────────────────────
  Set DNS server to: ${SERVER_IP}
  
  Or add to /etc/hosts (Linux/Mac) or C:\\Windows\\System32\\drivers\\etc\\hosts:
    ${SERVER_IP} ${MORGANA_DOMAIN} ${MISP_DOMAIN} ${LAUNCHER_DOMAIN}

${CYAN}${BOLD}Useful Commands:${NC}
────────────────────────────────────
  sudo systemctl status morgana-arsenal
  sudo systemctl status dnsmasq
  nslookup ${MORGANA_DOMAIN} ${SERVER_IP}
  curl http://127.0.0.1:6666/modules

${CYAN}${BOLD}Logs:${NC}
────────────────────────────────────
  Morgana: ${MORGANA_DIR}/caldera-debug.log
  DNS:     /var/log/syslog | grep dnsmasq
  Nginx:   /var/log/nginx/morgana-*.log
  MISP:    /var/log/nginx/misp-*.log
"
