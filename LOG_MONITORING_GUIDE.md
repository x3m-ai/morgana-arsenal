# Guida al Monitoraggio dei Log - Morgana Arsenal

## File di Log Principali

### 1. **caldera.log** - Log dettagliato principale
- **Percorso**: `/home/morgana/morgana-arsenal/caldera.log`
- **Contenuto**: Tutti i log del server con livello DEBUG/INFO
- **Quando usare**: Per debug dettagliato di operazioni, beacons, abilities

### 2. **caldera-output.log** - Output del server
- **Percorso**: `/home/morgana/morgana-arsenal/caldera-output.log`
- **Contenuto**: Output stdout/stderr del processo server.py
- **Quando usare**: Per vedere startup, errori fatali, banner

### 3. **caldera-live.log** - Log operazionale
- **Percorso**: `/home/morgana/morgana-arsenal/caldera-live.log`
- **Contenuto**: Eventi high-level (agent check-ins, operation changes)
- **Quando usare**: Per overview rapido dello stato operativo

### 4. **log_agent_merlino.log** - Log dell'agent Merlino
- **Percorso**: `/home/morgana/morgana-arsenal/log_agent_merlino.log`
- **Contenuto**: Output dell'agent sul target Windows
- **Quando usare**: Per debug lato agent (beacon, instruction execution)

---

## Log Migliorati per Beacon e Instructions

### Cosa è stato aggiunto

Ho migliorato il logging in **2 file critici**:

#### 1. **app/contacts/contact_http.py** (Gestione Beacon)
Ogni beacon ora logga:
- ✅ Profilo completo dell'agent (paw, platform, host, **group**)
- ✅ Numero di istruzioni restituite
- ✅ Dettagli di ogni istruzione (ID, Ability, Executor, Command)
- ✅ Lunghezza della risposta in bytes
- ✅ Separatori visivi per ogni beacon

#### 2. **app/service/contact_svc.py** (Logica di Tasking)
Ogni richiesta di istruzioni logga:
- ✅ Agent details (paw, **group**)
- ✅ Tutte le operations attive (nome, ID, **group**, stato, chain length)
- ✅ Matching tra agent.group e op.group (con check esatti)
- ✅ Perché un agent viene aggiunto o meno a un'operation
- ✅ Chain links e agent links disponibili

---

## Comandi Utili per Monitoraggio

### Monitoraggio in Tempo Reale (CONSIGLIATO)

```bash
# Script colorato che filtra solo i log rilevanti
./monitor-agent-beacons.sh
```

Questo script mostra SOLO:
- `[BEACON]` in verde
- `[GET_INSTRUCTIONS]` in blu
- `[ADD_AGENT]` in magenta
- `[HEARTBEAT]` in cyan
- Simboli colorati: ✓ (verde), ✗ (rosso), ⚠ (giallo)

### Monitor Manuale

```bash
# Segui tutti i log in tempo reale
tail -f caldera.log

# Filtra solo beacon e istruzioni
tail -f caldera.log | grep -E '\[BEACON\]|\[GET_INSTRUCTIONS\]|\[ADD_AGENT\]'

# Cerca un agent specifico
tail -f caldera.log | grep "gtbtqh"

# Cerca operation matching
tail -f caldera.log | grep "MATCH\|NO MATCH"
```

### Analisi Post-Mortem

```bash
# Ultimi 100 beacon
tail -100 caldera.log | grep '\[BEACON\]'

# Vedi tutte le operations controllate
grep '\[GET_INSTRUCTIONS\]' caldera.log | grep "Op:"

# Vedi problemi di matching agent-operation
grep 'NO MATCH\|did NOT match ANY' caldera.log

# Errori generali
grep -i error caldera.log | tail -20
```

---

## Esempio di Log Migliorato

### Beacon Ricevuto
```
2026-01-20 08:45:12 INFO [BEACON] ============== NEW BEACON ==============
2026-01-20 08:45:12 INFO [BEACON] Received 512 bytes from 192.168.124.1
2026-01-20 08:45:12 INFO [BEACON] Decoded profile: paw=gtbtqh, platform=windows, host=W11-MERLINO-01, group=red
```

### Agent Matching con Operations
```
2026-01-20 08:45:12 INFO [ADD_AGENT] ===== Checking agent gtbtqh (group="red") against 5 operations =====
2026-01-20 08:45:12 INFO [ADD_AGENT] Checking op "Test Operation Red Group" (id=a057..., group="red", state=running)
2026-01-20 08:45:12 INFO [ADD_AGENT] ✓ EXACT MATCH! agent.group="red" == op.group="red"
2026-01-20 08:45:12 INFO [ADD_AGENT] Checking op "Other Operation" (id=b234..., group="blue", state=running)
2026-01-20 08:45:12 INFO [ADD_AGENT] ✗ NO MATCH: agent.group="red" != op.group="blue"
```

