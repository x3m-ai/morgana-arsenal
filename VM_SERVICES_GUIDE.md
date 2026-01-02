# Morgana VM Services Guide

This document describes the services running on this Ubuntu VM, their locations, logs, and how to manage them.

---

## Access Credentials

| System | Username | Password |
|--------|----------|----------|
| **Ubuntu VM (SSH/Console)** | `morgana` | `morgana` |
| **Morgana Arsenal (Web UI)** | `morgana` | `morgana` |
| **MISP (Web UI)** | `admin@admin.test` | `admin` |

---

## Services Overview

| Service | Description | Port | Auto-Start |
|---------|-------------|------|------------|
| **Nginx** | Reverse proxy with SSL | 443, 8443 | Yes |
| **Morgana Arsenal** | C2 Framework (Caldera fork) | 8888 (internal) | Yes |
| **MISP** | Threat Intelligence Platform | 8080 (internal) | Yes |
| **MISP Workers** | Background job processors | N/A | Yes |
| **MISP Modules** | Enrichment/Import/Export modules | 6666 (internal) | Yes |
| **MySQL** | Database server | 3306 | Yes |
| **Redis** | Cache/Queue server | 6379 | Yes |
| **PHP-FPM 8.3** | PHP processor for MISP | N/A | Yes |

---

## 1. Morgana Arsenal (C2 Framework)

### Description
Morgana Arsenal is a professional Command & Control framework derived from MITRE Caldera v5.3.0. It provides red team simulation capabilities with custom Merlino agent support.

### Locations
| Component | Path |
|-----------|------|
| **Application** | `/home/morgana/morgana-arsenal/` |
| **Main Script** | `/home/morgana/morgana-arsenal/server.py` |
| **Virtual Environment** | `/home/morgana/morgana-arsenal/venv/` |
| **Configuration** | `/home/morgana/morgana-arsenal/conf/default.yml` |
| **Data/Payloads** | `/home/morgana/morgana-arsenal/data/` |
| **Plugins** | `/home/morgana/morgana-arsenal/plugins/` |
| **Frontend (Magma)** | `/home/morgana/morgana-arsenal/plugins/magma/` |

### Logs
| Log | Path | Description |
|-----|------|-------------|
| **Debug Log** | `/home/morgana/morgana-arsenal/caldera-debug.log` | Detailed debug output |
| **Live Log** | `/home/morgana/morgana-arsenal/caldera-live.log` | Operational events |
| **Systemd Journal** | `journalctl -u morgana-arsenal` | Service logs |

### Access URLs
- **Web UI**: https://192.168.124.133 (via Nginx)
- **Direct**: http://localhost:8888 (internal only)
- **Credentials**: morgana / morgana (configure in `conf/default.yml`)

### Service Management
```bash
# Status
sudo systemctl status morgana-arsenal

# Start/Stop/Restart
sudo systemctl start morgana-arsenal
sudo systemctl stop morgana-arsenal
sudo systemctl restart morgana-arsenal

# View logs
journalctl -u morgana-arsenal -f
tail -f /home/morgana/morgana-arsenal/caldera-debug.log

# Manual start (for debugging)
cd /home/morgana/morgana-arsenal
./venv/bin/python3 server.py --insecure --log DEBUG
```

---

## 2. MISP (Threat Intelligence Platform)

### Description
MISP (Malware Information Sharing Platform) is an open-source threat intelligence platform for sharing, storing, and correlating Indicators of Compromise (IOCs).

### Locations
| Component | Path |
|-----------|------|
| **Application** | `/var/www/MISP/` |
| **Configuration** | `/var/www/MISP/app/Config/` |
| **Database Config** | `/var/www/MISP/app/Config/database.php` |
| **Workers** | `/var/www/MISP/app/Console/worker/` |
| **Uploads** | `/var/www/MISP/app/files/` |
| **Temp Files** | `/var/www/MISP/app/tmp/` |

### Logs
| Log | Path | Description |
|-----|------|-------------|
| **Error Log** | `/var/www/MISP/app/tmp/logs/error.log` | Application errors |
| **Debug Log** | `/var/www/MISP/app/tmp/logs/debug.log` | Debug information |
| **Exec Log** | `/var/www/MISP/app/tmp/logs/exec-errors.log` | Execution errors |
| **Workers Journal** | `journalctl -u misp-workers` | Worker service logs |
| **PHP-FPM Log** | `/var/log/php8.3-fpm.log` | PHP errors |
| **Nginx Access** | `/var/log/nginx/misp-access.log` | HTTP access log |
| **Nginx Error** | `/var/log/nginx/misp-error.log` | HTTP errors |

### Access URLs
- **HTTPS**: https://192.168.124.133:8443 (via Nginx)
- **HTTP**: http://localhost:8080 (internal only)
- **Credentials**: admin@admin.test / admin
- **API Key**: `3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm`

### Service Management
```bash
# MISP Workers Status
sudo systemctl status misp-workers

# Start/Stop/Restart Workers
sudo systemctl start misp-workers
sudo systemctl stop misp-workers
sudo systemctl restart misp-workers

# View worker logs
journalctl -u misp-workers -f

# PHP-FPM (required for MISP web)
sudo systemctl status php8.3-fpm
sudo systemctl restart php8.3-fpm

# View MISP application logs
tail -f /var/www/MISP/app/tmp/logs/error.log
tail -f /var/www/MISP/app/tmp/logs/debug.log

# Manual worker start (for debugging)
cd /var/www/MISP/app/Console/worker
sudo -u www-data ./start.sh
```

