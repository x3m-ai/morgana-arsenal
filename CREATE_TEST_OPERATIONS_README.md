# Test Operations Creator - Morgana Arsenal

Script Python per creare automaticamente operations di test con adversaries casuali e agenti distribuiti su gruppi diversi.

## Funzionalità

- ✅ Crea operations automaticamente per ogni gruppo di agenti
- ✅ Assegna adversaries casuali ad ogni operation
- ✅ Distribuisce planners diversi (atomic, batch, buckets, bayes, etc.)
- ✅ Crea 2-3 operations per gruppo
- ✅ Tutte le operations create sono in stato **PAUSED** (pronte per essere avviate manualmente)

## Prerequisiti

- Server Morgana Arsenal in esecuzione
- Agenti creati (usa `simulate_agents.py` per creare agenti fittizi)
- Adversaries configurati nel sistema

## Utilizzo

```bash
# Esegui lo script
python3 create_test_operations.py
```

## Output Esempio

```
🔍 Recupero dati dal server...

✅ Trovati 21 agenti
✅ Trovati 38 adversaries
✅ Trovati 6 planners

📋 Gruppi disponibili:
   - red: 8 agenti [windows(4), linux(4)]
   - blue: 10 agenti [linux(8), darwin(1), windows(1)]
   - test: 2 agenti [linux(2)]
   - production: 1 agenti [windows(1)]

🎯 Creazione operations...

✅ Creata: Test_red_Super Spy_232801_1
   └─ ID: fe759c6e-29ad-4f77-867d-b306a47d519c
   └─ Adversary: Super Spy (15 abilities)
   └─ Planner: bayes
   └─ Gruppo: red (8 agenti)
   └─ Stato: PAUSED

✅ Creata: Test_blue_Ransack_232801_1
   └─ ID: 5b7c9c35-7eb3-409c-9faf-6f482341a48b
   └─ Adversary: Ransack (18 abilities)
   └─ Planner: look ahead
   └─ Gruppo: blue (10 agenti)
   └─ Stato: PAUSED
```

## Cosa Crea lo Script

### Per ogni gruppo di agenti:
- **2-3 operations** con adversaries casuali
- **Planner diverso** per ogni operation (atomic, batch, buckets, etc.)
- **Nome univoco** con timestamp: `Test_{gruppo}_{adversary}_{timestamp}_{numero}`
- **Stato PAUSED** - devono essere avviate manualmente dalla UI

### Distribuzione

Se hai questi gruppi:
- **red**: 8 agenti → 2 operations
- **blue**: 10 agenti → 3 operations
- **test**: 2 agenti → 2 operations
- **production**: 1 agente → 2 operations

Lo script crea **9 operations totali** distribuite su tutti i gruppi.

## Adversaries Utilizzati

Lo script seleziona **solo adversaries con abilities** configurate. Alcuni esempi:
- Hunter (9 abilities)
- Discovery (12 abilities)
- Collection (15 abilities)
- Ransack (18 abilities)

## Planners Utilizzati

- **atomic**: Esegue tutte le abilities nell'ordine
- **batch**: Raggruppa abilities simili
- **buckets**: Organizza per tattica
- **bayes**: Usa probabilità bayesiane
- **guided**: Richiede approvazione manuale per ogni step
- **look ahead**: Pianifica guardando avanti nelle dipendenze

## Verifica Operations Create

### Via API

```bash
# Lista tutte le operations
curl -H "KEY: ADMIN123" "http://localhost:8888/api/v2/operations" | jq '.[] | {name, state, group}'

# Conta operations per gruppo
curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/operations" | jq -r '.[] | select(.name | startswith("Test_")) | .group' | sort | uniq -c
```

### Via Web UI

1. Apri browser: `http://localhost:8888`
2. Vai su **Campaigns → Operations**
3. Dovresti vedere tutte le operations create con prefisso `Test_`
4. Ogni operation è in stato **PAUSED** (badge giallo)

## Avvio Operations

### Dalla UI

1. Vai su **Campaigns → Operations**
2. Clicca sulla riga dell'operation desiderata
3. Clicca il bottone **▶ Start** (verde)
4. Monitora l'esecuzione nella view Operation

### Via API

```bash
# Avvia una operation specifica
curl -H "KEY: ADMIN123" -X PATCH "http://localhost:8888/api/v2/operations/{OPERATION_ID}" \
  -H "Content-Type: application/json" \
  -d '{"state": "running"}'

# Avvia tutte le operations del gruppo red
for op_id in $(curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/operations" | jq -r '.[] | select(.group=="red") | .id'); do
    curl -H "KEY: ADMIN123" -X PATCH "http://localhost:8888/api/v2/operations/$op_id" \
      -H "Content-Type: application/json" \
      -d '{"state": "running"}'
done
```

