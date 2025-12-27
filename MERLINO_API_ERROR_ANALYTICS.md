# Merlino API - Error Analytics & Troubleshooting

**Version:** 1.0  
**Last Updated:** December 27, 2025

## Overview

The **Error Analytics & Troubleshooting API** provides comprehensive error tracking, analysis, and troubleshooting capabilities for Morgana Arsenal operations. It enables identification of failure patterns, root cause analysis, and remediation guidance.

This API is designed for the **Merlino Excel Add-in** to provide actionable insights into operation failures without requiring manual log analysis.

---

## Base Configuration

- **Base URL:** `{MORGANA_BASE_URL}` (example: `https://192.168.124.133:8888`)
- **Authentication:** HTTP header `KEY: <apiKey>`
- **Content-Type:** `application/json`
- **Namespace:** `/api/v2/merlino/analytics/error-analytics/*`
- **Timestamps:** ISO-8601 UTC (e.g., `2025-12-27T14:05:22Z`)

---

## Common Concepts

### Severity

String enum: `good` | `warn` | `bad` | `nodata`

### Execution Status (normalized)

String enum (lowercase): `success` | `fail` | `timeout` | `pending` | `unknown`

### Time Window

All endpoints accept optional query parameters:
- `from?: string` (ISO-8601 timestamp)
- `to?: string` (ISO-8601 timestamp)

If omitted, server applies default window (last 7 days) and returns effective window in response.

### Pagination

Standard pagination query parameters:
- `limit?: number` (default `250`, max `1000`)
- `offset?: number` (default `0`)

Paged responses return:
```json
{
  "paging": {
    "limit": 250,
    "offset": 0,
    "total": 1844
  }
}
```

### Payload Control (Optional Heavy Fields)

To prevent large payloads, command/output are excluded by default.

Query flags:
- `includeCommand?: boolean` (default `false`)
- `includeOutput?: boolean` (default `false`)
- `commandFormat?: "decoded" | "raw"` (default `decoded`)
- `outputFormat?: "decoded" | "raw"` (default `decoded`)

### Command Encoding

```typescript
{
  encoding: "plain" | "base64";
  value: string;
}
```

### Output Encoding

```typescript
{
  encoding: "plain" | "base64" | "json-base64";
  value: string;              // Base64 encoded
  parsed?: {                  // Present when encoding=json-base64 and parsing succeeded
    stdout: string;
    stderr: string;
    exit_code: number;
  };
}
```

---

## Event Item Schema

Core unit for troubleshooting is an "execution event":

```typescript
{
  item_id: string;                   // Unique identifier (e.g., "evt-abc123" or "link:uuid")
  occurred_at: string;               // ISO-8601 timestamp
  
  status: string;                    // "success" | "fail" | "timeout" | "pending" | "unknown"
  reason: string;                    // Normalized reason (see Reason Normalization section)
  severity: string;                  // "good" | "warn" | "bad" | "nodata"
  
  operation_id: string;              // Operation UUID
  operation_name: string;            // Operation name
  
  ability_id: string | null;         // Ability UUID
  ability_name: string | null;       // Ability name
  tactic: string | null;             // MITRE ATT&CK tactic
  technique_id: string | null;       // MITRE ATT&CK technique ID (e.g., "T1003")
  
  agent_paw: string | null;          // Agent PAW
  agent_host: string | null;         // Agent hostname
  agent_group: string | null;        // Agent group
  executor: string | null;           // Executor (e.g., "psh", "cmd", "sh")
  platform: string | null;           // Platform (e.g., "windows", "linux")
  plugin: string | null;             // Plugin name
  
  command?: {                        // Optional (if includeCommand=true)
    encoding: string;
    value: string;
  };
  output?: {                         // Optional (if includeOutput=true)
    encoding: string;
    value: string;
    parsed?: {
      stdout: string;
      stderr: string;
      exit_code: number;
    };
  };
  
  error_hint: string | null;         // Remediation hint
  source: string;                    // "caldera" | "morgana" | "excel" | "unknown"
}
```

