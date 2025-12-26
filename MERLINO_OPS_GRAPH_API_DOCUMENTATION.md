# Merlino Ops Graph API - Complete Documentation

**Date**: 2025-12-26  
**Version**: 1.0  
**Base URL**: `http://192.168.124.133:8888/api/v2` or `http://localhost:8888/api/v2`  
**Authentication**: Header `KEY: ADMIN123`

---

## Overview

The Merlino Ops Graph API provides **6 endpoints** designed specifically for the Merlino "Tests & Operations" dashboard. These APIs enable:
- **Hotspot identification** (failing operations, troubled agents, stuck operations)
- **Graph-ready data** for force-directed visualizations
- **Actionable drilldowns** into problems, operations, and agents
- **Intervention actions** (pause/stop operations, tag agents)

All APIs follow the specification in `ops-graph-api-spec.md`.

---

## API 1 (CORE) — Ops Graph Aggregation

### `POST /merlino/ops-graph`

**Purpose**: Return an operational force-graph dataset with nodes (operations, agents, problems) and edges (agent-operation, operation-problem, agent-problem).

**Request Body**:
```json
{
  "window_minutes": 60,
  "operation_ids": [],
  "agent_paws": [],
  "include_nodes": ["operation", "agent", "problem"],
  "include_edges": ["agent_operation", "operation_problem", "agent_problem"],
  "limits": { "max_nodes": 250, "max_edges": 800 },
  "thresholds": { "min_edge_weight": 1 },
  "grouping": "tactic_technique"
}
```

**Parameters**:
- `window_minutes` (int): Time window in minutes (default: 60)
- `operation_ids` (array): Filter by specific operation IDs (empty = all)
- `agent_paws` (array): Filter by specific agent PAWs (empty = all)
- `include_nodes` (array): Node types to include (`operation`, `agent`, `problem`)
- `include_edges` (array): Edge types to include (`agent_operation`, `operation_problem`, `agent_problem`)
- `limits.max_nodes` (int): Maximum nodes to return
- `limits.max_edges` (int): Maximum edges to return (trims weakest first)
- `thresholds.min_edge_weight` (int): Minimum edge weight to include
- `grouping` (string): Problem grouping strategy (`tactic_technique`)

**Response**:
```json
{
  "meta": {
    "window_minutes": 60,
    "generated": "2025-12-26T12:34:56Z"
  },
  "nodes": {
    "operations": [
      {
        "id": "op-uuid",
        "name": "Operation A",
        "state": "running",
        "started": "2025-12-26T11:00:00Z",
        "last_activity": "2025-12-26T12:30:00Z",
        "counts": { "success": 120, "failed": 9, "running": 3 },
        "agents_count": 4
      }
    ],
    "agents": [
      {
        "paw": "abc123",
        "host": "PC-01",
        "platform": "windows",
        "last_seen": "2025-12-26T12:33:10Z",
        "status": "active",
        "counts": { "success": 60, "failed": 7, "running": 2 }
      }
    ],
    "problems": [
      {
        "id": "problem:execution:T1059",
        "kind": "tactic_technique",
        "tactic": "execution",
        "technique": "T1059",
        "label": "execution / T1059",
        "counts": { "failed": 8, "running": 0, "success": 0 }
      }
    ]
  },
  "edges": {
    "agent_operation": [
      {
        "source": "agent:abc123",
        "target": "op:op-uuid",
        "weight": 32,
        "counts": { "success": 25, "failed": 6, "running": 1 }
      }
    ],
    "operation_problem": [
      {
        "source": "op:op-uuid",
        "target": "problem:execution:T1059",
        "weight": 6,
        "counts": { "failed": 6 }
      }
    ],
    "agent_problem": [
      {
        "source": "agent:abc123",
        "target": "problem:execution:T1059",
        "weight": 6,
        "counts": { "failed": 6 }
      }
    ]
  }
}
```

**Status Normalization**:
- Link status `0` → `success`
- Link status `1` or `124` → `failed`
- Link status `-1` or others → `running`

**cURL Example**:
```bash
curl -X POST http://localhost:8888/api/v2/merlino/ops-graph \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{
    "window_minutes": 60,
    "include_nodes": ["operation", "agent", "problem"],
    "include_edges": ["agent_operation", "operation_problem", "agent_problem"]
  }'
```

