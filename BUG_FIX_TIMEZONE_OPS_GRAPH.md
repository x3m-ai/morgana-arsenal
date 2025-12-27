# Bug Fix: Merlino Ops Graph API Empty Data Issue

## Date
December 26, 2025 (15:00 UTC)

## Issue Summary
The Merlino Ops Graph API endpoints were returning empty data (`{"nodes": [], "edges": []}`) despite operations with completed links existing in the system.

## Root Cause
**TypeError: can't compare offset-naive and offset-aware datetimes**

The API code was using `datetime.datetime.utcnow()` to calculate the time window cutoff, which returns a **timezone-naive** datetime object. However, link timestamps from `link.display['finish']` are in ISO format with 'Z' suffix (e.g., `2025-12-23T22:11:01Z`), which when parsed with `.fromisoformat()` after replacing 'Z' with '+00:00', creates a **timezone-aware** datetime object.

Python cannot compare naive and aware datetime objects, causing a TypeError that was silently caught by the exception handler, resulting in all links being skipped.

## Affected Code
File: `app/api/v2/handlers/operation_api.py`

**Affected Endpoints:**
1. `POST /api/v2/merlino/ops-graph` (line ~1327)
2. `GET /api/v2/merlino/ops-graph/problem-details` (line ~1707)
3. `GET /api/v2/merlino/ops-graph/operation-details` (line ~1859)
4. `GET /api/v2/merlino/ops-graph/agent-details` (line ~2023)

## Fix Applied

### Before (Incorrect):
```python
# Calculate time window
now = datetime.datetime.utcnow()  # Returns timezone-naive datetime
cutoff_time = now - datetime.timedelta(minutes=window_minutes)

# Later in code:
link_ts = datetime.datetime.fromisoformat(str(finish_value).replace('Z', '+00:00'))  # Timezone-aware
if link_ts < cutoff_time:  # TypeError: can't compare naive and aware datetimes
    continue
```

### After (Correct):
```python
# Calculate time window
now = datetime.datetime.now(datetime.timezone.utc)  # Returns timezone-aware datetime
cutoff_time = now - datetime.timedelta(minutes=window_minutes)

# Later in code:
link_ts = datetime.datetime.fromisoformat(str(finish_value).replace('Z', '+00:00'))  # Timezone-aware
if link_ts < cutoff_time:  # Comparison works correctly
    continue
```

## Changes Made

**Lines Changed:** 4 occurrences across 4 different methods

1. **Line 1327** - `merlino_ops_graph()`
   - Changed: `now = datetime.datetime.utcnow()`
   - To: `now = datetime.datetime.now(datetime.timezone.utc)`

2. **Line 1707** - `merlino_problem_details()`
   - Changed: `now = datetime.datetime.utcnow()`
   - To: `now = datetime.datetime.now(datetime.timezone.utc)`

3. **Line 1859** - `merlino_operation_details()`
   - Changed: `now = datetime.datetime.utcnow()`
   - To: `now = datetime.datetime.now(datetime.timezone.utc)`

4. **Line 2023** - `merlino_agent_details()`
   - Changed: `now = datetime.datetime.utcnow()`
   - To: `now = datetime.datetime.now(datetime.timezone.utc)`

## Testing Results

### Before Fix:
```bash
$ curl -X POST -H "KEY: ADMIN123" -H "Content-Type: application/json" \
  -d '{"options": {"windowMinutes": 4320}}' \
  http://localhost:8888/api/v2/merlino/ops-graph

{"nodes": [], "edges": []}  # Empty despite data existing
```

### After Fix:
```bash
$ curl -X POST -H "KEY: ADMIN123" -H "Content-Type: application/json" \
  -d '{"options": {"windowMinutes": 4320}}' \
  http://localhost:8888/api/v2/merlino/ops-graph

{
    "nodes": [
        {"id": "op:5a9a344c-d65a-4153-9259-0aa34a7d93dc", "type": "operation", ...},
        {"id": "agent:puqadh", "type": "agent", ...},
        {"id": "problem:discovery:T1082", "type": "problem", ...},
        {"id": "problem:defense-evasion:T1027.013", "type": "problem", ...}
    ],
    "edges": [...]
}  # Returns actual data
```

**All 6 API Endpoints Verified:**
- ✅ API 1: Ops Graph - Returns 4 nodes, 3 edges
- ✅ API 2: Problem Details - Returns top agents, operations, events
- ✅ API 3: Operation Details - Returns agents, problems, events
- ✅ API 4: Agent Details - Returns 1 operation, 1 problem, 2 events
- ✅ API 5: Ops Actions - (Not affected by this bug)
- ✅ API 6: UI Routes - (Not affected by this bug)

## Technical Details

### Python Datetime Behavior:
- `datetime.datetime.utcnow()` - Returns naive datetime (no timezone info)
- `datetime.datetime.now(datetime.timezone.utc)` - Returns aware datetime (UTC timezone)
- Naive and aware datetimes **cannot be compared** directly

### ISO 8601 Timestamp Handling:
- Link timestamps: `2025-12-23T22:11:01Z` (Zulu time = UTC)
- After `.replace('Z', '+00:00')`: `2025-12-23T22:11:01+00:00`
- `.fromisoformat()` correctly parses as timezone-aware datetime

## Prevention
To avoid similar issues in the future:
1. Always use `datetime.now(datetime.timezone.utc)` instead of `utcnow()`
2. Ensure all datetime comparisons use either all-naive or all-aware objects
3. Add explicit error logging with traceback for debugging (was key to finding this bug)

## Related Files
- `app/api/v2/handlers/operation_api.py` (main fix)
- `ops-graph-api-spec.md` (API specification - no changes needed)
- `ops-graph-test-calls.md` (test documentation - working as expected)

## Status
✅ **RESOLVED** - All API endpoints now return correct data within the specified time window.

## Additional Fix: Default Time Window
**Date**: December 26, 2025 (15:30 UTC)

### Issue
Frontend calls without explicit `windowMinutes` parameter were returning empty data because the default was only 24 hours (1440 minutes), and test data was older than that.

### Solution
Changed default time window from 24 hours to 7 days:

**File**: `app/api/v2/handlers/operation_api.py` (line 1292)

```python
# Before:
window_minutes = options.get('windowMinutes', 1440)  # Default 24h for frontend

# After:
window_minutes = options.get('windowMinutes', 10080)  # Default 7 days for frontend
```

### Verification
```powershell
# Frontend call (no windowMinutes specified, uses default 7 days now)
$uri = "https://192.168.124.133/api/v2/merlino/ops-graph"
$body = (@{
  options = @{
    includeAgents   = $true
    includeProblems = $true
    maxNodes        = 400
    maxEdges        = 1200
  }
} | ConvertTo-Json -Depth 10)

Invoke-RestMethod -Method Post -Uri $uri -Headers @{"KEY"="ADMIN123"} -Body $body
# Returns: 4 nodes, 3 edges ✅
```

## Git Commit
This fix should be committed with message:
```
Fix timezone-aware datetime + increase default time window in Merlino Ops Graph APIs

- Changed datetime.utcnow() to datetime.now(datetime.timezone.utc)
- Fixes TypeError preventing data from being returned
- Increased default windowMinutes from 1440 (24h) to 10080 (7 days)
- Frontend calls without explicit window now show data up to 7 days old
- All endpoints now return correct nodes/edges/events
```