**Notes:**
- `item_id` and `occurred_at` are always present
- `command` and `output` only present when respective `include` flags are `true`

---

## Endpoint 1: Overview / KPIs

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/overview`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | ISO-8601 | now - 7d | Start of time window |
| `to` | ISO-8601 | now | End of time window |
| `groupBy` | string | `day` | Trend grouping: `hour`, `day`, `week` |
| `operation_id` | string | (all) | Filter by operation UUID |
| `agent_paw` | string | (all) | Filter by agent PAW |
| `group` | string | (all) | Filter by agent group |

### Response 200

```typescript
{
  time_window: {
    from: string;                    // ISO-8601
    to: string;                      // ISO-8601
  };
  totals: {
    events: number;                  // Total executions
    errors: number;                  // Failed executions
    timeouts: number;                // Timed out executions
    success: number;                 // Successful executions
    unknown: number;                 // Unknown status executions
  };
  rates: {
    error_rate: number;              // 0-1
    timeout_rate: number;            // 0-1
    success_rate: number;            // 0-1
  };
  trend: Array<{
    bucket: string;                  // Bucket identifier (e.g., "2025-12-21" for day)
    events: number;
    errors: number;
    timeouts: number;
    success: number;
  }>;
  top_reasons: Array<{
    reason: string;                  // Normalized reason
    count: number;                   // Occurrence count
  }>;
}
```

### Example Request

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/overview?groupBy=day" \
  -H "KEY: ADMIN123"
```

### Example Response

```json
{
  "time_window": {
    "from": "2025-12-20T00:00:00Z",
    "to": "2025-12-27T00:00:00Z"
  },
  "totals": {
    "events": 12034,
    "errors": 1844,
    "timeouts": 210,
    "success": 9980,
    "unknown": 0
  },
  "rates": {
    "error_rate": 0.1532,
    "timeout_rate": 0.0174,
    "success_rate": 0.8294
  },
  "trend": [
    {
      "bucket": "2025-12-21",
      "events": 1500,
      "errors": 210,
      "timeouts": 22,
      "success": 1268
    },
    {
      "bucket": "2025-12-22",
      "events": 1700,
      "errors": 260,
      "timeouts": 30,
      "success": 1410
    }
  ],
  "top_reasons": [
    { "reason": "command_not_found", "count": 312 },
    { "reason": "access_denied", "count": 188 }
  ]
}
```

---

## Endpoint 2: Breakdown (Aggregations)

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/breakdown`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | ISO-8601 | now - 7d | Start of time window |
| `to` | ISO-8601 | now | End of time window |
| `dimension` | string | **REQUIRED** | Dimension: `status`, `operation`, `agent`, `group`, `ability`, `executor`, `platform`, `plugin`, `reason` |
| `metric` | string | `count` | Metric: `count`, `rate` |
| `operation_id` | string | (all) | Filter by operation |
| `agent_paw` | string | (all) | Filter by agent |
| `group` | string | (all) | Filter by group |
| `ability_id` | string | (all) | Filter by ability |
| `status` | CSV string | (all) | Filter by status (e.g., `fail,timeout`) |

### Response 200

```typescript
{
  time_window: {
    from: string;
    to: string;
  };
  dimension: string;                 // Applied dimension
  metric: string;                    // Applied metric
  items: Array<{
    key: string;                     // Dimension value
    label: string;                   // Human-readable label
    count: number;                   // Count of events
    rate: number;                    // Rate (0-1)
  }>;
}
```

### Example Request

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/breakdown?dimension=reason&metric=count" \
  -H "KEY: ADMIN123"
```

### Example Response

```json
{
  "time_window": {
    "from": "2025-12-20T00:00:00Z",
    "to": "2025-12-27T00:00:00Z"
  },
  "dimension": "reason",
  "metric": "count",
  "items": [
    {
      "key": "access_denied",
      "label": "Access denied",
      "count": 188,
      "rate": 0.102
    },
    {
      "key": "command_not_found",
      "label": "Command not found",
      "count": 312,
      "rate": 0.169
    }
  ]
}
```

