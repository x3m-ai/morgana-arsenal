# Merlino Ops Graph API - Link Details Extension

## Date
December 26, 2025 (16:00 UTC)

## Feature Summary
Extended the 3 Merlino Ops Graph drilldown API endpoints to optionally include per-link telemetry (command + output) for detailed debugging and analysis in the Merlino Excel Add-in.

## Implementation

### New Query Parameters (All 3 Endpoints)

Added **optional** query parameters to:
- `GET /api/v2/merlino/ops-graph/operation-details`
- `GET /api/v2/merlino/ops-graph/agent-details`
- `GET /api/v2/merlino/ops-graph/problem-details`

**Parameters:**
1. `include_links` (optional, default `false`)
   - When `true`, response includes `recent_links` array
   - When `false` (default), response identical to previous behavior
   
2. `output_max_chars` (optional, default `4000`, min `0`, max `50000`)
   - Maximum characters returned in each link's `output` field
   - If `0`, output field is empty string
   - Enforces cap at 50,000 chars
   
3. `output_format` (optional, default `raw`, allowed: `raw` | `base64`)
   - `raw`: UTF-8 string output
   - `base64`: Base64-encoded output

### New Response Fields

When `include_links=true`, responses include:

1. **`recent_links`** (array of `OpsGraphRecentLink` objects)
2. **`links_meta`** (object with metadata)

```json
{
  "recent_events": [...],
  "recent_links": [
    {
      "link_id": "f89b0ece-486a-415e-b8da-cd872b4959cf",
      "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
      "operation_name": "ops1",
      "agent_paw": "puqadh",
      "host": "WINDOWSPC01",
      "platform": "windows",
      "ability_id": "6fe8f0c1c175fd3a5fb1d384114f5ecf",
      "ability_name": "Decode Eicar File and Write to File",
      "tactic": "defense-evasion",
      "technique": "T1027.013",
      "status": "failed",
      "command": "$encodedString = ...",
      "command_is_plaintext": true,
      "output": "",
      "output_truncated": false,
      "executed_at": "2025-12-23T22:11:02Z",
      "finished_at": "2025-12-23T22:11:39Z"
    }
  ],
  "links_meta": {
    "include_links": true,
    "output_max_chars": 4000,
    "output_format": "raw"
  }
}
```

### OpsGraphRecentLink Data Model

**Complete field mapping:**

| Field | Type | Description |
|-------|------|-------------|
| `link_id` | string | Caldera link UUID |
| `operation_id` | string | Raw operation UUID |
| `operation_name` | string | Human-readable operation name |
| `agent_paw` | string | Agent PAW identifier |
| `host` | string | Hostname where link executed |
| `platform` | string | OS platform (windows, linux, darwin) |
| `ability_id` | string | Caldera ability UUID |
| `ability_name` | string | Human-readable ability name |
| `tactic` | string | MITRE ATT&CK tactic |
| `technique` | string | MITRE ATT&CK technique ID (e.g., T1027.013) |
| `status` | string | Normalized: `success`, `failed`, `running`, `timeout`, `unknown` |
| `command` | string | Command executed (plaintext if available, else base64) |
| `command_is_plaintext` | boolean | `true` if `command` is plaintext, `false` if encoded |
| `output` | string | Command output (truncated/encoded per params) |
| `output_truncated` | boolean | `true` if output was truncated due to `output_max_chars` |
| `executed_at` | string | ISO 8601 timestamp when link started (Caldera `decide` field) |
| `finished_at` | string | ISO 8601 timestamp when link completed (Caldera `finish` field) |

### Status Normalization

Caldera numeric status codes mapped to strings:
- `0` → `success`
- `1` → `failed`
- `124` → `timeout`
- `-1` → `running`
- Other → `unknown`

### Helper Function

Added `build_ops_graph_recent_link()` function (line ~32-165):
- Extracts all link details from Caldera link object
- Prefers `plaintext_command` over encoded `command`
- Handles output truncation and encoding
- Safe extraction of ability details (tactic/technique)
- Resolves agent platform from operation agents list

## Code Changes

**File:** `app/api/v2/handlers/operation_api.py`

### 1. New Helper Function (line ~32)
```python
def build_ops_graph_recent_link(link, operation, output_max_chars=4000, output_format='raw'):
    """Build OpsGraphRecentLink object from Caldera link."""
    # 130+ lines of extraction logic
    return {...}  # Complete OpsGraphRecentLink dict
```

### 2. Modified Endpoints

