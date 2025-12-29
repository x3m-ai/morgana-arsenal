# Morgana Arsenal - Realtime Operations Metrics API
**Documentation for Merlino Excel Add-in Integration**

---

## Table of Contents
1. [Overview](#overview)
2. [Base Configuration](#base-configuration)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
5. [Response Examples](#response-examples)
6. [Computation Rules](#computation-rules)
7. [Integration Notes](#integration-notes)

---

## Overview

Le **Realtime Operations Metrics API** forniscono metriche live sullo stato delle operazioni Caldera per dashboard e monitoring in tempo reale. Progettate per polling frequente (2-30 secondi) da Merlino Excel Add-in per KPI live mentre le operazioni sono in esecuzione.

**Key Features:**
- Snapshot completo: globalStats + operations + agents + timeline
- Endpoints specifici per ogni sezione (operations, agents, timeline)
- Filtraggio temporale con `windowMinutes` (default 60)
- Calcolo automatico di success rate e conteggi per stato
- Timeline eventi recenti con limite configurabile
- Supporto polling ad alta frequenza (2-30s refresh)

**Base URL:** `https://192.168.124.133/api/v2/merlino/realtime/`

**Authentication:** API Key nel header HTTP
```http
KEY: ADMIN123
```

---

## Base Configuration

**Server Caldera:**
- Host: `192.168.124.133`
- Port: `443` (HTTPS via Nginx)
- API Base: `/api/v2/merlino/realtime/`

**Headers richiesti:**
```http
KEY: ADMIN123
Content-Type: application/json
```

**Response Format:** JSON
**Encoding:** UTF-8
**Date Format:** ISO 8601 (YYYY-MM-DDTHH:MM:SS.ssssss+00:00)

---

## Data Models

### OperationRealtime
Operazione con contatori live calcolati dal chain.

```typescript
interface OperationRealtime {
    id: string;                      // UUID operazione
    name: string;                    // Nome operazione
    adversary: string | null;        // Adversary ID (UUID)
    state: string;                   // "running" | "finished" | "stopped" | "paused"
    started: string | null;          // ISO timestamp start
    start_time: string | null;       // ISO timestamp start (duplicato per compatibilità)
    finish_time: string | null;      // ISO timestamp fine
    total_abilities: number;         // Totale abilities nel chain
    success_count: number;           // Abilities con status=0
    error_count: number;             // Abilities con status=1 o 124
    running_count: number;           // Abilities con status=-1
    agents_count: number;            // Numero agenti coinvolti
    techniques_count: number;        // Numero tecniche MITRE uniche
    tcodes: string[];                // Lista technique IDs (T1110.001, etc.)
    abilities: AbilityInfo[];        // Prime 10 abilities (name, tactic, technique, status)
}
```

### AgentRealtime
Agent con platform e last_seen.

```typescript
interface AgentRealtime {
    paw: string;                     // PAW ID agente
    host: string | null;             // Hostname
    platform: string | null;         // "windows" | "linux" | "darwin"
    last_seen: string | null;        // ISO timestamp ultimo beacon
}
```

### GlobalRealtimeStats
Statistiche aggregate globali.

```typescript
interface GlobalRealtimeStats {
    totalOps: number;                // Totale operazioni
    totalAbilities: number;          // Totale abilities in tutte le ops
    totalSuccess: number;            // Totale abilities con status=0
    totalErrors: number;             // Totale abilities con status=1/124
    successRate: number;             // Percentuale successo (0-100, 3 decimali)
    runningOps: number;              // Operazioni con state="running"
    completedOps: number;            // Operazioni con state="finished"
    failedOps: number;               // Operazioni con state="stopped" o "paused"
    totalAgents: number;             // Totale agenti registrati
}
```

### TimelineEvent
Evento timeline per cronologia operazioni.

```typescript
interface TimelineEvent {
    timestamp: string;               // ISO timestamp evento
    operation: string;               // Nome operazione
    event: string;                   // "started" | "completed" | "stopped" | "ability_executed"
    details: string;                 // Descrizione evento
}
```

### AbilityInfo
Informazioni ability per operations.

```typescript
interface AbilityInfo {
    name: string;                    // Nome ability
    tactic: string | null;           // Tactic MITRE (discovery, execution, etc.)
    technique: string | null;        // Technique ID (T1082, etc.)
    status: string;                  // "success" | "error" | "running" | "unknown"
}
```

---

## API Endpoints

### 1. GET /merlino/realtime/operations/metrics
**Snapshot completo: globalStats + operations + agents + timeline**

Endpoint principale per dashboard live con tutte le metriche in una singola chiamata.

**Query Parameters:**

**windowMinutes** (int, default: 60)  
Finestra temporale per timeline (minuti)

**includeTimeline** (bool, default: true)  
Includere timeline eventi nella response

**timelineLimit** (int, default: 20)  
Numero massimo eventi timeline da restituire

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:19:54.719297+00:00",
        "windowMinutes": 60
    },
    "globalStats": {
        "totalOps": 5,
        "totalAbilities": 2,
        "totalSuccess": 1,
        "totalErrors": 1,
        "successRate": 50.0,
        "runningOps": 1,
        "completedOps": 0,
        "failedOps": 4,
        "totalAgents": 21
    },
    "operations": [
        {
            "id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
            "name": "ops1",
            "adversary": "d39c9b2e-44c3-4d4c-a9a4-33e6b9802499",
            "state": "running",
            "started": "2025-12-22T14:50:46.818881+00:00",
            "start_time": "2025-12-22T14:50:46.818881+00:00",
            "finish_time": null,
            "total_abilities": 2,
            "success_count": 1,
            "error_count": 1,
            "running_count": 0,
            "agents_count": 1,
            "techniques_count": 2,
            "tcodes": ["T1027.013", "T1082"],
            "abilities": [
                {
                    "name": "Merlino - Test Agent",
                    "tactic": "discovery",
                    "technique": "T1082",
                    "status": "success"
                },
                {
                    "name": "Decode Eicar File and Write to File",
                    "tactic": "defense-evasion",
                    "technique": "T1027.013",
                    "status": "error"
                }
            ]
        }
    ],
    "agents": [
        {
            "paw": "puqadh",
            "host": "WINDOWSPC01",
            "platform": "windows",
            "last_seen": "2025-12-27T00:28:41.509736+00:00"
        }
    ],
    "timeline": []
}
```

**Usage Example (Excel VBA):**
```vba
' Polling ogni 5 secondi per KPI live
Dim url As String
url = "https://192.168.124.133/api/v2/merlino/realtime/operations/metrics?windowMinutes=60"

Dim http As Object
Set http = CreateObject("MSXML2.XMLHTTP")
http.Open "GET", url, False
http.setRequestHeader "KEY", "ADMIN123"
http.send

If http.Status = 200 Then
    Dim json As Object
    Set json = JsonConverter.ParseJson(http.responseText)
    
    ' Estrai globalStats
    Range("B2").Value = json("globalStats")("totalOps")
    Range("B3").Value = json("globalStats")("successRate")
    Range("B4").Value = json("globalStats")("runningOps")
    Range("B5").Value = json("globalStats")("totalAgents")
    
    ' Popola tabella operations
    Dim i As Long
    For i = 0 To json("operations").Count - 1
        Range("A" & i + 8).Value = json("operations")(i)("name")
        Range("B" & i + 8).Value = json("operations")(i)("state")
        Range("C" & i + 8).Value = json("operations")(i)("success_count")
        Range("D" & i + 8).Value = json("operations")(i)("error_count")
    Next i
End If
```

---

### 2. GET /merlino/realtime/operations
**Solo lista operazioni (lightweight)**

Endpoint semplificato per polling rapido dello stato operazioni.

**Query Parameters:**

_Nessun parametro richiesto_ - Restituisce tutte le operazioni

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:19:59.898200+00:00"
    },
    "operations": [
        {
            "id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
            "name": "ops1",
            "state": "running"
        },
        {
            "id": "eb007f93-310f-47d3-b899-9b010faa5071",
            "name": "Linked Malicious Storage Artifacts",
            "state": "paused"
        }
    ]
}
```

**Usage Example (PowerShell):**
```powershell
$headers = @{ KEY = "ADMIN123" }
$response = Invoke-RestMethod -Uri "https://192.168.124.133/api/v2/merlino/realtime/operations" -Headers $headers
$response.operations | Format-Table name, state
```

---

### 3. GET /merlino/realtime/agents
**Solo lista agents (lightweight)**

Endpoint semplificato per polling rapido dello stato agenti.

**Query Parameters:**

_Nessun parametro richiesto_ - Restituisce tutti gli agenti registrati

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:25:50.882765+00:00"
    },
    "agents": [
        {
            "paw": "puqadh",
            "host": "WINDOWSPC01",
            "platform": "windows",
            "last_seen": "2025-12-27T14:25:37.252586+00:00"
        },
        {
            "paw": "pafyhz",
            "host": "test-host",
            "platform": "linux",
            "last_seen": "2025-12-23T23:15:11.863995+00:00"
        }
    ]
}
```

**Usage Example (curl):**
```bash
curl -s -k -H "KEY: ADMIN123" https://192.168.124.133/api/v2/merlino/realtime/agents | jq '.agents[] | {host, platform, last_seen}'
```

---

### 4. GET /merlino/realtime/timeline
**Solo timeline eventi (filtrato per finestra temporale)**

Endpoint per cronologia eventi recenti con filtraggio temporale.

**Query Parameters:**

**windowMinutes** (int, default: 60)  
Finestra temporale in minuti da ora (eventi più recenti)

**limit** (int, default: 20)  
Numero massimo eventi timeline da restituire

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:25:55.207657+00:00",
        "windowMinutes": 120
    },
    "timeline": []
}
```

**Nota:** Timeline restituisce eventi solo per operazioni con abilities eseguite nell'ultima finestra temporale. Se nessuna ability è stata eseguita recentemente, l'array è vuoto.

**Usage Example (Python):**
```python
import requests

headers = {'KEY': 'ADMIN123'}
params = {'windowMinutes': 30, 'limit': 10}
response = requests.get(
    'https://192.168.124.133/api/v2/merlino/realtime/timeline',
    headers=headers,
    params=params,
    verify=False  # Self-signed certificate
)

timeline = response.json()['timeline']
for event in timeline:
    print(f"{event['timestamp']}: {event['operation']} - {event['details']}")
```

---

## Response Examples

### Example 1: Operation Running con Multiple Abilities

**Request:**
```bash
curl -k -H "KEY: ADMIN123" "https://192.168.124.133/api/v2/merlino/realtime/operations/metrics?windowMinutes=60"
```

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:19:54.719297+00:00",
        "windowMinutes": 60
    },
    "globalStats": {
        "totalOps": 5,
        "totalAbilities": 2,
        "totalSuccess": 1,
        "totalErrors": 1,
        "successRate": 50.0,
        "runningOps": 1,
        "completedOps": 0,
        "failedOps": 4,
        "totalAgents": 21
    },
    "operations": [
        {
            "id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
            "name": "ops1",
            "adversary": "d39c9b2e-44c3-4d4c-a9a4-33e6b9802499",
            "state": "running",
            "started": "2025-12-22T14:50:46.818881+00:00",
            "start_time": "2025-12-22T14:50:46.818881+00:00",
            "finish_time": null,
            "total_abilities": 2,
            "success_count": 1,
            "error_count": 1,
            "running_count": 0,
            "agents_count": 1,
            "techniques_count": 2,
            "tcodes": ["T1027.013", "T1082"],
            "abilities": [
                {
                    "name": "Merlino - Test Agent",
                    "tactic": "discovery",
                    "technique": "T1082",
                    "status": "success"
                },
                {
                    "name": "Decode Eicar File and Write to File",
                    "tactic": "defense-evasion",
                    "technique": "T1027.013",
                    "status": "error"
                }
            ]
        }
    ],
    "agents": [
        {
            "paw": "puqadh",
            "host": "WINDOWSPC01",
            "platform": "windows",
            "last_seen": "2025-12-27T00:28:41.509736+00:00"
        }
    ],
    "timeline": []
}
```

**Interpretation:**
- 1 operazione running su 5 totali
- 2 abilities: 1 success (50%), 1 error (50%)
- Success rate: 50.0%
- 1 agente coinvolto (WINDOWSPC01, Windows)
- 2 tecniche MITRE: T1027.013 (Deobfuscate/Decode Files), T1082 (System Information Discovery)
- Timeline vuota (nessuna ability eseguita nell'ultima ora)

### Example 2: Multiple Operations Paused

**Request:**
```bash
curl -k -H "KEY: ADMIN123" "https://192.168.124.133/api/v2/merlino/realtime/operations"
```

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:19:59.898200+00:00"
    },
    "operations": [
        {
            "id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
            "name": "ops1",
            "state": "running"
        },
        {
            "id": "eb007f93-310f-47d3-b899-9b010faa5071",
            "name": "Linked Malicious Storage Artifacts",
            "state": "paused"
        },
        {
            "id": "93b009a3-b1a0-4d4e-9be8-0b20c2ad917c",
            "name": "LSASS Credential Dumping with Procdump",
            "state": "paused"
        },
        {
            "id": "e0cbca62-6755-42e7-9ecd-751f1da93b93",
            "name": "Doppelpaymer Stop Services",
            "state": "paused"
        },
        {
            "id": "fe759c6e-29ad-4f77-867d-b306a47d519c",
            "name": "Test_red_Super Spy_232801_1",
            "state": "paused"
        }
    ]
}
```