---

## Endpoint 3: Top Offenders

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/top-offenders`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | ISO-8601 | now - 7d | Start of time window |
| `to` | ISO-8601 | now | End of time window |
| `entity` | string | **REQUIRED** | Entity type: `operation`, `agent`, `ability`, `group` |
| `metric` | string | `error_rate` | Metric: `error_count`, `timeout_count`, `error_rate`, `combined_bad_rate` |
| `limit` | int | 50 | Maximum results |
| `minSamples` | int | 25 | Minimum execution count to include |

### Response 200

```typescript
{
  time_window: {
    from: string;
    to: string;
  };
  entity: string;                    // Applied entity type
  metric: string;                    // Applied metric
  items: Array<{
    entity_id: string;               // Entity identifier
    entity_name: string;             // Entity name
    sample_size: number;             // Total executions
    counts: {
      success: number;
      fail: number;
      timeout: number;
      pending: number;
      total: number;
    };
    rates: {
      success_rate: number;          // 0-1
      error_rate: number;            // 0-1
      timeout_rate: number;          // 0-1
    };
    severity: string;                // "good" | "warn" | "bad"
    top_reasons: string[];           // Array of most common reasons
  }>;
}
```

### Example Request

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/top-offenders?entity=ability&metric=error_rate&limit=10" \
  -H "KEY: ADMIN123"
```

---

## Endpoint 4: Events Search

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/events/search`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | ISO-8601 | now - 7d | Start of time window |
| `to` | ISO-8601 | now | End of time window |
| `limit` | int | 250 | Maximum results (max 1000) |
| `offset` | int | 0 | Pagination offset |
| `status` | CSV string | (all) | Filter by status |
| `operation_id` | string | (all) | Filter by operation |
| `agent_paw` | string | (all) | Filter by agent |
| `group` | string | (all) | Filter by group |
| `ability_id` | string | (all) | Filter by ability |
| `executor` | string | (all) | Filter by executor |
| `platform` | string | (all) | Filter by platform |
| `plugin` | string | (all) | Filter by plugin |
| `reason` | string | (all) | Filter by reason |
| `q` | string | (none) | Free text search (max 200 chars) |
| `includeCommand` | boolean | false | Include command field |
| `includeOutput` | boolean | false | Include output field |
| `commandFormat` | string | `decoded` | Command format |
| `outputFormat` | string | `decoded` | Output format |

### Response 200

```typescript
{
  time_window: {
    from: string;
    to: string;
  };
  paging: {
    limit: number;
    offset: number;
    total: number;
  };
  items: Array<EventItem>;           // See Event Item Schema above
}
```

### Example Request

```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/events/search?status=fail&includeOutput=true&limit=10" \
  -H "KEY: ADMIN123"
```

---

## Endpoint 5: Operation Drilldown

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/operation/{operation_id}`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation_id` | string | Yes | Operation UUID |

### Query Parameters

Same as Events Search, plus:
- Default `status` filter: `fail,timeout` (recommended)

### Response 200

```typescript
{
  operation_id: string;
  operation_name: string;
  time_window: {
    from: string;
    to: string;
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
      success_rate: number;
      error_rate: number;
      timeout_rate: number;
    };
    last_event_at: string;
  };
  items: Array<EventItem>;
  paging: {
    limit: number;
    offset: number;
    total: number;
  };
}
```

---

## Endpoint 6: Signatures (Clustering)

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/signatures`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | ISO-8601 | now - 7d | Start of time window |
| `to` | ISO-8601 | now | End of time window |
| `limit` | int | 100 | Maximum signatures |
| Filters | (same as Events Search) | (all) | Same filter options |

### Response 200

