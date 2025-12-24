# Merlino API Documentation

## Endpoint: Merlino Synchronize

### Base Information
- **URL**: `https://192.168.124.133/api/v2/merlino/synchronize`
- **Method**: `POST`
- **Authentication**: Header-based
- **Content-Type**: `application/json`

---

## Request Headers

```
KEY: ADMIN123
Content-Type: application/json
```

---

## Request Body (Payload)

### Format
JSON array of operation objects. Each operation object can have the following fields:

```json
[
  {
    "operation_id": "",           // String (UUID) - Leave empty to create new
    "adversary_id": "",           // String (UUID) - Leave empty to create new
    "operation": "Operation Name", // String (required for new operations)
    "adversary": "Adversary Name", // String (required for new adversaries)
    "description": "Description",  // String (optional)
    "comments": "User comments",   // String (optional)
    "tcodes": "T1082, T1027.013", // String (comma-separated MITRE technique IDs)
    "assigned": "",               // String (team assignment - not used in creation)
    "state": "",                  // String (not used - server sets to 'running')
    "agents": 0                   // Number (not used - calculated by server)
  }
]
```

### Field Details

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation_id` | String | No | UUID of existing operation. Leave empty to create new |
| `adversary_id` | String | No | UUID of existing adversary. Leave empty to create new |
| `operation` | String | Yes* | Operation name (*required if creating new) |
| `adversary` | String | Yes* | Adversary name (*required if creating new) |
| `description` | String | No | Operation/Adversary description |
| `comments` | String | No | User comments for the operation |
| `tcodes` | String | Yes* | Comma-separated MITRE ATT&CK technique IDs (*required for new adversary) |
| `assigned` | String | No | Team assignment (stored in client, not server) |
| `state` | String | No | Ignored - server always sets to 'running' |
| `agents` | Number | No | Ignored - calculated by server |

---

## Use Cases

### 1. Get All Operations (Initial Sync)
**Payload**: Empty array

```json
[]
```

**Behavior**: 
- Does not create any operations
- Returns all existing operations in flat format

---

### 2. Create New Operation with New Adversary
**Payload**: Operation with empty IDs

```json
[
  {
    "operation_id": "",
    "adversary_id": "",
    "operation": "Recon Mission Alpha",
    "adversary": "APT-DEMO-01",
    "description": "Reconnaissance and discovery phase",
    "tcodes": "T1082, T1087.001, T1033"
  }
]
```

**Behavior**:
1. Searches for abilities matching technique IDs (T1082, T1087.001, T1033)
2. Creates new Adversary with found abilities
3. Creates new Operation linked to adversary
4. Sets operation state to 'running' and autonomous to 1 (auto-execute)
5. Returns all operations including the newly created one

---

### 3. Create Multiple Operations at Once
**Payload**: Multiple operations

```json
[
  {
    "operation_id": "",
    "adversary_id": "",
    "operation": "Op Alpha",
    "adversary": "Red Team A",
    "tcodes": "T1082, T1059.001"
  },
  {
    "operation_id": "",
    "adversary_id": "",
    "operation": "Op Beta",
    "adversary": "Red Team B",
    "tcodes": "T1027.013, T1218.011"
  }
]
```

**Behavior**: Creates all operations sequentially, then returns all operations

---

## Response Format

### Success Response (200 OK)

Returns flat JSON array where **each row represents one link/ability execution** within an operation.

**Structure**: Operations with multiple abilities will have multiple rows (one per link).

```json
[
  {
    "operation": "ops1",                                // Operation name
    "state": "running",                                  // Operation state
    "adversary": "0 - Merlino - Test",                  // Adversary name
    "agents": 1,                                        // Number of agents connected
    "tcodes": "T1082, T1027.013",                      // All technique IDs in adversary
    "description": "",                                   // Operation description
    "comments": "",                                      // User comments
    "assigned": "",                                      // Team assignment (from localStorage)
    "started": "2025-12-22 14:50:46",                   // Operation start time
    "status": "0",                                      // Link status (0=success, 1=running, -1=failed)
    "ability": "Merlino - Test Agent",                  // Ability name
    "tactic": "discovery",                              // MITRE ATT&CK tactic
    "technique": "T1082",                               // MITRE ATT&CK technique ID
    "agent": "puqadh",                                  // Agent PAW (unique identifier)
    "host": "WINDOWSPC01",                              // Target host
    "pid": "0",                                         // Process ID
    "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",   // Operation UUID
    "adversary_id": "d39c9b2e-44c3-4d4c-a9a4-33e6b9802499"    // Adversary UUID
  },
  {
    "operation": "ops1",
    "state": "running",
    "adversary": "0 - Merlino - Test",
    "agents": 1,
    "tcodes": "T1082, T1027.013",
    "description": "",
    "assigned": "",
    "started": "2025-12-22 14:50:46",
    "status": "1",                                      // Different status
    "ability": "Decode Eicar File and Write to File",   // Different ability
    "tactic": "defense-evasion",                        // Different tactic
    "technique": "T1027.013",                           // Different technique
    "agent": "puqadh",
    "host": "WINDOWSPC01",
    "pid": "0",
    "operation_id": "5a9a344c-d65a-4153-9259-0aa34a7d93dc",
    "adversary_id": "d39c9b2e-44c3-4d4c-a9a4-33e6b9802499"
  }
]
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `operation` | String | Operation name |
| `state` | String | Operation state: 'running', 'paused', 'finished' |
| `adversary` | String | Adversary name |
| `agents` | Number | Count of connected agents |
| `tcodes` | String | Comma-separated list of all technique IDs in adversary |
| `description` | String | Operation description |
| `comments` | String | User comments for the operation |
| `assigned` | String | Team assignment (client-side only) |
| `started` | String | ISO timestamp of operation start |
| `status` | String | Link execution status: '0' (success), '1' (running), '-1' (failed) |
| `ability` | String | Ability name executed in this link |
| `tactic` | String | MITRE ATT&CK tactic (e.g., 'discovery', 'execution') |
| `technique` | String | MITRE ATT&CK technique ID (e.g., 'T1082') |
| `agent` | String | Agent PAW identifier |
| `host` | String | Target hostname |
| `pid` | String | Process ID used for execution |
| `operation_id` | String | Operation UUID (use for future updates) |
| `adversary_id` | String | Adversary UUID (use for future updates) |

