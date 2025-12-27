# Merlino API - Operations Health Matrix & Drilldown

**Version:** 1.0  
**Last Updated:** December 27, 2025

## Overview

The **Operations Health Matrix API** provides a comprehensive health monitoring system for operations in Morgana Arsenal. It consists of two complementary endpoints:

1. **Matrix Endpoint** - Provides a render-ready matrix (rows × columns = cells) with health scores, rates, and severity classification
2. **Drilldown Endpoint** - Provides detailed drill-down into a specific operation's execution items with optional command/output inclusion

These APIs are designed for the **Merlino Excel Add-in** to provide real-time operation health monitoring without client-side computation.

---

## Authentication

All requests require API key authentication:

```http
KEY: ADMIN123
```

---

## Endpoint 1: Operations Health Matrix

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/operations-health-matrix`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | ISO-8601 | now - 7d | Start of time window (e.g., `2025-12-20T00:00:00Z`) |
| `to` | ISO-8601 | now | End of time window (e.g., `2025-12-27T23:59:59Z`) |
| `groupBy` | string | `operation` | Grouping mode: `operation`, `operation_agent`, `operation_group` |
| `scope` | string | `all` | Filter scope: `all`, `picked` (future use) |
| `include` | CSV string | `cells,operationSummaries` | Include sections: `cells`, `operationSummaries`, `topIssues` |
| `limit` | int | 200 | Maximum number of rows to return |
| `minSamples` | int | 1 | Minimum execution count to include a row |

### Response Format

```typescript
{
  version: string;                    // API version (e.g., "1.0")
  generated_at: string;               // ISO-8601 timestamp of generation
  time_window: {
    from: string;                     // ISO-8601 start
    to: string;                       // ISO-8601 end
  };
  groupBy: string;                    // Applied grouping mode
  thresholds: {
    stale_minutes: number;            // Threshold for stale operations (30)
    warn_error_rate: number;          // Warning threshold for errors (0.05)
    bad_error_rate: number;           // Bad threshold for errors (0.2)
    warn_timeout_rate: number;        // Warning threshold for timeouts (0.05)
    bad_timeout_rate: number;         // Bad threshold for timeouts (0.2)
    min_samples: number;              // Minimum samples required
  };
  rows: Array<{
    row_id: string;                   // Unique row identifier (e.g., "op:uuid" or "op:uuid:operation_agent:paw")
    operation_id: string;             // Operation UUID
    operation_name: string;           // Operation name
    agent_paw: string | null;         // Agent PAW (if groupBy=operation_agent)
    agent_host: string | null;        // Agent hostname
    agent_group: string | null;       // Agent group (if groupBy=operation_group)
    last_seen: string | null;         // ISO-8601 timestamp of last event
  }>;
  columns: Array<{
    column_id: string;                // Column identifier (health_score, success_rate, etc.)
    label: string;                    // Human-readable label
    kind: string;                     // Data type: score, count, time
    description?: string;             // Optional description
  }>;
  cells: Array<{
    row_id: string;                   // Reference to row
    column_id: string;                // Reference to column
    value: number | string | null;    // Cell value (depends on column kind)
    severity: string;                 // Severity: "good", "warn", "bad", "nodata"
    details?: {                       // Additional details (health_score cell only)
      sample_size: number;            // Total executions
      success: number;                // Success count
      fail: number;                   // Failure count
      timeout: number;                // Timeout count
      pending: number;                // Pending count
      success_rate: number;           // Success rate (0-1)
      error_rate: number;             // Error rate (0-1)
      timeout_rate: number;           // Timeout rate (0-1)
      last_event_at: string | null;   // ISO-8601 timestamp
      stale: boolean;                 // Is operation stale?
      top_reasons: string[];          // Array of reasons (e.g., ["error_rate=0.50", "stale"])
    };
  }>;
  operationSummaries: Array<{
    operation_id: string;             // Operation UUID
    operation_name: string;           // Operation name
    state: string;                    // Operation state (running, finished, paused)
    group: string;                    // Operation group
    agent_count: number;              // Number of agents
    counts: {
      success: number;
      fail: number;
      timeout: number;
      pending: number;
      total: number;
    };
    rates: {
      success_rate: number | null;    // 0-1
      error_rate: number | null;      // 0-1
      timeout_rate: number | null;    // 0-1
    };
    last_event_at: string | null;     // ISO-8601
    freshness_minutes: number | null; // Minutes since last event
    health: {
      severity: string;               // "good", "warn", "bad", "nodata"
      score: number | null;           // 0-100
      reasons: string[];              // Array of reasons
    };
  }>;
  topIssues?: Array<any>;             // Optional (future use)
}
```

### Health Score Calculation

The health score is computed using the following formula:

```
health_score = 100 
             - (error_rate × 100 × 1.0)      // Error penalty (weight 1.0)
             - (timeout_rate × 100 × 0.7)    // Timeout penalty (weight 0.7)
             - (stale ? 20 : 0)              // Stale penalty (fixed -20)
