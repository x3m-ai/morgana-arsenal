# Ops Graph API - Test Calls (Morgana)

This document lists the exact HTTP calls used to validate the Ops Graph feature used in **Tests & Operations**.

## Context

- **Base URL currently tested:** `https://192.168.124.133`
- **Auth header:** `KEY: ADMIN123`
- **Primary endpoint:** `POST /api/v2/merlino/ops-graph`
- **Purpose:** return an Ops Graph suitable for rendering in the `OpsCommandGraph` view.

## What is being tested

1. **Connectivity + authentication** (Server reachable, TLS OK, KEY accepted)
2. **Response shape** (Does it return the expected JSON schema?)
3. **Data availability** (Non-empty nodes/edges)
4. **Drilldown endpoints** used when clicking nodes in the graph

---

## Call 1 - Fetch Ops Graph (MAIN)

### Goal
Fetch the graph data used by the UI to show the ops graph.

### HTTP
- **Method:** `POST`
- **URL:** `https://192.168.124.133/api/v2/merlino/ops-graph`
- **Headers:**
  - `Content-Type: application/json`
  - `KEY: ADMIN123`
- **Body:** (example)
```json
{
  "options": {
    "includeAgents": true,
    "includeProblems": true,
    "maxNodes": 400,
    "maxEdges": 1200
  }
}
```

### PowerShell (exact)
```powershell
$uri = "https://192.168.124.133/api/v2/merlino/ops-graph"
$headers = @{ "Content-Type"="application/json"; "KEY"="ADMIN123" }
$body = (@{
  options = @{
    includeAgents   = $true
    includeProblems = $true
    maxNodes        = 400
    maxEdges        = 1200
  }
} | ConvertTo-Json -Depth 10)

Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -TimeoutSec 30
```

### Expected response (frontend expectation)
The current frontend service `fetchOpsGraph()` expects:
```json
{
  "nodes": [
    { "id": "...", "type": "agent|operation|problem", "label": "..." }
  ],
  "edges": [
    { "id": "...", "source": "...", "target": "...", "type": "agent_in_operation|operation_has_problem" }
  ]
}
```

---

## Drilldown calls (DETAILS)

These are called by the UI when clicking a node to show details.

### Call 2 - Problem details

- **Method:** `GET`
- **URL template:**
  - `https://192.168.124.133/api/v2/merlino/ops-graph/problem-details?problem_id=PROBLEM_ID_HERE&window_minutes=1440&limit=100`

```powershell
$uri = "https://192.168.124.133/api/v2/merlino/ops-graph/problem-details?problem_id=PROBLEM_ID_HERE&window_minutes=1440&limit=100"
Invoke-RestMethod -Method Get -Uri $uri -Headers @{ "Content-Type"="application/json"; "KEY"="ADMIN123" } -TimeoutSec 30
```

### Call 3 - Operation details

- **Method:** `GET`
- **URL template:**
  - `https://192.168.124.133/api/v2/merlino/ops-graph/operation-details?operation_id=OPERATION_ID_HERE&window_minutes=1440&limit=100`

```powershell
$uri = "https://192.168.124.133/api/v2/merlino/ops-graph/operation-details?operation_id=OPERATION_ID_HERE&window_minutes=1440&limit=100"
Invoke-RestMethod -Method Get -Uri $uri -Headers @{ "Content-Type"="application/json"; "KEY"="ADMIN123" } -TimeoutSec 30
```

### Call 4 - Agent details

- **Method:** `GET`
- **URL template:**
  - `https://192.168.124.133/api/v2/merlino/ops-graph/agent-details?agent_paw=AGENT_PAW_HERE&window_minutes=1440&limit=100`

```powershell
$uri = "https://192.168.124.133/api/v2/merlino/ops-graph/agent-details?agent_paw=AGENT_PAW_HERE&window_minutes=1440&limit=100"
Invoke-RestMethod -Method Get -Uri $uri -Headers @{ "Content-Type"="application/json"; "KEY"="ADMIN123" } -TimeoutSec 30
```

---

## Notes

- If Call 1 returns HTTP 200 but no `nodes`/`edges` (or returns a different JSON structure), the UI will not be able to render the graph until:
  - an adapter is added client-side, or
  - Morgana returns the expected `{ nodes, edges }` format.

- Runtime log file path used by Office debugging:
  - `C:\Users\ninoc\AppData\Local\Temp\OfficeAddins.log.txt`
