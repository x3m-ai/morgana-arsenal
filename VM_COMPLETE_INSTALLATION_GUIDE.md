# Morgana VM Complete Installation Guide

This document provides a comprehensive step-by-step guide to replicate the complete Morgana Arsenal + MISP VM setup from scratch.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Base System Installation](#base-system-installation)
3. [Nginx Installation and Configuration](#nginx-installation-and-configuration)
4. [SSL Certificates Setup](#ssl-certificates-setup)
5. [Morgana Arsenal Installation](#morgana-arsenal-installation)
6. [MISP Installation](#misp-installation)
7. [MISP Modules Installation](#misp-modules-installation)
8. [Systemd Services Configuration](#systemd-services-configuration)
9. [Launcher Pages Setup](#launcher-pages-setup)
10. [Verification and Testing](#verification-and-testing)
11. [Quick Reference](#quick-reference)

---

## System Requirements

### Hardware
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ SSD

### Software
- **OS**: Ubuntu 24.04 LTS (Noble Numbat)
- **PHP**: 8.3
- **Python**: 3.12
- **Nginx**: Latest stable

### Network
- **Static IP**: 192.168.124.133 (or your preferred IP)
- **Required Ports**:
  - 80 (HTTP - Launcher page)
  - 443 (HTTPS - Morgana Arsenal)
  - 8443 (HTTPS - MISP)
  - 8888 (Internal - Morgana backend)
  - 8080 (Internal - MISP HTTP)
  - 6666 (Internal - MISP Modules)

---

## Base System Installation

### 1. Install Ubuntu 24.04 LTS

Download and install Ubuntu 24.04 LTS. During installation:
- Create user: `morgana`
- Set hostname: `morgana-arsenal`

### 2. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Essential Packages

```bash
sudo apt install -y \
    git curl wget vim htop \
    python3 python3-pip python3-venv \
    build-essential libssl-dev libffi-dev \
    software-properties-common apt-transport-https
```

---

## Nginx Installation and Configuration

### 1. Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2. Create SSL Directory

```bash
sudo mkdir -p /etc/nginx/ssl
sudo chmod 700 /etc/nginx/ssl
```

### 3. Configure Morgana Arsenal Proxy

Create the file `/etc/nginx/sites-available/caldera-proxy`:

```bash
sudo tee /etc/nginx/sites-available/caldera-proxy > /dev/null << 'EOF'
# Nginx Reverse Proxy Configuration for Caldera + CORS
# Morgana Arsenal C2 Framework

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name 192.168.124.133;
    
    ssl_certificate /etc/nginx/ssl/caldera.crt;
    ssl_certificate_key /etc/nginx/ssl/caldera.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    location / {
        # CORS Headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, KEY, Authorization, X-Requested-With, Accept, Origin' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length, Content-Type' always;
        add_header 'Access-Control-Max-Age' '86400' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        # Handle preflight OPTIONS requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, KEY, Authorization, X-Requested-With, Accept, Origin' always;
            add_header 'Access-Control-Max-Age' '86400' always;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' '0';
            return 204;
        }
        
        # Proxy to Caldera
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
        proxy_cache_bypass $http_upgrade;
        proxy_intercept_errors off;
    }
    
    location /nginx-health {
        access_log off;
        return 200 "Nginx proxy is running\n";
        add_header Content-Type text/plain;
    }
    
    access_log /var/log/nginx/caldera-access.log;
    error_log /var/log/nginx/caldera-error.log warn;
}
EOF
```

### 4. Configure Launcher Page (Port 80)

Create the file `/etc/nginx/sites-available/launcher.conf`:

```bash
sudo tee /etc/nginx/sites-available/launcher.conf > /dev/null << 'EOF'
# Morgana VM Launcher Page - Port 80
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    root /home/morgana/morgana-arsenal/static;
    
    # Serve launcher.html as default page
    location = / {
        index launcher.html;
        try_files /launcher.html =404;
    }
    
    # Serve all HTML files from static folder
    location ~* \.html$ {
        try_files $uri =404;
    }
    
    # Static assets from Morgana Arsenal static folder
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        try_files $uri =404;
        expires 1d;
    }
    
    # All other requests redirect to HTTPS Morgana Arsenal
    location / {
        return 301 https://$host$request_uri;
    }
    
    access_log /var/log/nginx/launcher-access.log;
    error_log /var/log/nginx/launcher-error.log warn;
}
EOF
```

### 5. Configure MISP HTTP (Port 8080)

Create the file `/etc/nginx/sites-available/misp.conf`:

```bash
sudo tee /etc/nginx/sites-available/misp.conf > /dev/null << 'EOF'
server {
    listen 8080;
    server_name localhost;
    
    root /var/www/MISP/app/webroot;
    index index.php;
    
    client_max_body_size 50M;
    
    location / {
        try_files $uri $uri/ /index.php?$args;
    }
    
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
EOF
```

### 6. Configure MISP HTTPS (Port 8443)

Create the file `/etc/nginx/sites-available/misp-https.conf`:

```bash
sudo tee /etc/nginx/sites-available/misp-https.conf > /dev/null << 'EOF'
# MISP HTTPS Configuration
# Secure access to MISP on port 8443

server {
    listen 8443 ssl http2;
    listen [::]:8443 ssl http2;
    server_name 192.168.124.133 localhost;
    
    # SSL Configuration (same as Morgana Arsenal)
    ssl_certificate /etc/nginx/ssl/caldera.crt;
    ssl_certificate_key /etc/nginx/ssl/caldera.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # MISP Root Directory
    root /var/www/MISP/app/webroot;
    index index.php;
    
    client_max_body_size 50M;
    
    location / {
        # CORS Headers for Merlino integration
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, Accept, Origin' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        # Handle preflight OPTIONS
        if ($request_method = 'OPTIONS') {
            return 204;
        }
        
        try_files $uri $uri/ /index.php?$args;
    }
    
    location ~ \.php$ {
        # CORS Headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, Accept, Origin' always;
        
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param HTTPS on;
        include fastcgi_params;
    }
    
    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Health check
    location /misp-health {
        access_log off;
        return 200 "MISP HTTPS proxy is running\n";
        add_header Content-Type text/plain;
    }
    
    # Logging
    access_log /var/log/nginx/misp-access.log;
    error_log /var/log/nginx/misp-error.log warn;
}
EOF
```

### 7. Enable All Sites

```bash
# Remove default site if exists
sudo rm -f /etc/nginx/sites-enabled/default

# Enable all sites
sudo ln -sf /etc/nginx/sites-available/caldera-proxy /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/launcher.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/misp.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/misp-https.conf /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL Certificates Setup

### Generate Self-Signed Certificate (Shared by Morgana and MISP)

```bash
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
    -keyout /etc/nginx/ssl/caldera.key \
    -out /etc/nginx/ssl/caldera.crt \
    -subj "/C=IT/ST=Italy/L=Rome/O=Morgana/OU=Security/CN=192.168.124.133"

# Set proper permissions
sudo chmod 600 /etc/nginx/ssl/caldera.key
sudo chmod 644 /etc/nginx/ssl/caldera.crt
```

> **Note**: Both Morgana Arsenal (port 443) and MISP (port 8443) share the same SSL certificate.

---

## Morgana Arsenal Installation

### 1. Clone Repository

```bash
cd /home/morgana
git clone https://github.com/x3m-ai/morgana-arsenal.git
cd morgana-arsenal
```

### 2. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Initial Configuration

Edit `conf/default.yml` as needed:

```yaml
host: 0.0.0.0
port: 8888
users:
  red:
    admin: admin
  blue:
    admin: admin
```

### 5. Test Manual Start

```bash
cd /home/morgana/morgana-arsenal
source venv/bin/activate
python3 server.py --insecure --log DEBUG
```

Press `Ctrl+C` to stop after verifying it works.

---

## MISP Installation

### 1. Install Prerequisites

```bash
sudo apt install -y \
    mariadb-server mariadb-client \
    redis-server \
    php8.3 php8.3-fpm php8.3-cli php8.3-dev \
    php8.3-json php8.3-xml php8.3-mysql php8.3-opcache \
    php8.3-readline php8.3-mbstring php8.3-zip php8.3-curl \
    php8.3-redis php8.3-gd php8.3-gnupg php8.3-intl php8.3-bcmath \
    libapache2-mod-php8.3 \
    zip unzip
```

### 2. Clone MISP

```bash
sudo mkdir /var/www/MISP
sudo chown www-data:www-data /var/www/MISP
sudo -u www-data git clone https://github.com/MISP/MISP.git /var/www/MISP
cd /var/www/MISP
sudo -u www-data git checkout v2.5  # or latest stable version
```

### 3. Install MISP Dependencies

```bash
cd /var/www/MISP
sudo -u www-data git submodule update --init --recursive
cd /var/www/MISP/app
sudo -u www-data php composer.phar install --no-dev
```

### 4. Configure Database

```bash
sudo mysql -u root << EOF
CREATE DATABASE misp;
CREATE USER 'misp'@'localhost' IDENTIFIED BY 'YourSecurePassword';
GRANT ALL PRIVILEGES ON misp.* TO 'misp'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 5. Import Database Schema

```bash
sudo mysql -u misp -p misp < /var/www/MISP/INSTALL/MYSQL.sql
```

### 6. Configure MISP

```bash
cd /var/www/MISP/app/Config
sudo -u www-data cp database.default.php database.php
sudo -u www-data cp core.default.php core.php
sudo -u www-data cp config.default.php config.php
```

Edit `database.php` with your MySQL credentials.

### 7. Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/MISP
sudo chmod -R 750 /var/www/MISP
sudo chmod -R g+ws /var/www/MISP/app/tmp
sudo chmod -R g+ws /var/www/MISP/app/files
sudo chmod -R g+ws /var/www/MISP/app/files/scripts/tmp
```

### 8. Enable PHP-FPM

```bash
sudo systemctl enable php8.3-fpm
sudo systemctl start php8.3-fpm
```

---

## MISP Modules Installation

### 1. Install MISP Modules via pip

```bash
sudo pip3 install misp-modules --break-system-packages --ignore-installed typing-extensions
```

### 2. Verify Installation

```bash
which misp-modules
# Expected: /usr/local/bin/misp-modules

pip3 show misp-modules
# Shows version 3.0.5 or higher
```

### 3. Create Systemd Service for MISP Modules

Create the file `/etc/systemd/system/misp-modules.service`:

```bash
sudo tee /etc/systemd/system/misp-modules.service > /dev/null << 'EOF'
[Unit]
Description=MISP Modules - Enrichment, Import, Export modules
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
ExecStart=/usr/local/bin/misp-modules -l 127.0.0.1
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=misp-modules

[Install]
WantedBy=multi-user.target
EOF
```

### 4. Enable and Start MISP Modules

```bash
sudo systemctl daemon-reload
sudo systemctl enable misp-modules
sudo systemctl start misp-modules
```

### 5. Verify MISP Modules is Running

```bash
# Check process
ps aux | grep misp-modules

# Test API response
curl http://127.0.0.1:6666/modules

# Should return a JSON array of available modules
```

---

## Systemd Services Configuration

### 1. Create Morgana Arsenal Service

Create the file `/etc/systemd/system/morgana-arsenal.service`:

```bash
sudo tee /etc/systemd/system/morgana-arsenal.service > /dev/null << 'EOF'
[Unit]
Description=Morgana Arsenal C2 Framework
After=network.target nginx.service mysql.service
Wants=nginx.service

[Service]
Type=simple
User=morgana
Group=morgana
WorkingDirectory=/home/morgana/morgana-arsenal
Environment="PATH=/home/morgana/morgana-arsenal/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/morgana/morgana-arsenal/venv/bin/python3 /home/morgana/morgana-arsenal/server.py --insecure --log DEBUG
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=morgana-arsenal

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Enable All Services

```bash
sudo systemctl daemon-reload

# Enable services to start at boot
sudo systemctl enable nginx
sudo systemctl enable php8.3-fpm
sudo systemctl enable misp-modules
sudo systemctl enable morgana-arsenal
sudo systemctl enable redis-server
sudo systemctl enable mariadb

# Start all services
sudo systemctl start nginx
sudo systemctl start php8.3-fpm
sudo systemctl start misp-modules
sudo systemctl start morgana-arsenal
sudo systemctl start redis-server
sudo systemctl start mariadb
```

---

## Launcher Pages Setup

The launcher pages provide a web-based portal for accessing both services.

### 1. Launcher HTML Location

The launcher files should be placed in:
- `/home/morgana/morgana-arsenal/static/launcher.html`
- `/home/morgana/morgana-arsenal/static/vm-services-guide.html`

### 2. Copy HTML Files to Desktop

Copy the launcher HTML files to the desktop for easy local access:

```bash
# Copy launcher pages to desktop
cp /home/morgana/morgana-arsenal/static/launcher.html ~/Desktop/
cp /home/morgana/morgana-arsenal/static/vm-services-guide.html ~/Desktop/

# Verify files are copied
ls -la ~/Desktop/*.html
```

These HTML files can be opened directly in a browser without needing the web server.

### 3. Desktop Shortcuts (Optional)

Create desktop shortcuts for easy access:

```bash
mkdir -p ~/Desktop

# Morgana Arsenal shortcut
cat > ~/Desktop/morgana-arsenal.desktop << 'EOF'
[Desktop Entry]
Name=Morgana Arsenal
Comment=Open Morgana Arsenal C2 Framework
Exec=xdg-open https://192.168.124.133
Icon=security-high
Terminal=false
Type=Application
Categories=Security;
EOF

# MISP shortcut
cat > ~/Desktop/misp.desktop << 'EOF'
[Desktop Entry]
Name=MISP
Comment=Open MISP Threat Intelligence
Exec=xdg-open https://192.168.124.133:8443
Icon=security-medium
Terminal=false
Type=Application
Categories=Security;
EOF

chmod +x ~/Desktop/*.desktop
```

---

## Verification and Testing

### 1. Check All Services

```bash
# Check service status
sudo systemctl status nginx
sudo systemctl status php8.3-fpm
sudo systemctl status misp-modules
sudo systemctl status morgana-arsenal
sudo systemctl status redis-server
sudo systemctl status mariadb
```

### 2. Test Endpoints

```bash
# Test Nginx health
curl -k https://192.168.124.133/nginx-health
# Expected: Nginx proxy is running

# Test MISP health
curl -k https://192.168.124.133:8443/misp-health
# Expected: MISP HTTPS proxy is running

# Test Morgana Arsenal API
curl -k https://192.168.124.133/api/v2/health
# Expected: JSON response

# Test MISP Modules
curl http://127.0.0.1:6666/modules | head -c 200
# Expected: JSON array of modules

# Test Launcher page
curl -s http://192.168.124.133 | head -20
# Expected: HTML content
```

### 3. Browser Access

- **Launcher Page**: http://192.168.124.133
- **Morgana Arsenal**: https://192.168.124.133
  - Credentials: `admin` / `admin`
- **MISP**: https://192.168.124.133:8443
  - Default: `admin@admin.test` / `admin`

---

## Quick Reference

### Service Management Commands

```bash
# Morgana Arsenal
sudo systemctl start morgana-arsenal
sudo systemctl stop morgana-arsenal
sudo systemctl restart morgana-arsenal
sudo systemctl status morgana-arsenal

# MISP Modules
sudo systemctl start misp-modules
sudo systemctl stop misp-modules
sudo systemctl restart misp-modules
sudo systemctl status misp-modules

# Nginx
sudo systemctl reload nginx
sudo systemctl restart nginx

# View Logs
sudo journalctl -u morgana-arsenal -f
sudo journalctl -u misp-modules -f
sudo tail -f /var/log/nginx/caldera-access.log
sudo tail -f /var/log/nginx/misp-access.log
```

### Port Summary

| Port | Protocol | Service | Description |
|------|----------|---------|-------------|
| 80 | HTTP | Launcher | VM services launcher page |
| 443 | HTTPS | Morgana | Morgana Arsenal C2 Framework |
| 8443 | HTTPS | MISP | MISP Threat Intelligence |
| 8888 | HTTP | Internal | Morgana backend (localhost) |
| 8080 | HTTP | Internal | MISP backend (localhost) |
| 6666 | HTTP | Internal | MISP Modules API (localhost) |

### SSL Certificate Info

- **Certificate**: `/etc/nginx/ssl/caldera.crt`
- **Key**: `/etc/nginx/ssl/caldera.key`
- **Validity**: 10 years (self-signed)
- **Shared by**: Morgana Arsenal (443) and MISP (8443)

### Important Paths

```
/home/morgana/morgana-arsenal/          # Morgana Arsenal root
/home/morgana/morgana-arsenal/venv/     # Python virtual environment
/var/www/MISP/                          # MISP installation
/etc/nginx/sites-available/             # Nginx configurations
/etc/nginx/ssl/                         # SSL certificates
/etc/systemd/system/                    # Systemd service files
```

---

## Troubleshooting

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error log
sudo tail -50 /var/log/nginx/error.log
```

### Morgana Arsenal Issues

```bash
# Check logs
sudo journalctl -u morgana-arsenal -n 100

# Manual start for debugging
cd /home/morgana/morgana-arsenal
source venv/bin/activate
python3 server.py --insecure --log DEBUG
```

### MISP Issues

```bash
# Check PHP-FPM
sudo systemctl status php8.3-fpm

# Check MISP logs
sudo tail -50 /var/www/MISP/app/tmp/logs/error.log

# Check permissions
sudo chown -R www-data:www-data /var/www/MISP
```

### MISP Modules Issues

```bash
# Check if running
ps aux | grep misp-modules

# Check logs
sudo journalctl -u misp-modules -n 50

# Manual start for debugging
sudo -u www-data misp-modules -l 127.0.0.1
```

---

## Version Information

| Component | Version |
|-----------|---------|
| Ubuntu | 24.04.3 LTS (Noble Numbat) |
| PHP | 8.3.6 |
| Python | 3.12 |
| Nginx | Latest stable |
| MISP Modules | 3.0.5 |
| Morgana Arsenal | 1.0 (based on MITRE Caldera 5.3.0) |

---

**Document Version**: 1.0  
**Last Updated**: January 2, 2026  
**Author**: Morgana Arsenal Team