```

**Clamped to:** `[0, 100]`

### Severity Classification

| Severity | Condition |
|----------|-----------|
| `nodata` | `total executions < minSamples` |
| `bad` | `error_rate >= 0.2` OR `timeout_rate >= 0.2` OR `stale = true` |
| `warn` | `error_rate >= 0.05` OR `timeout_rate >= 0.05` |
| `good` | All other cases |

**Example:**
- Operation with 50% error rate, stale (4456 minutes old):
  - Health score: `100 - (0.5 × 100) - 20 = 30`
  - Severity: `bad`
  - Reasons: `["error_rate=0.50", "stale"]`

### Example Request

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/operations-health-matrix?limit=10&minSamples=1" \
  -H "KEY: ADMIN123"
```

### Example Response (Excerpt)

```json
{
  "version": "1.0",
  "generated_at": "2025-12-27T00:27:37.140827+00:00",
  "time_window": {
    "from": "2025-12-20T00:27:37.140827+00:00",
    "to": "2025-12-27T00:27:37.140827+00:00"
  },
  "groupBy": "operation",
  "thresholds": {
    "stale_minutes": 30,
    "warn_error_rate": 0.05,
    "bad_error_rate": 0.2,
    "warn_timeout_rate": 0.05,
    "bad_timeout_rate": 0.2,
    "min_samples": 1
  },
  "rows": [
    {
      "row_id": "op:5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "operation_name": "ops1",
      "agent_paw": null,
      "agent_host": null,
      "agent_group": null,
      "last_seen": "2025-12-23T22:11:39+00:00"
    }
  ],
  "columns": [
    {"column_id": "health_score", "label": "Health", "kind": "score", "description": "0..100 score"},
    {"column_id": "success_rate", "label": "Success Rate", "kind": "score"},
    {"column_id": "error_rate", "label": "Error Rate", "kind": "score"},
    {"column_id": "timeout_rate", "label": "Timeout Rate", "kind": "score"},
    {"column_id": "last_event_at", "label": "Last Event", "kind": "time"},
    {"column_id": "freshness_minutes", "label": "Freshness (min)", "kind": "count"}
  ],
  "cells": [
    {
      "row_id": "op:5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "column_id": "health_score",
      "value": 30,
      "severity": "bad",
      "details": {
        "sample_size": 2,
        "success": 1,
        "fail": 1,
        "timeout": 0,
        "pending": 0,
        "success_rate": 0.5,
        "error_rate": 0.5,
        "timeout_rate": 0.0,
        "last_event_at": "2025-12-23T22:11:39+00:00",
        "stale": true,
        "top_reasons": ["error_rate=0.50", "stale"]
      }
    },
    {
      "row_id": "op:5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "column_id": "success_rate",
      "value": 50.0,
      "severity": "bad"
    },
    {
      "row_id": "op:5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "column_id": "error_rate",
      "value": 50.0,
      "severity": "bad"
    }
  ],
  "operationSummaries": [
    {
      "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "operation_name": "ops1",
      "state": "running",
      "group": "",
      "agent_count": 1,
      "counts": {
        "success": 1,
        "fail": 1,
        "timeout": 0,
        "pending": 0,
        "total": 2
      },
      "rates": {
        "success_rate": 0.5,
        "error_rate": 0.5,
        "timeout_rate": 0.0
      },
      "last_event_at": "2025-12-23T22:11:39+00:00",
      "freshness_minutes": 4456,
      "health": {
        "severity": "bad",
        "score": 30,
        "reasons": ["error_rate=0.50", "stale"]
      }
    }
  ]
}
```

---

## Endpoint 2: Operation Health Details (Drilldown)

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/operations-health-matrix/operation/{operation_id}`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation_id` | string | Yes | UUID of the operation to drill down into |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | ISO-8601 | now - 7d | Start of time window |
| `to` | ISO-8601 | now | End of time window |
| `limit` | int | 500 | Maximum number of items to return |
| `offset` | int | 0 | Pagination offset |
| `status` | CSV string | (all) | Filter by status: `success`, `fail`, `timeout`, `pending`, `unknown` |
| `agent_paw` | string | (all) | Filter by agent PAW |
| `includeOutput` | boolean | false | Include output field in items |
| `outputFormat` | string | `decoded` | Output format: `decoded` (with parsed JSON) or `raw` (base64) |
| `includeCommand` | boolean | false | Include command field in items |
| `commandFormat` | string | `decoded` | Command format: `decoded` (plain text) or `raw` (base64) |

