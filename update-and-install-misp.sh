#!/bin/bash
#
# Morgana Arsenal - Update & MISP Installation Script
# For existing Ubuntu installations
#
# Usage: sudo ./update-and-install-misp.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

MORGANA_REPO="https://github.com/x3m-ai/morgana-arsenal.git"

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${CYAN}=== $1 ===${NC}\n"; }

# Check root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root: sudo $0"
    exit 1
fi

# Detect user and morgana directory
if [ -d "/home/ubuntu/morgana-arsenal" ]; then
    MORGANA_USER="ubuntu"
    MORGANA_DIR="/home/ubuntu/morgana-arsenal"
elif [ -d "/home/morgana/morgana-arsenal" ]; then
    MORGANA_USER="morgana"
    MORGANA_DIR="/home/morgana/morgana-arsenal"
else
    log_error "Morgana Arsenal not found in /home/ubuntu or /home/morgana"
    exit 1
fi

MORGANA_HOME="/home/${MORGANA_USER}"

log_section "Morgana Arsenal Update + MISP Installation"
log_info "User: ${MORGANA_USER}"
log_info "Directory: ${MORGANA_DIR}"

# ============================================
# Step 1: Update Morgana Arsenal from public repo
# ============================================
log_section "Step 1: Updating Morgana Arsenal"

cd "${MORGANA_DIR}"

# Stop service if running
systemctl stop morgana-arsenal 2>/dev/null || true

# Backup current config
if [ -f "conf/local.yml" ]; then
    cp conf/local.yml conf/local.yml.backup
    log_info "Backed up conf/local.yml"
fi

# Update from public repo
log_info "Fetching from ${MORGANA_REPO}..."
sudo -u ${MORGANA_USER} git remote set-url origin ${MORGANA_REPO} 2>/dev/null || \
sudo -u ${MORGANA_USER} git remote add origin ${MORGANA_REPO} 2>/dev/null || true

sudo -u ${MORGANA_USER} git fetch origin
sudo -u ${MORGANA_USER} git reset --hard origin/main
sudo -u ${MORGANA_USER} git pull origin main

# Restore config if backed up
if [ -f "conf/local.yml.backup" ]; then
    cp conf/local.yml.backup conf/local.yml
    log_info "Restored conf/local.yml"
fi

# Update Python dependencies
log_info "Updating Python dependencies..."
if [ ! -d "venv" ]; then
    sudo -u ${MORGANA_USER} python3 -m venv venv
fi
sudo -u ${MORGANA_USER} bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

log_info "Morgana Arsenal updated!"

# ============================================
# Step 2: Install MISP Dependencies
# ============================================
log_section "Step 2: Installing MISP Dependencies"

apt-get update

# PHP and extensions
apt-get install -y \
    mariadb-server mariadb-client \
    redis-server \
    php php-fpm php-cli php-dev \
    php-json php-xml php-mysql php-opcache \
    php-readline php-mbstring php-zip php-curl \
    php-redis php-gd php-gnupg php-intl php-bcmath \
    php-apcu php-bz2 \
    zip unzip \
    git curl wget gnupg \
    libapache2-mod-php 2>/dev/null || true

# Detect PHP version
PHP_VERSION=$(php -r "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;")
log_info "PHP Version: ${PHP_VERSION}"

# Enable services
systemctl enable mariadb redis-server php${PHP_VERSION}-fpm
systemctl start mariadb redis-server php${PHP_VERSION}-fpm

log_info "MISP dependencies installed"

# ============================================
# Step 3: Clone/Update MISP
# ============================================
log_section "Step 3: Installing MISP"

MISP_DIR="/var/www/MISP"

if [ -d "${MISP_DIR}" ]; then
    log_info "MISP directory exists, updating..."
    cd ${MISP_DIR}
    sudo -u www-data git fetch origin
    sudo -u www-data git pull origin 2.4 || sudo -u www-data git pull origin main
else
    log_info "Cloning MISP..."
    mkdir -p /var/www
    git clone https://github.com/MISP/MISP.git ${MISP_DIR}
    chown -R www-data:www-data ${MISP_DIR}
    cd ${MISP_DIR}
    sudo -u www-data git checkout 2.4 || sudo -u www-data git checkout main
fi

# Update submodules
cd ${MISP_DIR}
sudo -u www-data git submodule update --init --recursive

# Install Python dependencies for MISP
log_info "Installing MISP Python dependencies..."
sudo -u www-data python3 -m venv ${MISP_DIR}/venv
sudo -u www-data ${MISP_DIR}/venv/bin/pip install --upgrade pip
sudo -u www-data ${MISP_DIR}/venv/bin/pip install -r ${MISP_DIR}/requirements.txt 2>/dev/null || true

# Install Composer dependencies
cd ${MISP_DIR}/app
if [ -f "composer.phar" ]; then
    sudo -u www-data php composer.phar install --no-dev
elif command -v composer &> /dev/null; then
    sudo -u www-data composer install --no-dev
else
    log_info "Installing Composer..."
    curl -sS https://getcomposer.org/installer | php
    mv composer.phar /usr/local/bin/composer
    chmod +x /usr/local/bin/composer
    sudo -u www-data composer install --no-dev
fi

log_info "MISP installed/updated"

# ============================================
# Step 4: Configure MariaDB for MISP
# ============================================
log_section "Step 4: Configuring Database"