**Interpretation:**
- 1 operazione running ("ops1")
- 4 operazioni paused (non in esecuzione, fermate manualmente)
- Total operations: 5

### Example 3: Agents List con Multiple Platforms

**Request:**
```bash
curl -k -H "KEY: ADMIN123" "https://192.168.124.133/api/v2/merlino/realtime/agents"
```

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:25:50.882765+00:00"
    },
    "agents": [
        {
            "paw": "puqadh",
            "host": "WINDOWSPC01",
            "platform": "windows",
            "last_seen": "2025-12-27T14:25:37.252586+00:00"
        },
        {
            "paw": "pafyhz",
            "host": "test-host",
            "platform": "linux",
            "last_seen": "2025-12-23T23:15:11.863995+00:00"
        },
        {
            "paw": "xmtqer",
            "host": "fake-host-001",
            "platform": "linux",
            "last_seen": "2025-12-23T23:19:59.578608+00:00"
        },
        {
            "paw": "rcdbxm",
            "host": "DC-729",
            "platform": "windows",
            "last_seen": "2025-12-23T23:23:02.158385+00:00"
        },
        {
            "paw": "vbmcai",
            "host": "imac-651",
            "platform": "darwin",
            "last_seen": "2025-12-23T23:23:02.173669+00:00"
        }
    ]
}
```

**Interpretation:**
- 5 agenti registrati (3 Windows, 2 Linux, 1 macOS)
- 1 agente attivo recentemente (puqadh, last_seen 13 secondi fa)
- 4 agenti inattivi (last_seen 4+ giorni fa)

### Example 4: Timeline Empty (No Recent Events)

**Request:**
```bash
curl -k -H "KEY: ADMIN123" "https://192.168.124.133/api/v2/merlino/realtime/timeline?windowMinutes=120&limit=10"
```

**Response:**
```json
{
    "meta": {
        "generatedAt": "2025-12-27T14:25:55.207657+00:00",
        "windowMinutes": 120
    },
    "timeline": []
}
```

**Interpretation:**
- Nessuna ability eseguita nelle ultime 2 ore (120 minuti)
- Timeline vuota (nessun evento ability_executed)
- Operazioni esistono ma senza executions recenti

---

## Computation Rules

### Success Rate Calculation
```
successRate = (totalSuccess / totalAbilities) * 100
```
- Arrotondato a 3 decimali (es. 50.000)
- Se `totalAbilities = 0`, `successRate = 0.0`
- Range: 0.0 - 100.0

### Operation State Mapping
```
- "running": Operation con state="running"
- "finished": Operation con state="finished"
- "stopped"/"paused": Operation con state="stopped" o "paused"
```

### Ability Status Mapping
```
Link status → Ability status:
- 0 → "success"
- 1, 124 → "error"
- -1 → "running"
- others → "unknown"
```

### Timeline Event Types
```
Event types generati:
- "started": Operation.start timestamp
- "ability_executed": Link.finish timestamp (per ogni ability completata)
```

### windowMinutes Filter
```
- Calcola window_start = generatedAt - windowMinutes
- Filtra eventi con timestamp >= window_start
- Ordina per timestamp DESC
- Applica limit
```

### TCodes Extraction
```
- Estrae technique_id da ogni ability nel chain
- Deduplica (set)
- Ordina alfabeticamente
- Restituisce lista (es. ["T1027.013", "T1082"])
```

---

## Integration Notes

### Polling Strategy per Merlino Excel Add-in

**Recommended Polling Intervals:**
- **Dashboard live**: 5 secondi (operations/metrics completo)
- **Operations status**: 10 secondi (operations lightweight)
- **Agents status**: 30 secondi (agents lightweight)
- **Timeline**: 15 secondi (timeline con windowMinutes=60)

**Resource Optimization:**
```
Scenario A: Dashboard completo (ogni 5s)
→ GET https://192.168.124.133/api/v2/merlino/realtime/operations/metrics?windowMinutes=60&timelineLimit=10