### Response Format

```typescript
{
  operation_id: string;               // Operation UUID
  operation_name: string;             // Operation name
  time_window: {
    from: string;                     // ISO-8601 start
    to: string;                       // ISO-8601 end
  };
  summary: {
    counts: {
      success: number;
      fail: number;
      timeout: number;
      pending: number;
      total: number;
    };
    rates: {
      success_rate: number | null;    // 0-1
      error_rate: number | null;      // 0-1
      timeout_rate: number | null;    // 0-1
    };
    last_event_at: string | null;     // ISO-8601
  };
  items: Array<{
    item_id: string;                  // Unique identifier (e.g., "link:uuid")
    occurred_at: string | null;       // ISO-8601 timestamp
    status: string;                   // "success", "fail", "timeout", "pending", "unknown"
    ability_id: string | null;        // Ability UUID
    ability_name: string | null;      // Ability name
    technique_id: string | null;      // MITRE ATT&CK technique ID (e.g., "T1082")
    tactic: string | null;            // MITRE ATT&CK tactic (e.g., "discovery")
    agent_paw: string | null;         // Agent PAW
    agent_host: string | null;        // Agent hostname
    agent_group: string | null;       // Agent group
    executor: string | null;          // Executor name (e.g., "psh", "cmd", "sh")
    platform: string | null;          // Platform (e.g., "windows", "linux")
    source: string;                   // Data source (always "caldera")
    command?: {                       // Optional (if includeCommand=true)
      encoding: string;               // "plain" or "base64"
      value: string;                  // Command text or base64
    };
    output?: {                        // Optional (if includeOutput=true)
      encoding: string;               // "json-base64", "plain", or "base64"
      value: string;                  // Base64 encoded output
      parsed?: {                      // Optional (if outputFormat=decoded and JSON parseable)
        stdout: string;               // Standard output
        stderr: string;               // Standard error
        exit_code: number;            // Exit code
      };
    };
    error_hint?: string;              // Optional error hint (e.g., "exit_code=1")
  }>;
  paging: {
    limit: number;                    // Applied limit
    offset: number;                   // Applied offset
    total: number;                    // Total items matching filters
  };
}
```

### Status Normalization

| Caldera Status | Normalized Status | Description |
|----------------|-------------------|-------------|
| 0 | `success` | Execution completed successfully |
| 1 | `fail` | Execution failed |
| 124 | `timeout` | Execution timed out |
| -1 | `pending` | Execution pending/in progress |
| Other | `unknown` | Unknown status |

### Example Request 1: Basic Drilldown

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/operations-health-matrix/operation/5a9a344c-d65a-4153-9259-0aa34a7d93dc" \
  -H "KEY: ADMIN123"
```

### Example Request 2: With Output and Command (Decoded)

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/operations-health-matrix/operation/5a9a344c-d65a-4153-9259-0aa34a7d93dc?includeOutput=true&includeCommand=true&outputFormat=decoded&commandFormat=decoded" \
  -H "KEY: ADMIN123"
```

### Example Request 3: Filtered by Status

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/operations-health-matrix/operation/5a9a344c-d65a-4153-9259-0aa34a7d93dc?status=fail,timeout&includeOutput=true" \
  -H "KEY: ADMIN123"
```

### Example Request 4: Paginated

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/operations-health-matrix/operation/5a9a344c-d65a-4153-9259-0aa34a7d93dc?limit=50&offset=0" \
  -H "KEY: ADMIN123"
```

### Example Response (Excerpt)