---

### Error Responses

#### 400 Bad Request
```json
{
  "error": "Expected list of operations"
}
```
**Cause**: Payload is not a JSON array

---

#### 500 Internal Server Error
```json
{
  "error": "Error message here",
  "traceback": "Full Python stack trace"
}
```
**Cause**: Server-side error (missing abilities, database issues, etc.)

---

## Important Notes

### 1. Flat Response Format
- **One row per link/ability execution**
- If an operation has 5 abilities and 3 links executed, you'll get 3 rows with the same operation_id
- Operations with no links yet will still have 1 row with status='N/A'

### 2. Technique ID Matching
- The `tcodes` field is parsed and split by comma
- Each technique ID (e.g., "T1082") is used to search the abilities database
- If no abilities are found for a technique, it will be skipped (no error)
- Example: "T1082, T1027.013, T9999" → finds abilities for T1082 and T1027.013, ignores T9999

### 3. Operation Creation Defaults
When creating new operations:
- **state**: Always set to 'running'
- **autonomous**: Set to 1 (abilities execute automatically)
- **group**: Empty string '' (means "All groups")
- **planner**: Uses first available planner in database
- **source**: Uses first available source in database
- **jitter**: '2/8' (2-8 seconds random delay)
- **visibility**: 50
- **obfuscator**: 'plain-text'

### 4. ID Behavior
- Both `operation_id` and `adversary_id` must be empty strings to create new
- If one ID is populated and the other is empty, creation will fail
- UUIDs are generated by the server, not the client

---

## Example cURL Commands

### Get All Operations
```bash
curl -k -X POST "https://192.168.124.133/api/v2/merlino/synchronize" \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '[]'
```

### Create New Operation
```bash
curl -k -X POST "https://192.168.124.133/api/v2/merlino/synchronize" \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '[{
    "operation_id": "",
    "adversary_id": "",
    "operation": "Test Operation",
    "adversary": "Test Adversary",
    "description": "Testing from Merlino",
    "comments": "This is a test operation",
    "tcodes": "T1082, T1059.001"
  }]'
```

---

## Excel Add-in Implementation Guidance

### Recommended Flow

1. **Initial Sync**: 
   - POST empty array `[]`
   - Store all returned operations in Excel table
   - Parse and display tcodes, agents, status per operation

2. **Create New Operation**:
   - User fills Excel rows with name, adversary, tcodes
   - Leave operation_id and adversary_id empty
   - POST array with new operations
   - Update Excel table with returned UUIDs

3. **Refresh Data**:
   - POST empty array `[]` periodically
   - Update Excel table with latest status, agents, links

4. **Data Parsing**:
   - Group rows by `operation_id` to show one operation with multiple links
   - Use `status` field to show execution progress (0=success, 1=running, -1=fail)
   - Parse `tcodes` field by splitting on comma+space

### Excel Table Structure Suggestion

| Operation Name | Adversary | Tcodes | State | Agents | Links | Status | Started | Operation ID | Adversary ID |
|----------------|-----------|--------|-------|--------|-------|--------|---------|--------------|--------------|
| ops1 | 0 - Merlino - Test | T1082, T1027.013 | running | 1 | 2 | 2/2 success | 2025-12-22 14:50:46 | 5a9a344c... | d39c9b2e... |

---

## Testing & Debugging

The server logs all incoming payloads:
```
[MERLINO SYNC] Received payload with X items
[MERLINO SYNC] Payload content: { ... }
[SYNC DEBUG] Searching for technique_id=T1082, found N abilities
[SYNC DEBUG] Added ability: Ability Name (ability-id-here)
```

Monitor logs:
```bash
tail -f /home/morgana/morgana-arsenal/caldera.log | grep -E "MERLINO|SYNC"
```

---

## Security Notes

- **SSL Certificate**: Server uses self-signed certificate, use `-k` flag in cURL or ignore SSL warnings
- **Authentication**: Header-based with `KEY: ADMIN123` - change in production!
- **Rate Limiting**: None currently implemented
- **CORS**: Not configured - same-origin or CORS headers needed for browser-based clients

---

## Version Information
- **Morgana Arsenal**: v5.3.0 (Caldera fork)
- **API Version**: v2
- **Last Updated**: December 22, 2025