---

## API 2 (CORE) — Problem Drilldown

### `GET /merlino/ops-graph/problem-details`

**Purpose**: Return top agents, top operations, and recent events for a specific problem.

**Query Parameters**:
- `problem_id` (required): Problem identifier (e.g., `problem:execution:T1059`)
- `window_minutes` (required): Time window in minutes
- `limit` (optional, default: 100): Maximum events to return

**Response**:
```json
{
  "problem": {
    "id": "problem:execution:T1059",
    "tactic": "execution",
    "technique": "T1059"
  },
  "top_agents": [
    {
      "paw": "abc123",
      "host": "PC-01",
      "failed": 6,
      "running": 1,
      "success": 0,
      "last_seen": "2025-12-26T12:33:10Z"
    }
  ],
  "top_operations": [
    {
      "id": "op-uuid",
      "name": "Operation A",
      "failed": 6,
      "running": 0,
      "success": 0,
      "state": "running"
    }
  ],
  "recent_events": [
    {
      "ts": "2025-12-26T12:31:00Z",
      "operation_id": "op-uuid",
      "operation": "Operation A",
      "agent": "abc123",
      "host": "PC-01",
      "ability": "Some Ability Name",
      "tactic": "execution",
      "technique": "T1059",
      "status": "failed"
    }
  ]
}
```

**cURL Example**:
```bash
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/problem-details?problem_id=problem:execution:T1059&window_minutes=60&limit=100"
```

---

## API 3 (CORE) — Operation Drilldown

### `GET /merlino/ops-graph/operation-details`

**Purpose**: Return per-agent involvement, top problems, and recent events for an operation.

**Query Parameters**:
- `operation_id` (required): Operation UUID
- `window_minutes` (required): Time window in minutes
- `limit` (optional, default: 100): Maximum events to return

**Response**:
```json
{
  "operation": {
    "id": "op-uuid",
    "name": "Operation A",
    "state": "running",
    "started": "2025-12-26T11:00:00Z",
    "last_activity": "2025-12-26T12:30:00Z",
    "counts": { "success": 120, "failed": 9, "running": 3 }
  },
  "agents": [
    {
      "paw": "abc123",
      "host": "PC-01",
      "platform": "windows",
      "last_seen": "2025-12-26T12:33:10Z",
      "counts": { "success": 25, "failed": 6, "running": 1 }
    }
  ],
  "top_problems": [
    { "problem_id": "problem:execution:T1059", "failed": 6 }
  ],
  "recent_events": [
    {
      "ts": "2025-12-26T12:31:00Z",
      "agent": "abc123",
      "ability": "X",
      "tactic": "execution",
      "technique": "T1059",
      "status": "failed"
    }
  ]
}
```

**cURL Example**:
```bash
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/operation-details?operation_id=xxx&window_minutes=60&limit=100"
```

---

## API 4 (CORE) — Agent Drilldown

### `GET /merlino/ops-graph/agent-details`

**Purpose**: Return operations, top problems, and recent events for a specific agent.

**Query Parameters**:
- `paw` (required): Agent PAW identifier
- `window_minutes` (required): Time window in minutes
- `limit` (optional, default: 100): Maximum events to return

**Response**:
```json
{
  "agent": {
    "paw": "abc123",
    "host": "PC-01",
    "platform": "windows",
    "last_seen": "2025-12-26T12:33:10Z",
    "status": "active"
  },
  "operations": [
    {
      "id": "op-uuid",
      "name": "Operation A",
      "state": "running",
      "counts": { "success": 25, "failed": 6, "running": 1 }
    }
  ],
  "top_problems": [
    { "problem_id": "problem:execution:T1059", "failed": 6 }
  ],
  "recent_events": [
    {
      "ts": "2025-12-26T12:31:00Z",
      "operation_id": "op-uuid",
      "ability": "X",
      "tactic": "execution",
      "technique": "T1059",
      "status": "failed"
    }
  ]
}
```

**cURL Example**:
```bash
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/agent-details?paw=abc123&window_minutes=60&limit=100"
```

---

## API 5 (OPTIONAL) — Intervention Actions

