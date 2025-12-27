# Merlino API - Ability Success Rate Analysis

**Data**: 2025-12-26  
**Endpoint**: `/api/v2/merlino/analytics/ability-success-rate`  
**Metodo**: `GET`  
**Versione**: 1.0  

---

## Descrizione

API dedicata per analizzare il **tasso di successo delle abilities** con metriche aggregate, tempi di esecuzione e dettagli sui fallimenti recenti per troubleshooting.

Fornisce dati autoritativi indipendenti dal payload `synchronize`, eliminando approssimazioni e inconsistenze.

---

## Autenticazione

Stessa autenticazione degli altri endpoint Merlino:

```http
GET /api/v2/merlino/analytics/ability-success-rate
Host: 192.168.124.133:8888
KEY: ADMIN123
```

---

## Query Parameters

Tutti i parametri sono **opzionali**:

| Parametro | Tipo | Default | Max | Descrizione |
|-----------|------|---------|-----|-------------|
| `since_hours` | int | `72` | - | Finestra temporale in ore (ultimi N ore) |
| `from` | ISO-8601 | - | - | Inizio finestra temporale (es: `2025-12-20T00:00:00Z`) |
| `to` | ISO-8601 | - | - | Fine finestra temporale (es: `2025-12-26T23:59:59Z`) |
| `operation_id` | string | - | - | Filtra per operazione specifica (UUID) |
| `agent_paw` | string | - | - | Filtra per agente specifico (PAW ID) |
| `group` | string | - | - | Filtra per gruppo Caldera (es: `red`, `blue`) |
| `limit` | int | `250` | `2000` | Numero massimo di abilities ritornate |
| `min_executions` | int | `1` | - | Minimo esecuzioni per includere l'ability |

**Regole finestra temporale**:
- Se `from` e `to` sono forniti, hanno precedenza su `since_hours`
- Altrimenti si usa `from = now - since_hours`, `to = now`

---

## Response Format

**Status Code**: `200 OK`  
**Content-Type**: `application/json`

### Struttura Response

```json
{
  "generated_at": "2025-12-26T23:31:22.355901+00:00",
  "window": {
    "from": "2025-12-23T23:31:22.355901+00:00",
    "to": "2025-12-26T23:31:22.355901+00:00",
    "since_hours": 72
  },
  "filters": {
    "operation_id": null,
    "agent_paw": null,
    "group": null,
    "min_executions": 1
  },
  "stats": {
    "unique_abilities": 2,
    "total_executions": 2,
    "success": 1,
    "failed": 1,
    "timeout": 0,
    "running": 0
  },
  "abilities": [
    {
      "ability_id": "6fe8f0c1c175fd3a5fb1d384114f5ecf",
      "ability_name": "Decode Eicar File and Write to File",
      "plugin": "atomic",
      "tactics": ["defense-evasion"],
      "techniques": ["T1027.013"],
      
      "total_executions": 1,
      "success_count": 0,
      "failure_count": 1,
      "timeout_count": 0,
      "running_count": 0,
      "success_rate": 0.0,
      
      "avg_execution_time_ms": 36671,
      "p95_execution_time_ms": 36671,
      
      "operations": [
        {
          "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
          "operation_name": "ops1",
          "executions": 1,
          "success": 0,
          "failed": 1,
          "timeout": 0,
          "running": 0
        }
      ],
      
      "recent_failures": [
        {
          "when": "2025-12-23T22:11:39+00:00",
          "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
          "operation_name": "ops1",
          "agent_paw": "puqadh",
          "agent_host": "WINDOWSPC01",
          "exit_code": 0,
          "stderr_preview": "",
          "stdout_preview": "WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo= : The term...",
          "problem_id": "defense-evasion/T1027.013"
        }
      ]
    }
  ]
}
```

---

## Campo-per-Campo

### Root Level

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `generated_at` | ISO-8601 | Timestamp generazione risposta (UTC) |
| `window` | object | Finestra temporale applicata |
| `filters` | object | Filtri applicati alla query |
| `stats` | object | Statistiche aggregate globali |
| `abilities` | array | Lista abilities con metriche dettagliate |