Scenario B: Solo status ops (ogni 10s)
→ GET https://192.168.124.133/api/v2/merlino/realtime/operations

Scenario C: Solo agents (ogni 30s)
→ GET https://192.168.124.133/api/v2/merlino/realtime/agents

Scenario D: Timeline separata (ogni 15s)
→ GET https://192.168.124.133/api/v2/merlino/realtime/timeline?windowMinutes=30&limit=20
```

### Error Handling

**Common HTTP Status Codes:**
- `200 OK`: Success, JSON payload in response body
- `401 Unauthorized`: Invalid API key (check KEY header)
- `500 Internal Server Error`: Server error (check traceback field in JSON)

**Error Response Format:**
```json
{
    "error": "Object of type datetime is not JSON serializable",
    "traceback": "Traceback (most recent call last):\n  File ..."
}
```

**Excel VBA Error Handling:**
```vba
If http.Status <> 200 Then
    Dim errorMsg As String
    errorMsg = JsonConverter.ParseJson(http.responseText)("error")
    MsgBox "API Error: " & errorMsg, vbCritical
    Exit Sub
End If
```

### Performance Considerations

**Response Sizes:**
- `/operations/metrics`: ~5-50 KB (dipende da operations count)
- `/operations`: ~1-5 KB (lightweight)
- `/agents`: ~2-10 KB (dipende da agents count)
- `/timeline`: ~1-20 KB (dipende da limit e windowMinutes)

**Network Impact:**
- Polling 5s: ~12 requests/min, ~0.6 MB/min (metrics)
- Polling 10s: ~6 requests/min, ~0.03 MB/min (operations)
- Polling 30s: ~2 requests/min, ~0.02 MB/min (agents)

**Recommended:**
- Use `/operations/metrics` per dashboard completo (5-10s polling)
- Use `/operations` + `/agents` + `/timeline` separati per ottimizzare bandwidth
- Cache response e confronta con precedente per detect changes

### Excel VBA Integration Template

**Module: MerlinoRealtimeAPI.bas**
```vba
Option Explicit

