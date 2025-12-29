# MISP Integration Guide - Merlino & Morgana Arsenal

**Data:** 29 Dicembre 2025  
**Stato:** ✅ Configurato e Testato  
**Versione:** 1.0

---

## 📍 Installazione MISP

- **Path:** `/var/www/MISP`
- **WebRoot:** `/var/www/MISP/app/webroot`
- **Config:** `/var/www/MISP/app/Config`
- **Database:** MySQL/MariaDB (nome: `misp`)
- **PHP Version:** 8.3

---

## 🌐 Endpoints API

### HTTP (porta 8080)
```
http://192.168.124.133:8080/events/add
```
- ✅ Funzionante
- 🔓 Non cifrato (solo per rete locale)
- Ideale per testing interno

### HTTPS (porta 8443) - **CONSIGLIATO**
```
https://192.168.124.133:8443/events/add
```
- ✅ Funzionante
- 🔒 Cifrato con SSL/TLS (stesso certificato di Morgana)
- ✅ CORS abilitato per integrazione Merlino
- ✅ Firewall configurato (porta aperta esternamente)
- **Usa questo per Merlino in produzione**

### Web Interface
```
https://192.168.124.133:8443/users/login
```

---

## 🔑 Autenticazione

### API Key
```
Authorization: 3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm
```

**Dove trovare altre API key:**
1. Login a MISP: https://192.168.124.133:8443/users/login
2. Menu: `Global Actions` → `My Profile`
3. Sezione: `Authentication key`
4. Click: `Reset Auth Key` (se necessario)

---

## 📤 Creazione Eventi da Merlino

### Headers Richiesti
```http
Authorization: 3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm
Content-Type: application/json
Accept: application/json
```

### Payload Example - Detection Rule Export
```json
{
  "Event": {
    "info": "Sentinel: Advanced Multistage Attack Detection",
    "threat_level_id": "2",
    "analysis": "1",
    "distribution": "0",
    "Tag": [
      {"name": "merlino:export"},
      {"name": "merlino:source=\"Sentinel\""},
      {"name": "merlino:name=\"Advanced Multistage Attack Detection\""},
      {"name": "misp-galaxy:mitre-attack-pattern=\"T1498\""},
      {"name": "misp-galaxy:mitre-attack-pattern=\"T1090\""},
      {"name": "misp-galaxy:mitre-attack-pattern=\"T1071\""}
    ],
    "Attribute": [
      {
        "type": "comment",
        "value": "Descrizione completa della detection rule...",
        "category": "Internal reference",
        "comment": "Merlino Catalogue Description"
      },
      {
        "type": "text",
        "value": "T1498,T1090,T1071",
        "category": "Internal reference",
        "comment": "MITRE Technique Codes"
      },
      {
        "type": "text",
        "value": "KQL: DeviceNetworkEvents | where...",
        "category": "Internal reference",
        "comment": "Detection Query"
      }
    ]
  }
}
```

### Threat Level IDs
| ID | Livello |
|----|---------|
| 1  | High    |
| 2  | Medium  |
| 3  | Low     |
| 4  | Undefined |

### Analysis Status
| ID | Stato |
|----|-------|
| 0  | Initial |
| 1  | Ongoing |
| 2  | Completed |

### Distribution
| ID | Tipo |
|----|------|
| 0  | Your organisation only |
| 1  | This community only |
| 2  | Connected communities |
| 3  | All communities |
| 4  | Sharing group |

---

## 🧪 Test Manuale

### HTTP Test
```bash
curl -X POST http://192.168.124.133:8080/events/add \
  -H "Authorization: 3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "Event": {
      "info": "TEST: Merlino Export",
      "threat_level_id": "2",
      "analysis": "1",
      "distribution": "0",
      "Tag": [
        {"name": "merlino:export"},
        {"name": "merlino:source=\"Test\""}
      ],
      "Attribute": [
        {
          "type": "comment",
          "value": "Test description",
          "category": "Internal reference",
          "comment": "Test"
        }
      ]
    }
  }'
```

### HTTPS Test (Consigliato)
```bash
curl -k -X POST https://192.168.124.133:8443/events/add \
  -H "Authorization: 3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "Event": {
      "info": "TEST: Merlino HTTPS Export",
      "threat_level_id": "2",
      "analysis": "1",
      "distribution": "0",
      "Tag": [
        {"name": "merlino:export"}
      ],
      "Attribute": [
        {
          "type": "comment",
          "value": "Test via HTTPS",
          "category": "Internal reference"
        }
      ]
    }
  }'
```