### `window` Object

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `from` | ISO-8601 | Inizio finestra temporale |
| `to` | ISO-8601 | Fine finestra temporale |
| `since_hours` | int | Ore di lookback usate |

### `filters` Object

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `operation_id` | string\|null | Filtro operation_id applicato |
| `agent_paw` | string\|null | Filtro agent_paw applicato |
| `group` | string\|null | Filtro group applicato |
| `min_executions` | int | Soglia minima esecuzioni |

### `stats` Object (Globale)

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `unique_abilities` | int | Numero abilities uniche trovate |
| `total_executions` | int | Totale esecuzioni aggregate |
| `success` | int | Totale esecuzioni con successo |
| `failed` | int | Totale esecuzioni fallite |
| `timeout` | int | Totale esecuzioni in timeout |
| `running` | int | Totale esecuzioni in corso |

### `abilities[]` Array Items

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `ability_id` | string | UUID dell'ability (identificatore stabile) |
| `ability_name` | string | Nome human-readable dell'ability |
| `plugin` | string | Plugin Caldera di origine (es: `stockpile`, `atomic`) |
| `tactics` | string[] | Lista MITRE tactics (lowercase, hyphenated) |
| `techniques` | string[] | Lista MITRE technique IDs (es: `T1059.001`) |
| `total_executions` | int | Totale esecuzioni di questa ability |
| `success_count` | int | Numero esecuzioni con successo (status=0) |
| `failure_count` | int | Numero esecuzioni fallite (status=1) |
| `timeout_count` | int | Numero esecuzioni in timeout (status=124) |
| `running_count` | int | Numero esecuzioni in corso (status=-1) |
| `success_rate` | float | Percentuale di successo (0.0 - 100.0) |
| `avg_execution_time_ms` | int\|null | Tempo medio esecuzione in millisecondi |
| `p95_execution_time_ms` | int\|null | 95° percentile tempo esecuzione in ms |
| `operations` | array | Breakdown per-operation |
| `recent_failures` | array | Ultimi 5 fallimenti (max) per troubleshooting |

### `operations[]` Array Items

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `operation_id` | string | UUID operazione |
| `operation_name` | string | Nome operazione |
| `executions` | int | Esecuzioni di questa ability in questa operation |
| `success` | int | Successi |
| `failed` | int | Fallimenti |
| `timeout` | int | Timeout |
| `running` | int | In corso |

### `recent_failures[]` Array Items

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `when` | ISO-8601 | Timestamp del fallimento |
| `operation_id` | string | UUID operazione |
| `operation_name` | string | Nome operazione |
| `agent_paw` | string | PAW dell'agente |
| `agent_host` | string | Hostname dell'agente |
| `exit_code` | int\|null | Exit code del comando (se disponibile) |
| `stderr_preview` | string | Prime 200 chars di stderr |
| `stdout_preview` | string | Prime 200 chars di stdout |
| `problem_id` | string\|null | ID problema formato `tactic/Txxxx` per drilldown |

**Nota `problem_id`**: Utilizzabile per chiamare endpoint di drilldown esistenti:
```
GET /api/v2/merlino/ops-graph/problem-details?problem_id=defense-evasion/T1027.013
```

---

## Status Normalization

L'API normalizza gli stati Caldera nei seguenti bucket:

| Status Caldera | Bucket | Descrizione |
|----------------|--------|-------------|
| `0` | `success` | Esecuzione completata con successo |
| `1` | `failed` | Esecuzione fallita con errore |
| `124` | `timeout` | Esecuzione terminata per timeout |
| `-1` | `running` | Esecuzione in corso o stato sconosciuto |

---

## Esempi di Chiamata

### 1. Query Base (ultimi 3 giorni)

```bash
curl -H "KEY: ADMIN123" \
  "http://192.168.124.133:8888/api/v2/merlino/analytics/ability-success-rate"
```

### 2. Ultimi 7 giorni con limite

