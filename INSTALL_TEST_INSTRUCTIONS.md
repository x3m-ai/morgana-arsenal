# Morgana Arsenal + MISP Installation Test

**Version:** 1.4.1  
**Last Updated:** January 11, 2026  
**Script Version Required:** 1.4.1+

## Status: WORKING (Tested January 11, 2026)

All components installed and verified working on Ubuntu 24.04 with PHP 8.3.
CORS configured for Merlino Excel Add-in integration (both Morgana and MISP).

---

## About Morgana Arsenal

**Morgana Arsenal** is a **fork of MITRE Caldera** - the open-source adversary emulation platform. It extends Caldera with additional features and plugins for red team operations and security testing.

- **Repository**: https://github.com/x3m-ai/morgana-arsenal.git
- **Based on**: [MITRE Caldera](https://github.com/mitre/caldera)
- **Language**: Python (backend) + Vue.js (frontend)

### Key Differences from Caldera

| Feature | Caldera | Morgana Arsenal |
|---------|---------|-----------------|
| Plugins | Standard | Extended with Merlino plugin |
| Deployment | Manual | Automated installer with MISP integration |
| DNS | Not included | Local DNS (*.merlino.local) |
| SSL | Not included | Auto-generated certificates |

---

## Your Task

You need to download and run the installation script for Morgana Arsenal + MISP, then verify everything works correctly.

## What the Script Does

The script `install-morgana-misp.sh` performs a complete installation of:

1. **Morgana Arsenal** - A C2 (Command & Control) framework (fork of MITRE Caldera)
2. **MISP** - Malware Information Sharing Platform (Threat Intelligence)
3. **Local DNS** - dnsmasq for `*.merlino.local` domain resolution
4. **SSL Certificates** - Self-signed certificates with proper SANs for local domains

### Components Installed

| Component | Purpose |
|-----------|---------|
| Morgana Arsenal | C2 Framework (Python/Vue.js) |
| MISP | Threat Intelligence Platform (PHP) |
| dnsmasq | Local DNS server |
| Nginx | Reverse proxy with SSL |
| MariaDB | Database for MISP |
| Redis | Cache for MISP |
| PHP-FPM | PHP processor for MISP |
| MISP Modules | Additional MISP functionality |

### Local DNS Domains Created

| Domain | Service | Port |
|--------|---------|------|
| `morgana.merlino.local` | Morgana Arsenal | 443 (HTTPS) |
| `misp.merlino.local` | MISP | 8443 (HTTPS) |
| `launcher.merlino.local` | Launcher page | 80 (HTTP) |

### Ports Used

| Port | Protocol | Service |
|------|----------|---------|
| 53 | UDP/TCP | dnsmasq (DNS) |
| 80 | HTTP | Launcher page |
| 443 | HTTPS | Morgana Arsenal |
| 8443 | HTTPS | MISP |
| 8888 | HTTP | Morgana backend (localhost) |
| 8080 | HTTP | MISP backend (localhost) |
| 6666 | HTTP | MISP Modules (localhost) |

---

## Installation Steps

### Step 1: Download and Run the Script

```bash
# Download
curl -O https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-morgana-misp.sh

# Run (takes 10-20 minutes)
sudo bash install-morgana-misp.sh
```

Or one-liner:
```bash
curl -sL https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-morgana-misp.sh | sudo bash
```

### Step 2: Wait for Completion

The script will show progress through 13 steps:
1. Pre-flight Checks
2. Installing System Dependencies
3. Local DNS Configuration (dnsmasq)
4. SSL Certificates
5. Nginx Configuration
6. Morgana Systemd Service
7. Installing MISP
8. Configuring MariaDB
9. Configuring MISP
10. Installing MISP Modules
11. Nginx for MISP
12. Starting Services
13. Verification

---

## Verification Checklist

After installation, verify everything works:

### 1. Check All Services Are Running

```bash
sudo systemctl status dnsmasq
sudo systemctl status nginx
sudo systemctl status morgana-arsenal
sudo systemctl status misp-modules
sudo systemctl status mariadb
sudo systemctl status redis-server
```

All should show `active (running)`.

### 2. Check DNS Resolution

```bash
# Test local DNS
nslookup morgana.merlino.local 127.0.0.1
nslookup misp.merlino.local 127.0.0.1

# Should return the server's IP address
```

### 3. Check Ports Are Listening

```bash
ss -tlnp | grep -E ":(53|80|443|8443|8888|6666) "
```

Expected output should show all ports listening.

### 4. Test HTTP/HTTPS Access

```bash
# Launcher page (HTTP)
curl -s http://localhost | head -20

# Morgana Arsenal (HTTPS)
curl -sk https://localhost | head -20

# MISP (HTTPS on 8443)
curl -sk https://localhost:8443 | head -20

# MISP Modules API
curl -s http://127.0.0.1:6666/modules | head -5
```

### 5. Check SSL Certificate

```bash
# View certificate details
openssl s_client -connect localhost:443 -servername morgana.merlino.local < /dev/null 2>/dev/null | openssl x509 -noout -text | grep -A1 "Subject Alternative Name"
```

Should show:
- `DNS:morgana.merlino.local`
- `DNS:misp.merlino.local`
- `DNS:launcher.merlino.local`
- `DNS:*.merlino.local`

### 6. Check CA Certificate Is Available

```bash
curl -s http://localhost/merlino-ca.crt | head -5
```

Should show `-----BEGIN CERTIFICATE-----`

### 7. Test Morgana Arsenal API

```bash
curl -sk https://localhost/api/v2/health
```

Should return health status.

---

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Morgana Arsenal | admin | admin |
| MISP | admin@admin.test | admin |

---

## Merlino Excel Add-in Integration

The installation includes CORS configuration for **Merlino Excel Add-in** (`https://merlino-addin.x3m.ai`).

### Windows Client Setup

1. **Download CA Certificate:**
   ```
   http://<SERVER_IP>/merlino-ca.crt
   ```

2. **Install Certificate on Windows:**
   - Double-click `merlino-ca.crt`
   - Click "Install Certificate..."
   - Select "Local Machine" → Next
   - Select "Place all certificates in the following store"
   - Click "Browse" → select "Trusted Root Certification Authorities"
   - Click Next → Finish

3. **Configure hosts file** (`C:\Windows\System32\drivers\etc\hosts`):
   ```
   <SERVER_IP> morgana.merlino.local misp.merlino.local launcher.merlino.local
   ```

4. **Configure Merlino Settings:**
   | Setting | Value |
   |---------|-------|
   | Caldera URL | `https://morgana.merlino.local` |
   | Caldera API Key | `ADMIN123` |
   | MISP URL | `https://misp.merlino.local:8443` |
   | MISP API Key | (get from MISP web UI) |

### CORS Verification

Test from the server:
```bash
# Morgana CORS
curl -ksI -X OPTIONS -H "Origin: https://merlino-addin.x3m.ai" \
  https://127.0.0.1/api/v2/abilities | grep -i access-control

# MISP CORS
curl -ksI -X OPTIONS -H "Origin: https://merlino-addin.x3m.ai" \
  https://127.0.0.1:8443/servers/getVersion | grep -i access-control
```

Expected headers:
```
access-control-allow-origin: https://merlino-addin.x3m.ai
access-control-allow-methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
access-control-allow-credentials: true
```

---

## Expected Final Output

At the end of installation, you should see:

```
════════════════════════════════════════
  Installation Complete!
════════════════════════════════════════

Morgana Arsenal + MISP installed successfully!

Local DNS Domains:
────────────────────────────────────
  DNS Server:      <YOUR_IP>
  Morgana:         morgana.merlino.local
  MISP:            misp.merlino.local
  Launcher:        launcher.merlino.local

Access URLs (via DNS):
────────────────────────────────────
  Launcher:        http://launcher.merlino.local
  Morgana Arsenal: https://morgana.merlino.local
  MISP:            https://misp.merlino.local:8443
```

---

## Troubleshooting

### Installation Log File

**IMPORTANT**: The installation script creates a detailed log file in the **same directory where the script is executed**:

```
./morgana-install.log
```

For example:
- If you run `sudo bash install-morgana-misp.sh` from `/home/ubuntu/`, the log will be at `/home/ubuntu/morgana-install.log`
- If you run via curl from `/tmp/`, the log will be at `/tmp/morgana-install.log`

This log contains:
- Timestamps for every step and substep
- Commands being executed (`[CMD]` prefix)
- Debug information (`[DEBUG]` prefix)  
- Warnings and errors with line numbers

**If installation fails**, check the log:
```bash
# View entire log (adjust path based on where you ran the script)
cat ./morgana-install.log

# View last 100 lines
tail -100 ./morgana-install.log

# Search for errors
grep -i "error\|fail\|warn" ./morgana-install.log

# Watch log in real-time during installation (in another terminal)
tail -f ./morgana-install.log
```

### Fixed Issues (already resolved in script)

The following issues were identified during testing and have been fixed in the installation script:

**v1.4.1 Fixes:**
1. **CORS for MISP**: Added CORS headers for MISP (port 8443) to allow Merlino Excel Add-in to call MISP API

**v1.4.0 Fixes:**
1. **CORS for Morgana**: Added CORS headers for Morgana (port 443) to allow Merlino Excel Add-in (`https://merlino-addin.x3m.ai`) to call Morgana API. Supports preflight OPTIONS requests with proper headers.

**v1.3.1 Fixes:**
1. **Composer install subshell**: Fixed `${MISP_DIR}` variable not available in bash subshell - now uses direct `cd` instead of subshell with `COMPOSER_ALLOW_SUPERUSER=1`

**v1.3.0 Fixes:**
1. **Nginx caldera-proxy config**: Fixed missing `error_log` and closing `}` in heredoc - this was causing nginx to fail with "unknown directive log_debug" error
2. **launcher.conf CA cert**: Added proper location block for `/merlino-ca.crt` with Content-Type header
3. **Composer installation**: Robust installation with proper cache directory for www-data user, verified autoload.php creation
4. **PHP-FPM restart**: Added restart after Composer install to reload new dependencies
5. **Nginx config validation**: Added `nginx -t` test before restart with diagnostic output on failure

**v1.2.0 Fixes:**
1. **Apache2 conflict**: Disabled Apache2 (installed as PHP dependency) which conflicts with Nginx on port 80
2. **DNS gateway detection**: Uses local gateway IP for upstream DNS instead of hardcoded 8.8.8.8

**v1.1.0 Fixes:**
1. **IP Detection**: Script now prefers local/private IP for LAN DNS instead of public IP
2. **MISP Branch**: Uses branch `2.5` (compatible with PHP 8.3) instead of old `2.4`
3. **Missing `bootstrap.php`**: Now automatically copied from `bootstrap.default.php`
4. **Database credentials**: Properly replaces placeholder `'db login'` and `'db password'`
5. **Morgana `conf/agents.yml`**: Created automatically if missing
6. **Morgana `conf/payloads.yml`**: Created automatically if missing
7. **Morgana log directory**: Creates `/home/$USER/caldera/` for debug logs

### If dnsmasq fails to start

```bash
# Check if systemd-resolved is blocking port 53
sudo lsof -i :53

# If so, the script should have handled it, but you can manually:
sudo systemctl stop systemd-resolved
sudo systemctl restart dnsmasq
```

### If Morgana Arsenal doesn't start

```bash
# Check logs
sudo journalctl -u morgana-arsenal -n 50

# Check if venv exists
ls -la /home/ubuntu/morgana-arsenal/venv/
```

### If MISP shows errors

```bash
# Check PHP-FPM
sudo systemctl status php*-fpm

# Check MISP logs
sudo tail -50 /var/log/nginx/misp-error.log
```

---

## Report Back

Please run all verification steps and report:

1. All service statuses (running/stopped)
2. DNS resolution working? (yes/no)
3. All ports listening? (list which ones)
4. Can access Morgana web UI? (yes/no)
5. Can access MISP web UI? (yes/no)
6. Any errors encountered

---

## Test Results (January 11, 2026)

### Services Status
| Service | Status |
|---------|--------|
| dnsmasq | ✅ Running |
| nginx | ✅ Running |
| morgana-arsenal | ✅ Running |
| misp-modules | ✅ Running |
| mariadb | ✅ Running |
| redis-server | ✅ Running |
| php8.3-fpm | ✅ Running |

### URL Access Test
| URL | Status |
|-----|--------|
| `http://launcher.merlino.local` | ✅ 200 OK |
| `https://morgana.merlino.local` | ✅ 200 OK |
| `https://misp.merlino.local:8443` | ✅ 302 → Login |

### DNS Resolution
- `morgana.merlino.local` → 192.168.124.131 ✅
- `misp.merlino.local` → 192.168.124.131 ✅
- `launcher.merlino.local` → 192.168.124.131 ✅

**All tests passed!**

Thank you!