```typescript
{
  time_window: {
    from: string;
    to: string;
  };
  items: Array<{
    signature_id: string;            // Signature identifier
    reason: string;                  // Normalized reason
    title: string;                   // Human-readable title
    count: number;                   // Occurrence count
    top_entities: {
      abilities: Array<{
        ability_id: string;
        name: string;
        count: number;
      }>;
      agents: Array<{
        agent_paw: string;
        host: string;
        count: number;
      }>;
    };
    example_item_id: string;         // Example event ID for reference
    first_seen_at: string;           // ISO-8601
    last_seen_at: string;            // ISO-8601
    hint: string;                    // Remediation hint
  }>;
}
```

---

## Endpoint 7: Signature Drilldown

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/signature/{signature_id}`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `signature_id` | string | Yes | Signature identifier |

### Query Parameters

Same as Events Search (pagination + include flags).

### Response 200

```typescript
{
  signature_id: string;
  time_window: {
    from: string;
    to: string;
  };
  summary: {
    reason: string;
    title: string;
    count: number;
  };
  items: Array<EventItem>;
  paging: {
    limit: number;
    offset: number;
    total: number;
  };
}
```

---

## Endpoint 8: Hints Knowledge Base

### Request

**Method:** `GET`  
**Path:** `/api/v2/merlino/analytics/error-analytics/hints`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reason` | string | (all) | Filter by reason |
| `signature_id` | string | (all) | Filter by signature |

### Response 200

```typescript
{
  items: Array<{
    id: string;                      // Hint identifier
    reason: string;                  // Applicable reason
    title: string;                   // Hint title
    steps: string[];                 // Array of remediation steps
    links: Array<{
      label: string;
      url: string;
    }>;
  }>;
}
```

### Example Response

```json
{
  "items": [
    {
      "id": "hint-access-denied-1",
      "reason": "access_denied",
      "title": "Access denied",
      "steps": [
        "Verify agent privilege level",
        "Try running ability with elevated executor",
        "Check endpoint protection logs"
      ],
      "links": [
        {
          "label": "Windows privilege elevation notes",
          "url": "https://docs.microsoft.com/..."
        }
      ]
    }
  ]
}
```

---

## Reason Normalization

The backend normalizes error reasons into stable categories for clustering:

### Recommended Reason Values

| Reason | Description | Example Indicators |
|--------|-------------|-------------------|
| `command_not_found` | Command/cmdlet not recognized | "not recognized as", "command not found" |
| `access_denied` | Insufficient permissions | "Access is denied", "permission denied" |
| `file_not_found` | File/path not found | "file not found", "cannot find" |
| `network_unreachable` | Network connectivity issue | "network", "unreachable", "timeout" |
| `timeout` | Execution timed out | status=124 |
| `parser_error` | Server-side parse error | Decode/parse failures |
| `dependency_missing` | Missing module/library | "module", "dll not found", "import error" |
| `amsi_block` | AMSI/EDR blocked execution | "amsi", "antimalware", "blocked" |
| `edr_block` | EDR blocked execution | "defender", "quarantine" |
| `invalid_argument` | Invalid command syntax | "invalid argument", "syntax error" |
| `unknown` | Unknown/unclassified | Fallback |

### Mapping Strategy

1. **Status-based:** status=124 → `timeout`, status=-1 → `pending`, status=0 → `success`
2. **Output analysis:** Parse stdout/stderr for keyword patterns
3. **Fallback:** If no match, return `unknown`

---

## Error Handling

### 400 Bad Request
Invalid parameters (bad enum, invalid time window, limit too high).

```json
{
  "error": "Invalid parameter: dimension must be one of: status, operation, agent, ..."
}
```

### 401/403 Unauthorized
Missing or invalid `KEY` header.

### 404 Not Found
Entity not found (operation, signature).

```json
{
  "error": "Operation 5a9a344c-d65a-4153-9259-0aa34a7d93dc not found"
}
```

### 422 Unprocessable Entity
Invalid params (e.g., missing required `dimension`).