### Istruzioni Restituite
```
2026-01-20 08:45:12 INFO [GET_INSTRUCTIONS] ===== Getting instructions for agent gtbtqh (group=red) =====
2026-01-20 08:45:12 INFO [GET_INSTRUCTIONS] Found 5 active operations
2026-01-20 08:45:12 INFO [GET_INSTRUCTIONS] Op: Test Operation Red Group (id=a057..., group="red", state=running, chain_len=23)
2026-01-20 08:45:12 INFO [GET_INSTRUCTIONS] Found 1 matching chain links for agent gtbtqh
2026-01-20 08:45:12 INFO [GET_INSTRUCTIONS] Chain link: ability=Discover Process, executor=psh, command=Get-Process | Out-String...
2026-01-20 08:45:12 INFO [BEACON] Instructions details:
2026-01-20 08:45:12 INFO   [1] ID=abc123, Ability=921055f4-5970-4707-909e, Executor=psh
2026-01-20 08:45:12 INFO [BEACON] Response summary: paw=gtbtqh, sleep=7, instructions=1, response_length=1024 bytes
2026-01-20 08:45:12 INFO [BEACON] ============== END BEACON ==============
```

---

## Debug Flow Completo

### Problema: "Agent non riceve istruzioni"

**Step 1**: Verifica che l'agent faccia beacon
```bash
tail -f caldera.log | grep "Decoded profile"
# Dovresti vedere: paw=xxx, platform=xxx, host=xxx, group=xxx
```

**Step 2**: Verifica il gruppo dell'agent
```bash
curl -k -s -X GET "http://localhost:8888/api/v2/agents" -H "KEY: ADMIN123" | \
  python3 -c "import sys, json; [print(f\"{a['paw']}: group={a['group']}\") for a in json.load(sys.stdin)]"
```

**Step 3**: Verifica i gruppi delle operations
```bash
curl -k -s -X GET "http://localhost:8888/api/v2/operations" -H "KEY: ADMIN123" | \
  python3 -c "import sys, json; [print(f\"{o['name']}: group='{o['group']}' state={o['state']}\") for o in json.load(sys.stdin)]"
```

**Step 4**: Controlla il matching nei log
```bash
grep "MATCH\|NO MATCH" caldera.log | tail -20
# Dovresti vedere "✓ EXACT MATCH!" per l'agent
```

**Step 5**: Verifica le istruzioni generate
```bash
grep "GET_INSTRUCTIONS.*Total instructions" caldera.log | tail -10
# Dovresti vedere: "Total instructions for xxx: N" (N > 0)
```

---

## Livelli di Log del Server

Il server può essere avviato con diversi livelli:

```bash
# INFO - Raccomandato per produzione (mostra i nostri log migliorati)
python3 server.py --insecure --log INFO

# DEBUG - Molto verbose (include anche log interni di Caldera)
python3 server.py --insecure --log DEBUG

# WARNING - Solo warning ed errori (troppo poco)
python3 server.py --insecure --log WARNING
```

**Raccomandazione**: Usa `--log INFO` per un buon bilanciamento tra dettaglio e rumore.

---

## Troubleshooting Comune

### 1. Non vedo i nuovi log migliorati
**Causa**: Server non riavviato dopo le modifiche  
**Soluzione**:
```bash
pkill -INT -f "python3.*server.py"
sleep 2
python3 server.py --insecure --log INFO > caldera-output.log 2>&1 &
```

### 2. Agent non matcha con operation
**Causa**: Gruppo diverso tra agent e operation  
**Soluzione**: Ricrea operation con gruppo corretto
```bash
curl -k -X POST "http://localhost:8888/api/v2/operations" \
  -H "KEY: ADMIN123" -H "Content-Type: application/json" \
  -d '{
    "name": "My Operation",
    "group": "red",  # ← DEVE corrispondere al gruppo agent
    "adversary": {"adversary_id": "xxx"},
    "state": "running",
    "autonomous": 1
  }'
```

### 3. Operation ha group=""
**Causa**: Campo `group` non specificato nella POST  
**Fix**: Vedi soluzione sopra, specifica SEMPRE `"group": "red"`

### 4. Log file troppo grande
**Soluzione**: Ruota i log
```bash
# Archivia e svuota
mv caldera.log caldera.log.$(date +%Y%m%d_%H%M%S)
touch caldera.log

# Oppure tronca (più veloce)
> caldera.log
```

---

## Conclusione

Con questi log migliorati puoi vedere **esattamente**:
1. Quando un agent fa beacon
2. Quale gruppo ha l'agent
3. Quali operations sono attive e i loro gruppi
4. Perché un agent viene aggiunto (o no) a un'operation
5. Quante istruzioni vengono generate e perché
6. Dettagli completi di ogni istruzione inviata

**File chiave**: `caldera.log`  
**Script chiave**: `./monitor-agent-beacons.sh`  
**Livello log**: `--log INFO`