## Comportamento con Agenti Fittizi

⚠️ **IMPORTANTE**: Se hai creato agenti con `simulate_agents.py`, questi sono agenti **fittizi**:

- ✅ Le operations si avviano correttamente
- ✅ Le abilities vengono assegnate agli agenti
- ✅ I links vengono creati nel chain
- ❌ Gli agenti NON eseguono realmente i comandi (nessuna macchina target)
- ❌ I risultati saranno vuoti o in timeout

Questo è **perfetto per testare**:
- La UI con molte operations
- La distribuzione di adversaries su gruppi diversi
- Il comportamento dei planners
- Le performance con molti agenti
- La visualizzazione del graph delle operations

## Pulizia

### Elimina tutte le test operations

```bash
# Via API - elimina operations che iniziano con "Test_"
for op_id in $(curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/operations" | jq -r '.[] | select(.name | startswith("Test_")) | .id'); do
    echo "Deleting operation $op_id..."
    curl -H "KEY: ADMIN123" -X DELETE "http://localhost:8888/api/v2/operations/$op_id"
done
```

### Reset completo database

```bash
# Ferma il server
./stop-caldera.sh

# Elimina il database
rm data/object_store

# Riavvia il server
python3 server.py --insecure --log DEBUG
```

## Workflow Completo di Test

```bash
# 1. Crea agenti fittizi
python3 simulate_agents.py --count 20 --groups "red,blue,production" --create-only

# 2. Crea operations di test
python3 create_test_operations.py

# 3. Verifica nella UI
# Apri http://localhost:8888 e vai su Campaigns → Operations

# 4. Avvia una operation
# Seleziona una operation e clicca Start

# 5. Monitora l'esecuzione
# Osserva il graph e i links creati

# 6. Pulizia (opzionale)
# Elimina operations via UI o API
```

## Casi d'Uso

### 1. Test UI Performance

```bash
# Crea molti agenti
python3 simulate_agents.py --count 50 --create-only

# Crea molte operations
python3 create_test_operations.py

# Verifica che la UI risponda bene con molte operations
```

### 2. Test Adversary Distribution

```bash
# Crea gruppi bilanciati
python3 simulate_agents.py --count 10 --groups "red" --create-only
python3 simulate_agents.py --count 10 --groups "blue" --create-only

# Crea operations per confrontare adversaries
python3 create_test_operations.py

# Analizza quale adversary genera più links
```

### 3. Test Planner Behavior

```bash
# Crea operations di test
python3 create_test_operations.py

# Avvia operations con planners diversi
# Confronta come atomic vs batch vs buckets organizzano le abilities
```

### 4. Demo per Clienti

```bash
# Setup ambiente completo
python3 simulate_agents.py --count 30 --groups "red,blue,production" --create-only
python3 create_test_operations.py

# Mostra la UI con operations realistiche senza eseguire nulla
```

## Note Tecniche

### API Endpoint Utilizzato

```http
POST /api/v2/operations
Headers:
  KEY: ADMIN123
  Content-Type: application/json
Body:
  {
    "name": "Test_red_Hunter_123456_1",
    "adversary": {"adversary_id": "uuid"},
    "group": "red",
    "planner": {"id": "atomic"},
    "source": {"id": "uuid"},
    "state": "paused",
    "jitter": "2/8",
    "visibility": 50,
    "autonomous": 1,
    "obfuscator": "plain-text"
  }
```

### Naming Convention

Le operations create seguono questo pattern:
```
Test_{gruppo}_{adversary_primi15char}_{timestamp}_{numero}
```

Esempio:
```
Test_red_Super Spy_232801_1
  └─ gruppo: red
  └─ adversary: Super Spy
  └─ timestamp: 23:28:01
  └─ numero: 1 (prima operation per questo gruppo)
```

## Troubleshooting

### "Nessun agente trovato"

```bash
# Crea prima degli agenti
python3 simulate_agents.py --count 10 --groups "red,blue" --create-only
```

### "Nessun adversary trovato"

- Verifica che ci siano adversaries nel sistema
- Controlla `data/adversaries/*.yml`
- Assicurati che abbiano `atomic_ordering` configurato

### Operations non visibili nella UI

- Fai refresh del browser (Ctrl+Shift+R)
- Verifica con API: `curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/operations`
- Controlla i log: `tail -f caldera-debug.log`

### Errore HTTP 401

- Verifica l'API key in `conf/default.yml`
- Usa `--api-key "TUA_CHIAVE"` se diversa

## Licenza

Parte di Morgana Arsenal - Apache 2.0 License