```json
{
  "error": "Missing required parameter: dimension"
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

## Performance Recommendations

1. **Default `includeOutput/includeCommand` to `false`** for list endpoints
2. **Default `limit` to `250`, max `1000`**
3. **Cap `q` (free text search) length at 200 characters**
4. **Use pagination** for large result sets
5. **Cache signature clustering** results (recommended TTL: 5 minutes)

---

## Integration Notes for Merlino Excel Add-in

### Dashboard View
- Use **Overview endpoint** to display KPIs: total errors, error rate, trend chart
- Chart `trend` array as line/bar chart (x=bucket, y=errors)
- Show `top_reasons` as pie chart or horizontal bar chart

### Drill-Down Workflow
1. **Identify Problem**: Use **Breakdown endpoint** with `dimension=ability` to find problematic abilities
2. **Analyze Root Cause**: Use **Top Offenders endpoint** with `entity=ability` and `minSamples=50`
3. **Investigate Events**: Use **Events Search endpoint** with filters (status=fail, ability_id=X)
4. **Review Details**: Display `error_hint` and `output.parsed.stderr` in detail pane

### Signature-Based Troubleshooting
1. Call **Signatures endpoint** to get clusters of similar errors
2. Display signatures sorted by `count` (descending)
3. User clicks signature → call **Signature Drilldown endpoint** to see all events
4. Display remediation from **Hints KB endpoint** based on `reason`

### Search Experience
- Implement free text search with `q` parameter (searches command/output)
- Combine with filters (operation, agent, status) for faceted search
- Use `includeOutput=true` only when user expands an item (on-demand loading)

---

## Real-World Examples

### Example 1: Quick Health Check

**Request:**
```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/overview?groupBy=day" \
  -H "KEY: ADMIN123"
```

**Response:**
```json
{
  "time_window": {
    "from": "2025-12-20T00:00:00+00:00",
    "to": "2025-12-27T23:59:59+00:00"
  },
  "totals": {
    "events": 2,
    "errors": 1,
    "timeouts": 0,
    "success": 1,
    "unknown": 0
  },
  "rates": {
    "error_rate": 0.5,
    "timeout_rate": 0.0,
    "success_rate": 0.5
  },
  "trend": [
    {
      "bucket": "2025-12-23",
      "events": 2,
      "errors": 1,
      "timeouts": 0,
      "success": 1
    }
  ],
  "top_reasons": [
    {"reason": "command_not_found", "count": 1}
  ]
}
```

### Example 2: Find Problematic Abilities

**Request:**
```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/breakdown?dimension=ability" \
  -H "KEY: ADMIN123"
```

**Response:**
```json
{
  "time_window": {
    "from": "2025-12-20T01:22:42+00:00",
    "to": "2025-12-27T01:22:42+00:00"
  },
  "dimension": "ability",
  "metric": "count",
  "items": [
    {
      "key": "Merlino - Test Agent",
      "label": "Merlino - Test Agent",
      "count": 1,
      "rate": 0.5
    },
    {
      "key": "Decode Eicar File and Write to File",
      "label": "Decode Eicar File And Write To File",
      "count": 1,
      "rate": 0.5
    }
  ]
}
```

### Example 3: Investigate Failed Execution with Full Context

**Request:**
```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/events/search?status=fail&limit=1&includeCommand=true&includeOutput=true" \
  -H "KEY: ADMIN123"