#### A) `merlino_problem_details()` (line ~1800-1980)
- Parse new query params
- Initialize `recent_links_data = []`
- In link loop: call `build_ops_graph_recent_link()` when `include_links=true`
- Add `recent_links` and `links_meta` to response

#### B) `merlino_operation_details()` (line ~1990-2185)
- Same changes as problem_details
- Links filtered to operation

#### C) `merlino_agent_details()` (line ~2185-2365)
- Same changes as problem_details
- Links filtered to agent PAW

**Total lines added:** ~400 lines (helper + modifications)

## Testing

### Test 1: Backward Compatibility
```bash
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/agent-details?agent_paw=puqadh&window_minutes=10080"

# Response: Same as before (no recent_links)
{
  "agent": {...},
  "operations": [...],
  "top_problems": [...],
  "recent_events": [...]
}
```

### Test 2: With Link Details
```bash
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/agent-details?agent_paw=puqadh&window_minutes=10080&include_links=true&output_max_chars=500"

# Response: Includes recent_links and links_meta
{
  "agent": {...},
  "operations": [...],
  "top_problems": [...],
  "recent_events": [...],
  "recent_links": [
    {
      "link_id": "...",
      "command": "...",
      "output": "...",
      ...
    }
  ],
  "links_meta": {
    "include_links": true,
    "output_max_chars": 500,
    "output_format": "raw"
  }
}
```

### Test 3: Output Omission
```bash
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/agent-details?agent_paw=puqadh&window_minutes=10080&include_links=true&output_max_chars=0"

# All links have empty output field
```

### Test 4: Base64 Output
```bash
curl -H "KEY: ADMIN123" \
  "http://localhost:8888/api/v2/merlino/ops-graph/agent-details?agent_paw=puqadh&window_minutes=10080&include_links=true&output_format=base64"

# Output fields are base64-encoded
```

### Test Results
✅ All 3 endpoints tested with:
- `include_links=false` (default) - backward compatible
- `include_links=true` - returns link details
- `output_max_chars=0` - omits output
- `output_max_chars=200` - truncates long outputs
- `output_format=base64` - encodes output

✅ All required fields present in `OpsGraphRecentLink`
✅ `command_is_plaintext` correctly set based on source
✅ Limits and caps enforced (limit≤200, output_max_chars≤50000)

## Merlino Integration

**Expected Usage:**
```typescript
// In Merlino Excel Add-in
const response = await fetch(
  `${API_BASE}/api/v2/merlino/ops-graph/agent-details?` +
  `agent_paw=${paw}&window_minutes=20160&limit=25&` +
  `include_links=true&output_max_chars=4000&output_format=raw`,
  {
    headers: { 'KEY': 'ADMIN123' }
  }
);

const data = await response.json();

// Display in drilldown panel
data.recent_links.forEach(link => {
  console.log(`Command: ${link.command}`);
  console.log(`Output: ${link.output}`);
  console.log(`Status: ${link.status}`);
});
```

## Performance Considerations

- **Default behavior unchanged**: No performance impact when `include_links=false`
- **With links enabled**: Adds ~0.2-0.5KB per link (without output)
- **With output**: Can add significant payload (bounded by `output_max_chars`)
- **Recommended**: Use `limit` parameter to control result size
- **Safe defaults**: 
  - `limit=25-100` for UI display
  - `output_max_chars=4000` for typical outputs
  - Set `output_max_chars=0` if output not needed

## Future Enhancements

Possible future additions (not implemented):
- Filtering links by status (`?status=failed`)
- Pagination for large result sets
- Compressed output (`output_format=gzip`)
- Partial output (first/last N lines only)

## Git Commit

```
Add per-link telemetry to Merlino Ops Graph drilldown APIs

- New optional parameters: include_links, output_max_chars, output_format
- Returns recent_links array with full link details (command, output, etc.)
- Fully backward compatible (opt-in via include_links=true)
- Enforces sane limits (max 200 links, 50K chars output)
- Helper function build_ops_graph_recent_link() handles extraction
- Affects: operation-details, agent-details, problem-details
- Tested with all parameter combinations
```

## Related Files

- `app/api/v2/handlers/operation_api.py` (main implementation)
- `ops-graph-api-spec.md` (original specification)
- `ops-graph-test-calls.md` (test documentation)
- `MERLINO_OPS_GRAPH_API_DOCUMENTATION.md` (complete API docs)

## Status
✅ **IMPLEMENTED AND TESTED** - Ready for Merlino integration

---

**Implementation Date:** December 26, 2025  
**Implementer:** Morgana Arsenal Team  
**Requested By:** Merlino (Excel Add-in)