```json
{
  "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
  "operation_name": "ops1",
  "time_window": {
    "from": "2025-12-20T00:29:35.823770+00:00",
    "to": "2025-12-27T00:29:35.823770+00:00"
  },
  "summary": {
    "counts": {
      "success": 1,
      "fail": 1,
      "timeout": 0,
      "pending": 0,
      "total": 2
    },
    "rates": {
      "success_rate": 0.5,
      "error_rate": 0.5,
      "timeout_rate": 0.0
    },
    "last_event_at": "2025-12-23T22:11:39+00:00"
  },
  "items": [
    {
      "item_id": "link:39d1fb65-7670-4a1b-ae08-82e9f6e6b83f",
      "occurred_at": "2025-12-23T22:11:01+00:00",
      "status": "success",
      "ability_id": "a1b2c3d4-test-merlino-0001",
      "ability_name": "Merlino - Test Agent",
      "technique_id": "T1082",
      "tactic": "discovery",
      "agent_paw": "puqadh",
      "agent_host": "WINDOWSPC01",
      "agent_group": "red",
      "executor": "psh",
      "platform": null,
      "source": "caldera",
      "command": {
        "encoding": "plain",
        "value": "Get-ComputerInfo | Select-Object CsName, OsName, OsArchitecture, WindowsVersion, CsDomain | Format-List"
      },
      "output": {
        "encoding": "json-base64",
        "value": "eyJzdGRvdXQ...",
        "parsed": {
          "stdout": "\r\n\r\nCsName         : WINDOWSPC01\r\nOsName         : Microsoft Windows 11 Pro for Workstations\r\nOsArchitecture : 64-bit\r\nWindowsVersion : 2009\r\nCsDomain       : WORKGROUP\r\n\r\n\r\n\r\n",
          "stderr": "",
          "exit_code": 0
        }
      }
    },
    {
      "item_id": "link:f89b0ece-486a-415e-b8da-cd872b4959cf",
      "occurred_at": "2025-12-23T22:11:39+00:00",
      "status": "fail",
      "ability_id": "6fe8f0c1c175fd3a5fb1d384114f5ecf",
      "ability_name": "Decode Eicar File and Write to File",
      "technique_id": "T1027.013",
      "tactic": "defense-evasion",
      "agent_paw": "puqadh",
      "agent_host": "WINDOWSPC01",
      "agent_group": "red",
      "executor": "psh",
      "platform": null,
      "source": "caldera",
      "command": {
        "encoding": "plain",
        "value": "$encodedString = \"WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo=\"; $bytes = [System.Convert]::FromBase64String($encodedString); $decodedString = [System.Text.Encoding]::UTF8.GetString($bytes); $decodedString | Out-File T1027.013_decodedEicar.txt"
      },
      "output": {
        "encoding": "json-base64",
        "value": "eyJzdGRvdXQ...",
        "parsed": {
          "stdout": "WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo= : The term \r\n'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo=' is not recognized as \r\nthe name of a cmdlet, function, script file, or operable program...",
          "stderr": "",
          "exit_code": 0
        }
      }
    }
  ],
  "paging": {
    "limit": 5,
    "offset": 0,
    "total": 2
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid parameter: limit must be a positive integer"
}
```

### 404 Not Found
```json
{
  "error": "Operation 5a9a344c-d65a-4153-9259-0aa34a7d93dc not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Unexpected error occurred",
  "traceback": "Traceback (most recent call last)..."
}
```

---

## Performance Expectations

- **Matrix Endpoint:** Typically responds in 200-500ms for 10-50 operations
- **Drilldown Endpoint:** Typically responds in 100-300ms for 100-500 items
- **With Output Decryption:** Add ~50-100ms per item for output decryption
- **Pagination:** Use `limit` and `offset` for large datasets (recommended `limit=500`)

---

## Integration Notes for Merlino Excel Add-in

### Matrix Visualization
1. **Heatmap Grid**: Use `severity` field to color cells:
   - `good` → Green
   - `warn` → Yellow
   - `bad` → Red
   - `nodata` → Gray
2. **Tooltip**: Display `details.top_reasons` on cell hover
3. **Drilldown**: Click on cell → call drilldown endpoint with `operation_id` from `row_id`

### Drilldown Visualization
1. **Table View**: Display items in sortable/filterable table
2. **Pagination**: Implement "Load More" or pagination controls using `limit`/`offset`
3. **Output Decoding**: When `includeOutput=true` and `outputFormat=decoded`, display `parsed.stdout` in monospace font
4. **Command Display**: Show decoded command in collapsible section
5. **Status Icons**: 
   - `success` → ✅ Green checkmark
   - `fail` → ❌ Red X
   - `timeout` → ⏱️ Yellow clock
   - `pending` → ⏳ Gray hourglass

### Refresh Strategy
- **Matrix**: Auto-refresh every 30-60 seconds
- **Drilldown**: Refresh on demand or when matrix updates
- **Filters**: Persist filters in localStorage for user convenience

---

## Changelog

**Version 1.0** (December 27, 2025):
- Initial implementation of Operations Health Matrix endpoint
- Initial implementation of Operation Health Details (Drilldown) endpoint
- Health score calculation with error/timeout/stale penalties
- Severity classification (good/warn/bad/nodata)
- GroupBy support (operation, operation_agent, operation_group)
- Optional output/command inclusion with decoded/raw formats
- Pagination support for drilldown
- Comprehensive filtering (status, agent_paw)

---

## Contact & Support

- **Repository**: https://github.com/x3m-ai/morgana-arsenal (private)
- **Base Project**: MITRE Caldera (https://github.com/mitre/caldera)
- **License**: Apache 2.0 (see LICENSE and NOTICE files)

For Merlino integration questions, contact the Morgana Arsenal team.