```

**Response:**
```json
{
  "time_window": {
    "from": "2025-12-20T01:22:57+00:00",
    "to": "2025-12-27T01:22:57+00:00"
  },
  "paging": {"limit": 1, "offset": 0, "total": 1},
  "items": [
    {
      "item_id": "link:f89b0ece-486a-415e-b8da-cd872b4959cf",
      "occurred_at": "2025-12-23T22:11:39Z",
      "status": "fail",
      "reason": "command_not_found",
      "severity": "bad",
      "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "operation_name": "ops1",
      "ability_id": "6fe8f0c1c175fd3a5fb1d384114f5ecf",
      "ability_name": "Decode Eicar File and Write to File",
      "tactic": "defense-evasion",
      "technique_id": "T1027.013",
      "agent_paw": "puqadh",
      "agent_host": "WINDOWSPC01",
      "agent_group": "red",
      "executor": "psh",
      "platform": null,
      "plugin": "atomic",
      "error_hint": "Verify command exists or install required dependencies",
      "source": "caldera",
      "command": {
        "encoding": "plain",
        "value": "$encodedString = \"WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo=\"; $bytes = [System.Convert]::FromBase64String($encodedString); $decodedString = [System.Text.Encoding]::UTF8.GetString($bytes); $decodedString | Out-File T1027.013_decodedEicar.txt"
      },
      "output": {
        "encoding": "json-base64",
        "value": "eyJzdGRvdXQ...",
        "parsed": {
          "stdout": "WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo= : The term \r\n'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo=' is not recognized as \r\nthe name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was \r\nincluded, verify that the path is correct and try again...",
          "stderr": "",
          "exit_code": 0
        }
      }
    }
  ]
}
```

### Example 4: Pattern Detection with Signatures

**Request:**
```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/signatures?limit=5" \
  -H "KEY: ADMIN123"
```

**Response:**
```json
{
  "time_window": {
    "from": "2025-12-20T01:22:24+00:00",
    "to": "2025-12-27T01:22:24+00:00"
  },
  "items": [
    {
      "signature_id": "sig-ec420626",
      "reason": "command_not_found",
      "title": "Command Not Found",
      "count": 1,
      "top_entities": {
        "abilities": [
          {
            "ability_id": "6fe8f0c1c175fd3a5fb1d384114f5ecf",
            "name": "Decode Eicar File and Write to File",
            "count": 1
          }
        ],
        "agents": [
          {
            "agent_paw": "puqadh",
            "host": "WINDOWSPC01",
            "count": 1
          }
        ]
      },
      "example_item_id": "link:f89b0ece-486a-415e-b8da-cd872b4959cf",
      "first_seen_at": "2025-12-23T22:11:39+00:00",
      "last_seen_at": "2025-12-23T22:11:39+00:00",
      "hint": "Verify command exists or install required dependencies"
    }
  ]
}
```

### Example 5: Get Remediation Guidance

**Request:**
```bash
curl -X GET "http://192.168.124.133:8888/api/v2/merlino/analytics/error-analytics/hints?reason=command_not_found" \
  -H "KEY: ADMIN123"
```

**Response:**
```json
{
  "items": [
    {
      "id": "hint-command-not-found-1",
      "reason": "command_not_found",
      "title": "Command Not Found",
      "steps": [
        "Verify command exists on target system (check PATH)",
        "Install required dependencies or tools",
        "Use absolute path to command binary",
        "Check for typos in command name",
        "Verify correct shell/executor is being used (cmd vs psh vs sh)"
      ],
      "links": [
        {
          "label": "PowerShell cmdlet reference",
          "url": "https://docs.microsoft.com/powershell/"
        },
        {
          "label": "Linux command reference",
          "url": "https://man7.org/"
        }
      ]
    }
  ]
}
```

---

## Changelog

**Version 1.0** (December 27, 2025):
- Initial API specification for Error Analytics & Troubleshooting
- 8 endpoints: Overview, Breakdown, Top Offenders, Events Search, Operation Drilldown, Signatures, Signature Drilldown, Hints KB
- Reason normalization with 11 standard categories
- Comprehensive filtering, pagination, and payload control
- Signature clustering for similar error grouping
- Hints knowledge base for remediation guidance
- Real-world examples from production testing

---

## Contact & Support

- **Repository**: https://github.com/x3m-ai/morgana-arsenal (private)
- **Base Project**: MITRE Caldera (https://github.com/mitre/caldera)
- **License**: Apache 2.0 (see LICENSE and NOTICE files)

For Merlino integration questions, contact the Morgana Arsenal team.