### `POST /merlino/ops-actions`

**Purpose**: Allow Merlino UI to trigger operational actions.

**Supported Actions**:

### 1. Pause Operation
**Request**:
```json
{
  "action": "pause_operation",
  "operation_id": "op-uuid"
}
```

**Response**:
```json
{
  "ok": true,
  "message": "paused",
  "operation_id": "op-uuid"
}
```

### 2. Stop Operation
**Request**:
```json
{
  "action": "stop_operation",
  "operation_id": "op-uuid"
}
```

**Response**:
```json
{
  "ok": true,
  "message": "stopped",
  "operation_id": "op-uuid"
}
```

### 3. Tag Agent
**Request**:
```json
{
  "action": "tag_agent",
  "paw": "abc123",
  "tag": "needs-attention"
}
```

**Response**:
```json
{
  "ok": true,
  "message": "tagged as needs-attention",
  "paw": "abc123",
  "tag": "needs-attention"
}
```

**cURL Examples**:
```bash
# Pause operation
curl -X POST http://localhost:8888/api/v2/merlino/ops-actions \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{"action": "pause_operation", "operation_id": "xxx"}'

# Stop operation
curl -X POST http://localhost:8888/api/v2/merlino/ops-actions \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{"action": "stop_operation", "operation_id": "xxx"}'

# Tag agent
curl -X POST http://localhost:8888/api/v2/merlino/ops-actions \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{"action": "tag_agent", "paw": "abc123", "tag": "needs-attention"}'
```

---

## API 6 (OPTIONAL) — UI Route Resolver

### `GET /merlino/ui-routes`

**Purpose**: Return UI URL patterns so Merlino can open Morgana pages without guessing.

**Response**:
```json
{
  "base_url": "http://192.168.124.133:8888",
  "routes": {
    "operation": "/operations/{id}",
    "agent": "/agents/{paw}",
    "search": "/search?q={query}"
  }
}
```

**Usage Example**:
```javascript
// Get UI routes
const routesData = await fetch('http://192.168.124.133:8888/api/v2/merlino/ui-routes', {
  headers: { 'KEY': 'ADMIN123' }
}).then(r => r.json());

// Open operation page
const operationUrl = routesData.base_url + routesData.routes.operation.replace('{id}', 'op-uuid');
window.open(operationUrl);
```

**cURL Example**:
```bash
curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/merlino/ui-routes
```

---

## Error Handling

All APIs return errors in the following format:

**Error Response**:
```json
{
  "error": "Description of the error",
  "traceback": "Full Python traceback (DEBUG mode only)"
}
```

**Common HTTP Status Codes**:
- `200 OK`: Successful request
- `400 Bad Request`: Missing or invalid parameters
- `404 Not Found`: Resource not found (operation, agent, etc.)
- `500 Internal Server Error`: Server-side error (check logs)

---

## Implementation Notes

### Status Normalization
All APIs normalize Caldera link statuses to three values:
- `success`: Link completed successfully (status = 0)
- `failed`: Link failed or timed out (status = 1 or 124)
- `running`: Link is pending or paused (status = -1 or other)

### Time Window
All APIs accept `window_minutes` to filter events:
- Only links with `finish` timestamp within the window are included
- Uses UTC timezone for all timestamps
- Format: ISO 8601 (e.g., `2025-12-26T12:34:56Z`)

### Problem Grouping
Problems are grouped by `tactic` and `technique`:
- Problem ID format: `problem:{tactic}:{technique}`
- Example: `problem:execution:T1059`
- Stable IDs enable caching and drilldown

### Edge Weights
- `agent_operation` edges: Sum of all statuses (success + failed + running)
- `operation_problem` edges: Sum of failed events only
- `agent_problem` edges: Sum of failed events only

### Limits and Thresholds
- `max_edges`: Enforced by sorting edges by weight descending and trimming
- `min_edge_weight`: Edges with weight below threshold are excluded
- `max_nodes`: Not currently enforced (returns all matching nodes)

---

## Integration Guide

### Minimal Viable Implementation
For fastest results, start with:
1. **API 1**: `POST /merlino/ops-graph` (graph data)
2. **API 2**: `GET /merlino/ops-graph/problem-details` (problem drilldown)