' Configurazione API
Private Const API_BASE As String = "https://192.168.124.133/api/v2/merlino/realtime/"
Private Const API_KEY As String = "ADMIN123"

' Funzione generica per chiamate API
Function CallMerlinoRealtimeAPI(endpoint As String, Optional params As String = "") As Object
    Dim http As Object
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")  ' Supporto HTTPS
    
    Dim url As String
    url = API_BASE & endpoint
    If params <> "" Then url = url & "?" & params
    
    http.Open "GET", url, False
    http.setRequestHeader "KEY", API_KEY
    http.setOption 2, 13056  ' Ignora errori certificato SSL self-signed
    http.send
    
    If http.Status = 200 Then
        Set CallMerlinoRealtimeAPI = JsonConverter.ParseJson(http.responseText)
    Else
        Err.Raise vbObjectError + 1000, "Merlino API", "HTTP " & http.Status & ": " & http.responseText
    End If
End Function

' Get complete metrics snapshot
Function GetOperationsMetrics(Optional windowMinutes As Integer = 60) As Object
    Set GetOperationsMetrics = CallMerlinoRealtimeAPI("operations/metrics", "windowMinutes=" & windowMinutes)
End Function

' Get operations list (lightweight)
Function GetOperations() As Object
    Set GetOperations = CallMerlinoRealtimeAPI("operations")