### MISP Modules
```bash
# Status
sudo systemctl status misp-modules

# Start/Stop/Restart
sudo systemctl start misp-modules
sudo systemctl stop misp-modules
sudo systemctl restart misp-modules

# View logs
journalctl -u misp-modules -f

# Manual start (for debugging)
sudo -u www-data /usr/local/bin/misp-modules -l 127.0.0.1
```

---

## 3. Nginx (Reverse Proxy)

### Description
Nginx serves as the SSL/TLS termination point and reverse proxy for both Morgana Arsenal and MISP.

### Locations
| Component | Path |
|-----------|------|
| **Main Config** | `/etc/nginx/nginx.conf` |
| **Sites Available** | `/etc/nginx/sites-available/` |
| **Sites Enabled** | `/etc/nginx/sites-enabled/` |
| **SSL Certificates** | `/etc/nginx/ssl/` |
| **Morgana Config** | `/etc/nginx/sites-available/caldera` |
| **MISP HTTPS Config** | `/etc/nginx/sites-available/misp-https.conf` |

### SSL Certificates
| File | Path |
|------|------|
| **Certificate** | `/etc/nginx/ssl/caldera.crt` |
| **Private Key** | `/etc/nginx/ssl/caldera.key` |

### Logs
| Log | Path |
|-----|------|
| **Access Log** | `/var/log/nginx/access.log` |
| **Error Log** | `/var/log/nginx/error.log` |
| **MISP Access** | `/var/log/nginx/misp-access.log` |
| **MISP Error** | `/var/log/nginx/misp-error.log` |

### Service Management
```bash
# Status
sudo systemctl status nginx

# Start/Stop/Restart
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx

# Test configuration (before restart)
sudo nginx -t

# Reload (no downtime)
sudo systemctl reload nginx

# View logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

---

## 4. Database Services

### MySQL
```bash
# Status
sudo systemctl status mysql

# Start/Stop/Restart
sudo systemctl start mysql
sudo systemctl stop mysql
sudo systemctl restart mysql

# Logs
tail -f /var/log/mysql/error.log

# Connect to MISP database
mysql -u misp -p misp
```

### Redis
```bash
# Status
sudo systemctl status redis-server

# Start/Stop/Restart
sudo systemctl start redis-server
sudo systemctl stop redis-server
sudo systemctl restart redis-server

# Logs
journalctl -u redis-server -f

# Test connection
redis-cli ping
```

---

## Auto-Start Configuration

All services are configured to start automatically at boot via systemd.

### Verify Auto-Start Status
```bash
# Check which services are enabled
systemctl is-enabled nginx morgana-arsenal misp-workers misp-modules php8.3-fpm mysql redis-server
```

### Enable/Disable Auto-Start
```bash
# Enable at boot
sudo systemctl enable morgana-arsenal
sudo systemctl enable misp-workers
sudo systemctl enable misp-modules

# Disable at boot
sudo systemctl disable morgana-arsenal
sudo systemctl disable misp-workers
sudo systemctl disable misp-modules
```

### Boot Order
The services start in this order (defined in systemd unit files):
1. **mysql** (database)
2. **redis-server** (cache)
3. **php8.3-fpm** (PHP processor)
4. **nginx** (web server)
5. **morgana-arsenal** (C2 framework, after nginx)
6. **misp-modules** (enrichment modules, after redis)
7. **misp-workers** (after mysql and redis)

---

## Quick Troubleshooting

### Check All Services Status
```bash
sudo systemctl status nginx morgana-arsenal misp-workers misp-modules php8.3-fpm mysql redis-server --no-pager
```

### Restart Everything
```bash
sudo systemctl restart mysql redis-server php8.3-fpm nginx morgana-arsenal misp-modules misp-workers
```

### Common Issues

#### Morgana Arsenal 502 Bad Gateway
```bash
# Check if Python server is running
ps aux | grep server.py
# Restart service
sudo systemctl restart morgana-arsenal
# Check logs
journalctl -u morgana-arsenal -n 50
```

#### MISP Not Loading
```bash
# Check PHP-FPM
sudo systemctl status php8.3-fpm
# Check Nginx MISP config
sudo nginx -t
# Check MISP logs
tail -20 /var/www/MISP/app/tmp/logs/error.log
```

#### Port Already in Use
```bash
# Check what's using a port
sudo lsof -i :8888
sudo lsof -i :8080
# Kill process manually if needed
sudo kill -9 <PID>
```

---

## Network Ports Summary

| Port | Protocol | Service | Access |
|------|----------|---------|--------|
| 22 | TCP | SSH | External |
| 80 | TCP | HTTP (redirect) | External |
| 443 | TCP | HTTPS (Morgana) | External |
| 3306 | TCP | MySQL | Internal |
| 6379 | TCP | Redis | Internal |
| 6666 | TCP | MISP Modules | Internal |
| 8080 | TCP | MISP HTTP | Internal |
| 8443 | TCP | MISP HTTPS | External |
| 8888 | TCP | Morgana HTTP | Internal |

### Firewall Status
```bash
sudo ufw status
```

---

## Systemd Service Files

| Service | File |
|---------|------|
| Morgana Arsenal | `/etc/systemd/system/morgana-arsenal.service` |
| MISP Workers | `/etc/systemd/system/misp-workers.service` |
| MISP Modules | `/etc/systemd/system/misp-modules.service` |
| Nginx | `/lib/systemd/system/nginx.service` |
| MySQL | `/lib/systemd/system/mysql.service` |
| Redis | `/lib/systemd/system/redis-server.service` |
| PHP-FPM | `/lib/systemd/system/php8.3-fpm.service` |

### After Editing Service Files
```bash
sudo systemctl daemon-reload
sudo systemctl restart <service-name>
```

---

**Last Updated**: December 31, 2025  
**VM IP**: 192.168.124.133  
**Maintainer**: Morgana (@x3m-ai)
