# Morgana Arsenal — Merlino Ops Graph API Spec

Date: 2025-12-26

## Goal
Provide an **operations-focused**, graph-ready API for Merlino “Tests & Operations” so the UI can:
- Identify **hotspots** (what is failing, where, why)
- Identify **agents in trouble** (inactive, high failures)
- Identify **operations stuck** (running too long, high running count)
- Offer **actionable drilldowns** and optional **intervention actions** (pause/stop/tag)

This specification is intentionally “made-to-measure” to avoid client-side reconstruction from flat link rows.

## Concepts

### Event
An execution record for a single ability/link.

Minimum event fields required by this spec:
- `ts` (timestamp)
- `operation_id`, `operation` (name)
- `agent` (paw), `host`
- `ability` (name)
- `tactic` (string)
- `technique` (technique id, e.g., `T1059`)
- `status` (normalized: `success` | `failed` | `running`)

### Problem node
A stable identifier representing a recurring operational issue.

Default grouping: **tactic + technique**.
- `problem_id`: `problem:{tactic}:{technique}` (e.g., `problem:execution:T1059`)

Optionally, future grouping modes may include:
- `tactic_technique_ability`
- `ability`

## Status normalization
Server MUST normalize statuses to:
- `success`
- `failed`
- `running`

No numeric codes (`"0"|"1"|"-1"`) should leak into these endpoints.

## API 1 (CORE) — Ops Graph Aggregation

### POST `/api/v2/merlino/ops-graph`

#### Purpose
Return an **operational force-graph dataset** with:
- Nodes: operations, agents, problems
- Edges: agent-operation, operation-problem, agent-problem

This enables a "command map": operations and agents connected to **problem hubs**.

#### Request
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

#### Response
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

#### Notes
- `problem.id` MUST be stable for caching and drilldown.
- `limits.max_edges` MAY be enforced by trimming weakest edges first.
- `thresholds.min_edge_weight` applied after aggregation.

## API 2 (CORE) — Problem Drilldown

### GET `/api/v2/merlino/ops-graph/problem-details`

#### Purpose
When the user clicks a problem node, return:
- top agents involved
- top operations involved
- recent events sample for immediate troubleshooting

#### Query Params
- `problem_id` (required)
- `window_minutes` (required)
- `limit` (optional, default 100)

Example:
`/api/v2/merlino/ops-graph/problem-details?problem_id=problem:execution:T1059&window_minutes=60&limit=100`

#### Response
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

## API 3 (CORE) — Operation Drilldown

### GET `/api/v2/merlino/ops-graph/operation-details`

#### Purpose
When the user clicks an operation node, return:
- per-agent involvement
- top problems for this operation
- recent event sample

#### Query Params
- `operation_id` (required)
- `window_minutes` (required)
- `limit` (optional, default 100)

#### Response
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

## API 4 (CORE) — Agent Drilldown

### GET `/api/v2/merlino/ops-graph/agent-details`

#### Purpose
When the user clicks an agent node, return:
- operations the agent contributed to
- top problems caused by this agent
- recent event sample

#### Query Params
- `paw` (required)
- `window_minutes` (required)
- `limit` (optional, default 100)

#### Response
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

## API 5 (OPTIONAL) — Intervention Actions

### POST `/api/v2/merlino/ops-actions`

#### Purpose
Allow Merlino UI to trigger operational actions (with confirmations and logging).

#### Request (examples)
Pause operation:
```json
{ "action": "pause_operation", "operation_id": "op-uuid" }
```

Stop operation:
```json
{ "action": "stop_operation", "operation_id": "op-uuid" }
```

Tag agent (needs-attention):
```json
{ "action": "tag_agent", "paw": "abc123", "tag": "needs-attention" }
```

#### Response
```json
{ "ok": true, "message": "paused", "operation_id": "op-uuid" }
```

## API 6 (OPTIONAL) — UI Route Resolver

### GET `/api/v2/merlino/ui-routes`

#### Purpose
Return UI URL patterns so Merlino can open Morgana pages without guessing.

#### Response
```json
{
  "base_url": "https://morgana.local",
  "routes": {
    "operation": "/operations/{id}",
    "agent": "/agents/{paw}",
    "search": "/search?q={query}"
  }
}
```

## Minimal viable implementation (fastest path)
If you want the quickest end-to-end win:
1) Implement **API 1**: `POST /api/v2/merlino/ops-graph`
2) Implement **API 2**: `GET /api/v2/merlino/ops-graph/problem-details`

Everything else can follow incrementally.

## Notes for server-side aggregation
- Aggregate by time window (last X minutes)
- Derive `last_activity` as max(ts) per entity
- Edge weights = event counts (or failure counts for problem edges)
- Trim edges by smallest `weight` to respect `max_edges`

---
End of spec.