End Function

' Get agents list (lightweight)
Function GetAgents() As Object
    Set GetAgents = CallMerlinoRealtimeAPI("agents")
End Function

' Get timeline events
Function GetTimeline(Optional windowMinutes As Integer = 60, Optional limit As Integer = 20) As Object
    Set GetTimeline = CallMerlinoRealtimeAPI("timeline", "windowMinutes=" & windowMinutes & "&limit=" & limit)
End Function

' Update dashboard con metrics complete
Sub UpdateDashboard()
    On Error GoTo ErrorHandler
    
    Dim metrics As Object
    Set metrics = GetOperationsMetrics(60)
    
    ' Global Stats
    Range("B2").Value = metrics("globalStats")("totalOps")
    Range("B3").Value = metrics("globalStats")("totalAbilities")
    Range("B4").Value = metrics("globalStats")("successRate")
    Range("B5").Value = metrics("globalStats")("runningOps")
    Range("B6").Value = metrics("globalStats")("totalAgents")
    
    ' Operations table
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Dashboard")
    Dim startRow As Integer: startRow = 10
    
    ws.Range("A" & startRow & ":F100").ClearContents
    
    Dim i As Integer
    For i = 0 To metrics("operations").Count - 1
        Dim op As Object
        Set op = metrics("operations")(i)
        
        ws.Range("A" & startRow + i).Value = op("name")
        ws.Range("B" & startRow + i).Value = op("state")
        ws.Range("C" & startRow + i).Value = op("total_abilities")
        ws.Range("D" & startRow + i).Value = op("success_count")
        ws.Range("E" & startRow + i).Value = op("error_count")
        ws.Range("F" & startRow + i).Value = Join(op("tcodes"), ", ")
    Next i
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Error updating dashboard: " & Err.Description, vbCritical
End Sub
```

**Usage in Excel:**
```vba
' Polling timer (run every 5 seconds)
Sub StartPolling()
    Application.OnTime Now + TimeValue("00:00:05"), "UpdateDashboard"
