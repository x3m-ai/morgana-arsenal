# Morgana Arsenal + MISP Installation Test

## Your Task

You need to download and run the installation script for Morgana Arsenal + MISP, then verify everything works correctly.

## What the Script Does

The script `install-morgana-misp.sh` performs a complete installation of:

1. **Morgana Arsenal** - A C2 (Command & Control) framework based on MITRE Caldera
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

Thank you!