# Check if MISP database exists
if ! mysql -e "USE misp" 2>/dev/null; then
    log_info "Creating MISP database..."
    mysql -e "CREATE DATABASE misp;"
    mysql -e "CREATE USER IF NOT EXISTS 'misp'@'localhost' IDENTIFIED BY 'misp_password';"
    mysql -e "GRANT ALL PRIVILEGES ON misp.* TO 'misp'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    
    # Import schema
    mysql -u misp -pmisp_password misp < ${MISP_DIR}/INSTALL/MYSQL.sql
    log_info "Database created and schema imported"
else
    log_info "MISP database already exists"
fi

# ============================================
# Step 5: Configure MISP
# ============================================
log_section "Step 5: Configuring MISP"

cd ${MISP_DIR}/app/Config

# Create config files if they don't exist
if [ ! -f "database.php" ]; then
    cp database.default.php database.php
    # Update database config
    sed -i "s/'database' => 'misp'/'database' => 'misp'/" database.php
    sed -i "s/'login' => 'misp'/'login' => 'misp'/" database.php
    sed -i "s/'password' => ''/'password' => 'misp_password'/" database.php
    chown www-data:www-data database.php
    log_info "Created database.php"
fi

if [ ! -f "core.php" ]; then
    cp core.default.php core.php
    chown www-data:www-data core.php
    log_info "Created core.php"
fi

if [ ! -f "config.php" ]; then
    cp config.default.php config.php
    chown www-data:www-data config.php
    log_info "Created config.php"
fi

# Set permissions
chown -R www-data:www-data ${MISP_DIR}
chmod -R 750 ${MISP_DIR}
chmod -R g+ws ${MISP_DIR}/app/tmp
chmod -R g+ws ${MISP_DIR}/app/files
chmod -R g+ws ${MISP_DIR}/app/files/scripts/tmp 2>/dev/null || true

log_info "MISP configured"

# ============================================
# Step 6: Install MISP Modules
# ============================================
log_section "Step 6: Installing MISP Modules"

pip3 install misp-modules --break-system-packages --ignore-installed typing-extensions 2>/dev/null || \
pip3 install misp-modules --ignore-installed typing-extensions 2>/dev/null || \
pip3 install misp-modules 2>/dev/null || true

# Create systemd service
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
systemctl start misp-modules || log_warn "MISP modules may need configuration"

log_info "MISP Modules installed"

# ============================================
# Step 7: Configure Nginx for MISP
# ============================================
log_section "Step 7: Configuring Nginx for MISP"

# Get server IP
SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || \
            curl -s https://ipinfo.io/ip 2>/dev/null || \
            hostname -I | awk '{print $1}')

# MISP HTTP backend (internal)
cat > /etc/nginx/sites-available/misp.conf << EOF
server {
    listen 8080;
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
    server_name ${SERVER_IP} localhost;
    
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

# Enable sites
ln -sf /etc/nginx/sites-available/misp.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/misp-https.conf /etc/nginx/sites-enabled/

# Test and reload nginx
nginx -t && systemctl reload nginx

log_info "Nginx configured for MISP"

# ============================================
# Step 8: Restart Services
# ============================================
log_section "Step 8: Restarting Services"

systemctl restart php${PHP_VERSION}-fpm
systemctl restart nginx
systemctl restart morgana-arsenal
systemctl restart misp-modules 2>/dev/null || true

log_info "Services restarted"

# ============================================
# Step 9: Verification
# ============================================
log_section "Step 9: Verification"

echo "Service Status:"
systemctl is-active --quiet nginx && echo -e "  Nginx: ${GREEN}Running${NC}" || echo -e "  Nginx: ${RED}Stopped${NC}"
systemctl is-active --quiet morgana-arsenal && echo -e "  Morgana Arsenal: ${GREEN}Running${NC}" || echo -e "  Morgana Arsenal: ${RED}Stopped${NC}"
systemctl is-active --quiet php${PHP_VERSION}-fpm && echo -e "  PHP-FPM: ${GREEN}Running${NC}" || echo -e "  PHP-FPM: ${RED}Stopped${NC}"
systemctl is-active --quiet misp-modules && echo -e "  MISP Modules: ${GREEN}Running${NC}" || echo -e "  MISP Modules: ${YELLOW}Check config${NC}"
systemctl is-active --quiet mariadb && echo -e "  MariaDB: ${GREEN}Running${NC}" || echo -e "  MariaDB: ${RED}Stopped${NC}"
systemctl is-active --quiet redis-server && echo -e "  Redis: ${GREEN}Running${NC}" || echo -e "  Redis: ${RED}Stopped${NC}"

# ============================================
# Complete
# ============================================
log_section "Installation Complete!"

echo -e "
${GREEN}Morgana Arsenal updated and MISP installed!${NC}

${CYAN}Access URLs:${NC}
  Morgana Arsenal: https://${SERVER_IP}
  MISP:            https://${SERVER_IP}:8443

${CYAN}Default Credentials:${NC}
  Morgana: admin / admin
  MISP:    admin@admin.test / admin (change on first login)

${CYAN}MISP Modules API:${NC}
  curl http://127.0.0.1:6666/modules

${CYAN}Useful Commands:${NC}
  sudo systemctl status morgana-arsenal
  sudo systemctl status misp-modules
  sudo journalctl -u morgana-arsenal -f
"