End Sub

' Stop polling
Sub StopPolling()
    On Error Resume Next
    Application.OnTime Now + TimeValue("00:00:05"), "UpdateDashboard", , False
End Sub
```

### Best Practices

1. **Use Specific Endpoints**: Preferisci `/operations`, `/agents`, `/timeline` separati invece di `/operations/metrics` completo se non serve tutto
2. **Cache Responses**: Confronta con precedente response per detect changes
3. **Error Handling**: Gestisci 401 (invalid key) e 500 (server error) con retry logic
4. **Timeout**: Setta timeout HTTP a 10s (evita freeze in Excel se server lento)
5. **Background Refresh**: Usa Application.OnTime per polling asincrono senza bloccare UI
6. **Conditional Formatting**: Colora celle in base a state (running=green, paused=yellow, stopped=red)
7. **Charts**: Usa globalStats per sparkline/gauge charts (successRate, runningOps)
8. **Timeline**: Mostra ultimi 10 eventi in scrollable list con timestamp formattato

---

## Changelog

**Version 1.0 - 2025-12-27**
- Initial release
- 4 endpoints: operations/metrics, operations, agents, timeline
- Support for windowMinutes, includeTimeline, timelineLimit, limit parameters
- GlobalRealtimeStats calculation with successRate
- Timeline filtering by windowMinutes
- Excel VBA integration template

---

## Support & Contact

**Repository:** https://github.com/x3m-ai/morgana-arsenal (private)
**Base Project:** MITRE Caldera (https://github.com/mitre/caldera)
**License:** Apache 2.0

Per domande o problemi, contatta il maintainer del progetto.

---

**Last Updated:** December 27, 2025
**API Version:** 1.0
**Maintainer:** Morgana (@x3m-ai)