### PowerShell Test (da Windows)
```powershell
$headers = @{
    "Authorization" = "3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm"
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

$body = @{
    Event = @{
        info = "TEST: Merlino from PowerShell"
        threat_level_id = "2"
        analysis = "1"
        distribution = "0"
        Tag = @(
            @{name = "merlino:export"}
        )
        Attribute = @(
            @{
                type = "comment"
                value = "Test from PowerShell"
                category = "Internal reference"
            }
        )
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "https://192.168.124.133:8443/events/add" `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -SkipCertificateCheck
```

---

## 📊 Monitoraggio

### Script di Monitoraggio
```bash
cd /home/morgana/morgana-arsenal
./monitor-misp-integration.sh
```

**Funzionalità:**
1. **Monitor Tempo Reale** - Tail -f sui log con parsing
2. **Statistiche** - Conteggio eventi creati/errori
3. **Ultimi 20 Eventi** - Storia recente
4. **Ultimi Errori** - Troubleshooting
5. **Test API** - Test rapido HTTP/HTTPS

### Log Files
```bash
# Access log (tutte le richieste)
sudo tail -f /var/log/nginx/misp-access.log

# Error log (solo errori)
sudo tail -f /var/log/nginx/misp-error.log

# Filtra solo POST /events/add
sudo tail -f /var/log/nginx/misp-access.log | grep "POST /events/add"
```

---

## ✅ Response Attesa (Success)

### Status Code: 200
```json
{
  "Event": {
    "id": "3117",
    "uuid": "3748a04b-9681-4bf5-b220-2392160436cc",
    "date": "2025-12-29",
    "info": "TEST: Merlino Export",
    "threat_level_id": "2",
    "analysis": "1",
    "published": false,
    "Attribute": [...],
    "Tag": [...],
    "Org": {
      "name": "ORGNAME",
      "uuid": "..."
    }
  }
}
```

**Campi Importanti per Merlino:**
- `id` - Event ID in MISP (incrementale)
- `uuid` - UUID universale dell'evento
- `info` - Titolo evento (visibile in lista)
- `date` - Data creazione

---

## ❌ Gestione Errori

### 401 Unauthorized
```json
{
  "name": "Authentication failed. Please make sure you pass the API key of an API enabled user along in the Authorization header.",
  "message": "Authentication failed. Please make sure you pass the API key...",
  "url": "/events/add"
}
```
**Soluzione:** Verifica che l'API key sia corretta nell'header `Authorization`

### 403 Forbidden
```json
{
  "name": "You do not have permission to use this functionality.",
  "message": "You do not have permission to use this functionality.",
  "url": "/events/add"
}
```
**Soluzione:** L'utente associato alla API key non ha permessi di scrittura

### 400 Bad Request
```json
{
  "name": "Bad Request",
  "message": "Errors in Event",
  "url": "/events/add",
  "errors": {
    "info": ["This field cannot be left blank"]
  }
}
```
**Soluzione:** Payload JSON malformato o campi obbligatori mancanti

### 500 Internal Server Error
**Soluzione:** Controllare i log di MISP:
```bash
sudo tail -100 /var/log/nginx/misp-error.log
```

---

## 🔧 Configurazione Nginx

### File: `/etc/nginx/sites-available/misp-https.conf`
- Porta: 8443
- SSL: Certificato condiviso con Morgana
- CORS: Abilitato per Merlino
- PHP-FPM: Unix socket `/var/run/php/php8.3-fpm.sock`

### Reload Nginx dopo modifiche
```bash
sudo nginx -t              # Verifica sintassi
sudo systemctl reload nginx # Ricarica configurazione
```

---

## 🔥 Firewall (UFW)

### Porte Aperte
```
22/tcp    → SSH
80/tcp    → HTTP (redirect a HTTPS)
443/tcp   → Morgana Arsenal HTTPS
8080/tcp  → MISP HTTP (interno)
8443/tcp  → MISP HTTPS (pubblico) ✅
```

### Verifica
```bash
sudo ufw status numbered
```

---

## 📝 Attributi Disponibili

### Tipi Comuni per Merlino
| Type | Category | Uso |
|------|----------|-----|
| `comment` | Internal reference | Descrizioni, note |
| `text` | Internal reference | Testo libero, codici |
| `link` | External analysis | URL, riferimenti |
| `other` | Other | Dati non categorizzati |
| `filename` | Payload delivery | Nomi file |
| `md5` | Payload delivery | Hash MD5 |
| `sha256` | Payload delivery | Hash SHA256 |
| `ip-src` | Network activity | IP sorgente |
| `ip-dst` | Network activity | IP destinazione |
| `domain` | Network activity | Domini |
| `url` | Network activity | URL completi |

### Categorie Principali
- `Internal reference` - Dati interni, note
- `External analysis` - Link, riferimenti esterni
- `Network activity` - IoC di rete
- `Payload delivery` - File, hash
- `Artifacts dropped` - File creati/modificati
- `Persistence mechanism` - Tecniche di persistenza

---

## 🎯 Best Practices per Merlino

### 1. Tag Standardizzati
```json
"Tag": [
  {"name": "merlino:export"},                          // Sempre presente
  {"name": "merlino:source=\"<platform>\""},           // Sentinel, Defender, etc.
  {"name": "merlino:type=\"<tipo>\""},                 // detection, alert, etc.
  {"name": "merlino:severity=\"<livello>\""},          // high, medium, low
  {"name": "misp-galaxy:mitre-attack-pattern=\"T1234\""}  // MITRE ATT&CK
]
```

### 2. Attributi Minimi Consigliati
```json
"Attribute": [
  {
    "type": "comment",
    "value": "<descrizione completa>",
    "category": "Internal reference",
    "comment": "Detection Rule Description"
  },
  {
    "type": "text",
    "value": "<lista tcodes>",
    "category": "Internal reference",
    "comment": "MITRE Technique Codes"
  },
  {
    "type": "text",
    "value": "<query>",
    "category": "Internal reference",
    "comment": "Detection Query"
  }
]
```

### 3. Nomenclatura Eventi
```
Format: <Platform>: <Nome Detection>
Esempi:
- "Sentinel: Advanced Persistence Detection"
- "Defender: Suspicious PowerShell Activity"
- "Splunk: Lateral Movement Detection"
```

### 4. Error Handling in Merlino
```vba
' Esempio VBA per gestione errori
On Error GoTo ErrorHandler

