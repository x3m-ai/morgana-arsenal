# Simulatore di Agenti Fittizi - Morgana Arsenal

Script Python per creare e mantenere agenti fittizi nel sistema Morgana Arsenal, permettendo di testare scenari multi-agent senza bisogno di installare agenti veri su macchine target.

## Funzionalità

- ✅ Crea agenti con hostname realistici per Windows, Linux e macOS
- ✅ Genera PAW univoci assegnati dal server
- ✅ Supporta gruppi personalizzati (red, blue, production, dev, test)
- ✅ Supporta diverse piattaforme (windows, linux, darwin)
- ✅ Può mantenere gli agenti "alive" con update periodici
- ✅ Utilizza API REST per massima compatibilità

## Prerequisiti

- Server Morgana Arsenal in esecuzione su `http://localhost:8888`
- Python 3.x con librerie: `aiohttp`, `asyncio`

## Installazione Dipendenze

```bash
pip3 install aiohttp
```

## Utilizzo Base

### Creare agenti (senza beacon continui)

```bash
# Crea 5 agenti random
python3 simulate_agents.py --create-only

# Crea 10 agenti in gruppi specifici
python3 simulate_agents.py --count 10 --groups "red,blue" --create-only

# Crea 8 agenti solo Windows e Linux
python3 simulate_agents.py --count 8 --platforms "windows,linux" --create-only

# Crea 12 agenti con gruppi e piattaforme specifiche
python3 simulate_agents.py --count 12 --groups "red,blue,production" --platforms "windows,linux" --create-only
```

### Mantenere agenti con update periodici

```bash
# Crea 5 agenti e mantienili con update ogni 30 secondi
python3 simulate_agents.py --count 5 --groups "red,blue"

# Update ogni 60 secondi
python3 simulate_agents.py --count 5 --beacon-interval 60

# Interrompi con Ctrl+C
```

## Opzioni CLI

| Opzione | Default | Descrizione |
|---------|---------|-------------|
| `--count` | 5 | Numero di agenti da creare |
| `--groups` | random | Gruppi separati da virgola (es: "red,blue,production") |
| `--platforms` | random | Piattaforme separate da virgola (es: "windows,linux") |
| `--create-only` | false | Crea agenti una volta sola senza update |
| `--beacon-interval` | 30 | Intervallo update in secondi |
| `--server` | http://localhost:8888 | URL del server Caldera |
| `--api-key` | ADMIN123 | Chiave API per autenticazione |

## Esempi Pratici

### Scenario 1: Test Red Team vs Blue Team

```bash
# Crea 10 agenti red team (attaccanti)
python3 simulate_agents.py --count 10 --groups "red" --create-only

# Crea 5 agenti blue team (difensori)
python3 simulate_agents.py --count 5 --groups "blue" --create-only
```

### Scenario 2: Test Multi-Platform

```bash
# Mix di Windows, Linux e macOS
python3 simulate_agents.py --count 15 --platforms "windows,linux,darwin" --create-only
```

### Scenario 3: Test Environment Segregation

```bash
# Agenti production
python3 simulate_agents.py --count 8 --groups "production" --platforms "linux" --create-only

# Agenti development
python3 simulate_agents.py --count 5 --groups "dev" --platforms "windows,linux" --create-only

# Agenti test
python3 simulate_agents.py --count 3 --groups "test" --create-only
```

### Scenario 4: Mantenimento Continuo

```bash
# Crea e mantieni 10 agenti (simula beacon reali)
python3 simulate_agents.py --count 10 --groups "red,blue" --beacon-interval 45
# Premi Ctrl+C per fermare
```

## Caratteristiche degli Agenti Generati

### Hostname Realistici

- **Windows**: `WIN-DESKTOP-{num}`, `WIN-SRV-{num}`, `WORKSTATION-{num}`, `DC-{num}`
- **Linux**: `ubuntu-{num}`, `centos-{num}`, `debian-{num}`, `kali-{num}`
- **macOS**: `macbook-{num}`, `imac-{num}`, `mac-mini-{num}`

### Executor Appropriati

- **Windows**: `cmd`, `psh`, `pwsh`
- **Linux**: `sh`, `bash`
- **macOS**: `sh`, `bash`, `zsh`

### Privilege Levels

- **Windows**: User, Elevated, SYSTEM (random)
- **Linux/macOS**: User, root (random)