```bash
curl -H "KEY: ADMIN123" \
  "http://192.168.124.133:8888/api/v2/merlino/analytics/ability-success-rate?since_hours=168&limit=50"
```

### 3. Filtra per operazione specifica

```bash
curl -H "KEY: ADMIN123" \
  "http://192.168.124.133:8888/api/v2/merlino/analytics/ability-success-rate?operation_id=5a9a344c-d65a-4153-9259-0aa34a7d93dc"
```

### 4. Filtra per agente

```bash
curl -H "KEY: ADMIN123" \
  "http://192.168.124.133:8888/api/v2/merlino/analytics/ability-success-rate?agent_paw=puqadh"
```

### 5. Filtra per gruppo

```bash
curl -H "KEY: ADMIN123" \
  "http://192.168.124.133:8888/api/v2/merlino/analytics/ability-success-rate?group=red"
```

### 6. Finestra temporale custom

```bash
curl -H "KEY: ADMIN123" \
  "http://192.168.124.133:8888/api/v2/merlino/analytics/ability-success-rate?from=2025-12-20T00:00:00Z&to=2025-12-26T23:59:59Z"
```

### 7. Solo abilities con almeno 10 esecuzioni

```bash
curl -H "KEY: ADMIN123" \
  "http://192.168.124.133:8888/api/v2/merlino/analytics/ability-success-rate?min_executions=10&limit=100"
```

---

## Error Responses

### 400 Bad Request

Parametri query invalidi (es: data ISO-8601 malformata, since_hours negativo).

```json
{
  "error": "Invalid query parameter: invalid literal for int() with base 10: 'abc'"
}
```

### 401/403 Unauthorized

API key mancante o invalida.

```json
{
  "error": "Unauthorized"
}
```

### 500 Internal Server Error

Errore server durante elaborazione.

```json
{
  "error": "Internal server error",
  "traceback": "..."
}
```

---

## Performance

- **Target response time**: < 2 secondi per finestre di 168h (7 giorni)
- **Default limit**: 250 abilities (configurable, max 2000)
- **Dati aggregati**: Statistiche pre-calcolate per performance ottimale
- **Paginazione**: Non ancora implementata (verrà aggiunta in futuro)

---

## Note per l'Implementazione in Merlino

### Excel Add-in Integration

1. **Tab "Success Analysis"**: Utilizzare questa API per popolare metriche e tabelle
2. **Caching**: Considerare cache locale per ridurre chiamate ripetute
3. **Refresh automatico**: Suggerito ogni 5-10 minuti per dati real-time
4. **Drilldown**: Utilizzare `problem_id` per integrare con endpoint dettagli problema

### Calcolo Success Rate

**NON** calcolare il success rate lato client dal `synchronize`. Questa API fornisce già:
- Success rate corretto e autoritativo
- Normalizzazione status consistente
- Aggregate per operation/agent

### Visualizzazioni Suggerite

1. **Tabella principale**: Ordinata per `success_rate` ascendente (mostra problemi first)
2. **Grafici**:
   - Bar chart: Success rate per ability
   - Pie chart: Distribuzione success/failed/timeout
   - Timeline: Failures nel tempo
3. **Dettagli fallimenti**: Mostrare `recent_failures[]` con preview output

### Filtri UI Suggeriti

- Dropdown operazioni (da `operations[]`)
- Dropdown agenti (da chiamata separata o hardcoded)
- Slider time window (24h, 72h, 7d, 30d)
- Checkbox "Solo problematiche" (success_rate < 80%)

---

## Changelog

### v1.0 (2025-12-26)
- ✅ Release iniziale
- ✅ Query parameters completi
- ✅ Success rate e execution time metrics
- ✅ Recent failures con output preview
- ✅ Problem ID per drilldown integration
- ✅ Status normalization consistente

---

## Contatti

Per bug report o richieste di modifica, contattare il team Morgana Arsenal.

**Repository**: https://github.com/x3m-ai/morgana-arsenal (private)  
**Maintainer**: Morgana (@x3m-ai)