Everything else can follow incrementally.

### JavaScript Integration Example
```javascript
// Fetch ops graph data
async function fetchOpsGraph(windowMinutes = 60) {
  const response = await fetch('http://192.168.124.133:8888/api/v2/merlino/ops-graph', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'KEY': 'ADMIN123'
    },
    body: JSON.stringify({
      window_minutes: windowMinutes,
      include_nodes: ['operation', 'agent', 'problem'],
      include_edges: ['agent_operation', 'operation_problem', 'agent_problem']
    })
  });
  
  return await response.json();
}

// Fetch problem details
async function fetchProblemDetails(problemId, windowMinutes = 60) {
  const url = new URL('http://192.168.124.133:8888/api/v2/merlino/ops-graph/problem-details');
  url.searchParams.set('problem_id', problemId);
  url.searchParams.set('window_minutes', windowMinutes);
  url.searchParams.set('limit', 100);
  
  const response = await fetch(url, {
    headers: { 'KEY': 'ADMIN123' }
  });
  
  return await response.json();
}

// Pause operation
async function pauseOperation(operationId) {
  const response = await fetch('http://192.168.124.133:8888/api/v2/merlino/ops-actions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'KEY': 'ADMIN123'
    },
    body: JSON.stringify({
      action: 'pause_operation',
      operation_id: operationId
    })
  });
  
  return await response.json();
}
```

### Python Integration Example
```python
import requests

BASE_URL = 'http://192.168.124.133:8888/api/v2'
HEADERS = {'KEY': 'ADMIN123'}

# Fetch ops graph
def fetch_ops_graph(window_minutes=60):
    response = requests.post(
        f'{BASE_URL}/merlino/ops-graph',
        headers=HEADERS,
        json={
            'window_minutes': window_minutes,
            'include_nodes': ['operation', 'agent', 'problem'],
            'include_edges': ['agent_operation', 'operation_problem', 'agent_problem']
        }
    )
    return response.json()

# Fetch problem details
def fetch_problem_details(problem_id, window_minutes=60, limit=100):
    response = requests.get(
        f'{BASE_URL}/merlino/ops-graph/problem-details',
        headers=HEADERS,
        params={
            'problem_id': problem_id,
            'window_minutes': window_minutes,
            'limit': limit
        }
    )
    return response.json()

# Pause operation
def pause_operation(operation_id):
    response = requests.post(
        f'{BASE_URL}/merlino/ops-actions',
        headers=HEADERS,
        json={
            'action': 'pause_operation',
            'operation_id': operation_id
        }
    )
    return response.json()
```

---

## Testing

### Quick Test All APIs
```bash
# API 1 - Ops Graph
curl -X POST http://localhost:8888/api/v2/merlino/ops-graph \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{"window_minutes": 60}'

# API 2 - Problem Details (needs real problem_id)
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/problem-details?problem_id=problem:execution:T1059&window_minutes=60"

# API 3 - Operation Details (needs real operation_id)
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/operation-details?operation_id=xxx&window_minutes=60"

# API 4 - Agent Details (needs real paw)
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/agent-details?paw=abc123&window_minutes=60"

# API 5 - Ops Actions (will return 404 for fake IDs)
curl -X POST http://localhost:8888/api/v2/merlino/ops-actions \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{"action": "pause_operation", "operation_id": "test"}'

# API 6 - UI Routes
curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/merlino/ui-routes
```

---

## Changelog

**Version 1.0** (2025-12-26):
- Initial implementation of all 6 APIs
- Full spec compliance with `ops-graph-api-spec.md`
- Status normalization (success/failed/running)
- Time window filtering
- Problem grouping by tactic+technique
- Edge weight calculation and trimming
- All drilldown endpoints implemented
- Intervention actions (pause/stop/tag)
- UI route resolver

---

## Support

- **Repository**: https://github.com/x3m-ai/morgana-arsenal (private)
- **Specification**: `ops-graph-api-spec.md`
- **Server Logs**: `/tmp/morgana-startup.log`
- **Base Project**: MITRE Caldera (https://github.com/mitre/caldera)

**Last Updated**: December 26, 2025  
**Maintainer**: Morgana (@x3m-ai)