## Verifica Agenti Creati

### Via API REST

```bash
# Lista tutti gli agenti
curl -H "KEY: ADMIN123" "http://localhost:8888/api/v2/agents" | jq '.[] | {paw, host, platform, group}'

# Conta agenti per gruppo
curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/agents" | jq -r '.[].group' | sort | uniq -c
```

### Via Web UI

1. Apri browser: `http://localhost:8888`
2. Login: `admin` / `admin`
3. Vai su **Campaigns → Agents**
4. Dovresti vedere tutti gli agenti fittizi

## Pulizia Agenti

### Elimina tutti gli agenti fittizi

```bash
# Lista PAWs degli agenti fake (hostname contiene pattern)
curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/agents" | jq -r '.[] | select(.host | test("WIN-|ubuntu-|kali-|centos-|debian-|macbook-|imac-|DC-")) | .paw'

# Elimina un agente specifico
curl -H "KEY: ADMIN123" -X DELETE "http://localhost:8888/api/v2/agents/{PAW}"
```

### Script di pulizia rapida

```bash
# Elimina tutti gli agenti dal gruppo 'test'
for paw in $(curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/agents" | jq -r '.[] | select(.group=="test") | .paw'); do
    echo "Deleting $paw..."
    curl -H "KEY: ADMIN123" -X DELETE "http://localhost:8888/api/v2/agents/$paw"
done
```

## Note Tecniche

### API REST Utilizzata

Lo script usa l'endpoint `/api/v2/agents` invece del classico `/beacon` per maggiore affidabilità:

```http
POST /api/v2/agents
Headers:
  KEY: ADMIN123
  Content-Type: application/json
Body:
  {
    "server": "http://localhost:8888",
    "group": "red",
    "host": "fake-host",
    "platform": "linux",
    "executors": ["sh", "bash"],
    ...
  }
```

### Differenze con Agenti Reali

Gli agenti fittizi:
- ✅ Appaiono nella UI come agenti normali
- ✅ Possono essere assegnati a operations
- ✅ Possono essere organizzati in gruppi
- ⚠️ NON eseguono realmente abilities (nessuna macchina target)
- ⚠️ I links creati falliranno (nessun risultato reale)
- ⚠️ `last_seen` timestamp può essere aggiornato con `--beacon-interval`

### Casi d'Uso Ideali

1. **Test UI**: Verificare rendering con molti agenti
2. **Test Gruppi**: Testare operazioni su gruppi diversi
3. **Test Adversaries**: Verificare distribuzione abilities multi-platform
4. **Performance**: Stress test con centinaia di agenti
5. **Demo**: Mostrare Morgana Arsenal senza installare agenti veri

## Troubleshooting

### Errore "HTTP 500" o "Connection refused"

- Verifica che il server Morgana Arsenal sia in esecuzione
- Controlla che l'URL sia corretto: `http://localhost:8888`

### Errore "HTTP 401 Unauthorized"

- Verifica l'API key nel file `conf/default.yml`
- Usa `--api-key "TUA_CHIAVE"` se diversa da `ADMIN123`

### Agenti non visibili nella UI

- Fai refresh del browser (Ctrl+Shift+R)
- Verifica con API: `curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents`
- Controlla i log del server: `tail -f caldera-debug.log`

### "Unknown field" error

- Assicurati che i campi nel profilo siano corretti
- Lo script è aggiornato per usare `sleep_min`/`sleep_max` non `sleep`

## Esempi Output

```
🤖 Creating 6 fake agents...
   Groups: ['red', 'blue', 'production']
   Platforms: random

✅ Created agent 1/6: rcdbxm (windows/red) - DC-729
✅ Created agent 2/6: hvhfjh (linux/blue) - centos-185
✅ Created agent 3/6: bnzdbx (linux/blue) - ubuntu-272
✅ Created agent 4/6: cyfzqr (windows/production) - WIN-DESKTOP-528
✅ Created agent 5/6: mnbush (linux/blue) - ubuntu-259
✅ Created agent 6/6: vbmcai (darwin/blue) - imac-651

✅ Successfully created 6 agents!
```

## Contributi

Per miglioramenti o bug report, modifica il file `simulate_agents.py` o contatta il team Morgana Arsenal.

## Licenza

Parte di Morgana Arsenal - Apache 2.0 License