Dim xhr As Object
Set xhr = CreateObject("MSXML2.ServerXMLHTTP.6.0")

xhr.Open "POST", "https://192.168.124.133:8443/events/add", False
xhr.setRequestHeader "Authorization", "3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm"
xhr.setRequestHeader "Content-Type", "application/json"
xhr.Send jsonPayload

If xhr.Status = 200 Then
    Debug.Print "✅ Event created successfully"
    ' Parse response per ottenere Event ID
Else
    Debug.Print "❌ Error: " & xhr.Status & " - " & xhr.responseText
End If

Exit Sub

ErrorHandler:
    Debug.Print "❌ Network Error: " & Err.Description
```

---

## 🚀 Test di Integrazione Completo

### 1. Verifica Connettività
```bash
curl -k https://192.168.124.133:8443/misp-health
# Output atteso: "MISP HTTPS proxy is running"
```

### 2. Test Autenticazione
```bash
curl -k https://192.168.124.133:8443/users/view/me.json \
  -H "Authorization: 3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm"
# Output atteso: JSON con dettagli utente
```

### 3. Test Creazione Evento
```bash
# Usa il comando nel paragrafo "HTTPS Test"
```

### 4. Verifica in MISP UI
```
1. Apri: https://192.168.124.133:8443
2. Login
3. Menu: Event Actions → List Events
4. Cerca eventi con tag "merlino:export"
```

---

## 📞 Supporto & Troubleshooting

### MISP non risponde
```bash
# Verifica servizi
sudo systemctl status nginx
sudo systemctl status php8.3-fpm

# Riavvia se necessario
sudo systemctl restart php8.3-fpm
sudo systemctl restart nginx
```

### Errori SSL/Certificate
Per Merlino da Windows, potrebbe essere necessario disabilitare la verifica certificato:
```vba
' In VBA
xhr.setOption 2, 13056 ' Ignora errori certificato SSL
```

### Log in Tempo Reale
```bash
# Terminal 1: Nginx access log
sudo tail -f /var/log/nginx/misp-access.log | grep --color=always "POST /events/add"

# Terminal 2: Nginx error log
sudo tail -f /var/log/nginx/misp-error.log
```

---

## 📚 Risorse Utili

- **MISP API Documentation:** https://www.misp-project.org/openapi/
- **MISP Event Format:** https://www.misp-project.org/datamodels/
- **MITRE ATT&CK:** https://attack.mitre.org/
- **Morgana Arsenal:** https://github.com/x3m-ai/morgana-arsenal

---

**Status: ✅ PRONTO PER INTEGRAZIONE CON MERLINO**

Ultimo aggiornamento: 29 Dicembre 2025  
Maintainer: Morgana Arsenal Team (@x3m-ai)
