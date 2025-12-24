# Merlino Dashboard APIs

Complete API documentation for Merlino Excel Add-in Dashboard integration with Morgana Arsenal.

**Base URL**: `http://192.168.124.133:8888` or `https://192.168.124.133`
**Authentication**: Header `KEY: ADMIN123`

---

## 1. General Metrics API

**Endpoint**: `GET /api/v2/merlino/dashboard/metrics`

**Description**: Returns overall statistics for Operations Intelligence Dashboard.

**Response Example**:
```json
{
  "total_operations": 24,
  "operations_running": 0,
  "operations_done": 7,
  "operations_stopped": 17,
  "total_abilities": null,
  "abilities_success": 0,
  "abilities_errors": 0,
  "success_rate": 0.0,
  "success_rate_status": "Needs Attention",
  "active_agents": 21,
  "agent_platforms": {
    "linux": 14,
    "windows": 6,
    "darwin": 1
  }
}
```

**Fields**:
- `total_operations`: Total number of operations in system
- `operations_running`: Operations currently in "running" state
- `operations_done`: Operations in "finished" state
- `operations_stopped`: Operations in "paused" state
- `total_abilities`: Total links/abilities executed (null if 0)
- `abilities_success`: Number of successful ability executions (status=0)
- `abilities_errors`: Number of failed/timeout executions (status=1 or 124)
- `success_rate`: Percentage of successful executions (0-100)
- `success_rate_status`: "Excellent" (≥80%), "Good" (≥60%), "Needs Attention" (<60%)
- `active_agents`: Total number of agents
- `agent_platforms`: Breakdown by OS platform

**Usage in Merlino**:
- Top dashboard cards
- Total Operations card (with running/done/stopped breakdown)
- Total Abilities card (with success/errors)
- Success Rate gauge
- Active Agents card (with platform breakdown)

---

## 2. Ability Success Rate Analysis API

**Endpoint**: `GET /api/v2/merlino/dashboard/abilities`

**Description**: Returns detailed ability performance statistics with clustering.

**Response Example**:
```json
{
  "top_performers": [
    {
      "ability_id": "abc123",
      "name": "Identify active user",
      "tactic": "discovery",
      "technique_id": "T1033",
      "executions": 10,
      "success_rate": 95.0,
      "avg_time": 2.5,
      "success": 19,
      "failed": 1,
      "timeout": 0,
      "pending": 0,
      "used_in_operations": 3
    }
  ],
  "needs_attention": [
    {
      "ability_id": "def456",
      "name": "LSASS dump",
      "tactic": "credential-access",
      "technique_id": "T1003.001",
      "executions": 8,
      "success_rate": 62.5,
      "avg_time": 5.2,
      "success": 5,
      "failed": 2,
      "timeout": 1,
      "pending": 0,
      "used_in_operations": 2
    }
  ],
  "needs_improvement": [
    {
      "ability_id": "ghi789",
      "name": "Exfiltrate via DNS",
      "tactic": "exfiltration",
      "technique_id": "T1048.003",
      "executions": 5,
      "success_rate": 20.0,
      "avg_time": 10.0,
      "success": 1,
      "failed": 3,
      "timeout": 1,
      "pending": 0,
      "used_in_operations": 1
    }
  ],
  "total_abilities_analyzed": 25
}
```

**Fields**:
- `top_performers`: Abilities with ≥80% success rate
- `needs_attention`: Abilities with 50-79% success rate
- `needs_improvement`: Abilities with <50% success rate
- Per ability:
  - `ability_id`: Unique ability identifier
  - `name`: Human-readable ability name
  - `tactic`: MITRE ATT&CK tactic
  - `technique_id`: MITRE ATT&CK technique ID (e.g., T1003.001)
  - `executions`: Total times executed
  - `success_rate`: Percentage successful (0-100)
  - `avg_time`: Average execution time in seconds
  - `success/failed/timeout/pending`: Count by status
  - `used_in_operations`: Number of operations using this ability

**Usage in Merlino**:
- "Ability Success Rate Analysis" section
- Three clustered lists: Top Performers, Needs Attention, Needs Improvement (<50%)
- Each ability card shows executions, success rate, avg time, status breakdown, operations used

---

## 3. Operations Health Matrix API

**Endpoint**: `GET /api/v2/merlino/dashboard/operations-health`

**Description**: Returns comprehensive health status for all operations.

**Response Example**:
```json
[
  {
    "operation_id": "abc-123-def-456",
    "operation_name": "Test_blue_Discovery_232801_3",
    "status": "STOPPED",
    "abilities": 0,
    "success": 0,
    "errors": 0,
    "success_rate": 0.0,
    "agents": 0,
    "health": "critical",
    "health_score": 0.0,
    "adversary": "Discovery",
    "started": "2025-12-23 14:30:00"
  },
  {
    "operation_id": "xyz-789-uvw-012",
    "operation_name": "Test_red_Super Spy_232801_1",
    "status": "FINISHED",
    "abilities": 15,
    "success": 12,
    "errors": 3,
    "success_rate": 80.0,
    "agents": 3,
    "health": "healthy",
    "health_score": 80.0,
    "adversary": "Super Spy",
    "started": "2025-12-23 12:00:00"
  }
]
```

**Fields** (array sorted by health_score, worst first):
- `operation_id`: Unique operation UUID
- `operation_name`: Operation name
- `status`: "RUNNING", "STOPPED", "FINISHED"
- `abilities`: Total abilities/links in operation
- `success`: Number of successful executions
- `errors`: Number of failed/timeout executions
- `success_rate`: Percentage successful (0-100)
- `agents`: Number of unique agents involved
- `health`: "healthy" (≥80%), "warning" (50-79%), "critical" (<50%)
- `health_score`: Numeric health score (0-100)
- `adversary`: Adversary profile name
- `started`: Start timestamp (ISO 8601)

**Usage in Merlino**:
- "Operations Health Matrix" table
- Columns: Operation Name, Status, Abilities, Success, Errors, Success Rate, Agents, Health
- Health indicator: red circle (critical), yellow (warning), green (healthy)
- Filter by status dropdown: All Status / Running / Stopped / Finished
- Export CSV button

---

## 4. Error Analytics API

**Endpoint**: `GET /api/v2/merlino/dashboard/errors`

**Description**: Returns error analysis and troubleshooting data.

**Response Example**:
```json
{
  "total_errors": 0,
  "operations_with_errors": 0,
  "critical_operations": 0,
  "unique_error_types": 0,
  "failure_rate": 0.0,
  "most_common_errors": [
    {
      "message": "Access denied",
      "count": 5
    },
    {
      "message": "Command timeout",
      "count": 3
    }
  ],
  "operations_ranked": [
    {
      "operation_id": "abc-123",
      "operation_name": "Test_red_Super Spy",
      "error_count": 5,
      "error_types": 2,
      "criticality": "high"
    }
  ]
}
```

**Fields**:
- `total_errors`: Total error count across all operations
- `operations_with_errors`: Number of operations with at least 1 error
- `critical_operations`: Operations with ≥50% error rate
- `unique_error_types`: Number of distinct error messages
- `failure_rate`: Overall failure percentage (0-100)
- `most_common_errors`: Top 5 error messages with counts
- `operations_ranked`: Operations sorted by error count (top 20)
  - `criticality`: "critical" (≥50% errors), "high" (≥25%), "medium" (<25%), "low"

**Usage in Merlino**:
- "Error Analytics & Troubleshooting" section
- Top cards: Total Errors, Operations with Errors, Unique Error Types
- "Most Common Error Messages" list
- "Operations Ranked by Error Count" table
- Empty state: "No Errors Detected - All operations are running smoothly!"

---

## 5. Real-Time Metrics API

**Endpoint**: `GET /api/v2/merlino/dashboard/realtime`

**Description**: Returns live operational metrics and recent activity.

**Response Example**:
```json
{
  "execution_velocity": 0.0,
  "success_rate": 0.0,
  "success_rate_trend": "STABLE",
  "active_operations": {
    "running": 0,
    "stopped": 24
  },
  "total_abilities": null,
  "abilities_ok": 0,
  "abilities_error": 0,
  "health_percentage": 0.0,
  "recent_activity": [
    {
      "operation_name": "ops1",
      "message": "Operation started with undefined abilities",
      "timestamp": "23:50:38"
    },
    {
      "operation_name": "Test_red_Super Spy_232801_1",
      "message": "Operation has 5 abilities",
      "timestamp": "23:50:01"
    }
  ]
}
```

**Fields**:
- `execution_velocity`: Abilities executed per minute (last 10 minutes)
- `success_rate`: Overall success percentage (0-100)
- `success_rate_trend`: "STABLE", "IMPROVING", "DECLINING"
- `active_operations`: Breakdown of running/stopped operations
- `total_abilities`: Total abilities executed (null if 0)
- `abilities_ok`: Successful executions count
- `abilities_error`: Failed/timeout count
- `health_percentage`: Overall system health (0-100)
- `recent_activity`: Last 10 operations with activity (array)
  - `operation_name`: Operation name
  - `message`: Activity description
  - `timestamp`: Time (HH:MM:SS)

**Usage in Merlino**:
- "Real-Time Operations Metrics" section (with 🔴 LIVE indicator)
- Cards: Execution Velocity, Success Rate, Active Operations, Total Abilities
- "Overall Health Gauge" circular gauge (0-100%)
- "Recent Activity" scrollable list
- Auto-refresh indicator: "Auto-refreshing every X seconds"

---

## 6. Force Graph Data API

**Endpoint**: `GET /api/v2/merlino/dashboard/force-graph`

**Description**: Returns nodes and links for force-directed graph visualization of operations, agents, and TTPs relationships.

**Response Example**:
```json
{
  "nodes": [
    {
      "id": "op_abc-123-def-456",
      "label": "Test_blue_Discovery_232801_3",
      "type": "operation",
      "size": 5,
      "color": "#ffdd57",
      "state": "paused",
      "ttps": ["T1033", "T1087", "T1082"],
      "metadata": {
        "full_name": "Test_blue_Discovery_232801_3",
        "adversary": "Discovery",
        "abilities": 0
      }
    },
    {
      "id": "agent_kali-625",
      "label": "kali-625",
      "type": "agent",
      "size": 8,
      "color": "#48c774",
      "platform": "linux",
      "metadata": {
        "paw": "kali-625",
        "host": "kali-625",
        "group": "blue",
        "operations": 2
      }
    }
  ],
  "links": [
    {
      "source": "op_abc-123",
      "target": "op_def-456",
      "value": 3,
      "type": "shared_ttp",
      "label": "3 TTPs",
      "metadata": {
        "shared_ttps": ["T1033", "T1087", "T1082"]
      }
    },
    {
      "source": "agent_kali-625",
      "target": "op_abc-123",
      "value": 1,
      "type": "agent_operation",
      "label": "executes"
    }
  ],
  "stats": {
    "total_nodes": 45,
    "total_links": 67,
    "operations": 24,
    "agents": 21
  }
}
```

**Node Types**:

1. **Operation Nodes**:
   - `id`: "op_{operation_id}"
   - `type`: "operation"
   - `color`: Blue (#3273dc) = running, Yellow (#ffdd57) = paused, Green (#48c774) = finished
   - `size`: Based on number of abilities (minimum 5)
   - `ttps`: Array of MITRE ATT&CK technique IDs
   - `metadata`: Full name, adversary, abilities count

2. **Agent Nodes**:
   - `id`: "agent_{paw}"
   - `type`: "agent"
   - `color`: Red (#f14668) = Windows, Green (#48c774) = Linux, Blue (#3273dc) = Darwin
   - `size`: Fixed at 8
   - `platform`: "windows", "linux", "darwin"
   - `metadata`: PAW, host, group, operations count

**Link Types**:

1. **Shared TTP Links** (operation ↔ operation):
   - `type`: "shared_ttp"
   - `value`: Number of shared TTPs (strength of connection)
   - `label`: "{count} TTPs"
   - `metadata.shared_ttps`: Array of shared technique IDs

2. **Agent-Operation Links** (agent → operation):
   - `type`: "agent_operation"
   - `value`: 1
   - `label`: "executes"

**Graph Properties**:
- **Force Strength**: Based on `value` field (more shared TTPs = stronger attraction)
- **Node Size**: Reflects importance (operations with more abilities are larger)
- **Color Coding**: 
  - Operations by state (running/paused/finished)
  - Agents by platform (Windows/Linux/macOS)
- **Clustering**: Operations with shared TTPs cluster together
- **Agent Proximity**: Agents near operations they executed on

**Usage in Merlino**:
- Interactive force-directed graph visualization
- Legend showing node types and colors
- Hover tooltips with metadata
- Click to highlight connections
- Zoom and pan controls
- Filter by operation state, agent platform, or TTP
- Export as image/SVG

---

## API Usage Examples

### JavaScript (Excel Add-in)

```javascript
// General Metrics
async function loadDashboardMetrics() {
  const response = await fetch('http://192.168.124.133:8888/api/v2/merlino/dashboard/metrics', {
    headers: { 'KEY': 'ADMIN123' }
  });
  const data = await response.json();
  
  // Update dashboard cards
  document.getElementById('total-ops').textContent = data.total_operations;
  document.getElementById('success-rate').textContent = data.success_rate + '%';
  document.getElementById('active-agents').textContent = data.active_agents;
}

// Force Graph
async function loadForceGraph() {
  const response = await fetch('http://192.168.124.133:8888/api/v2/merlino/dashboard/force-graph', {
    headers: { 'KEY': 'ADMIN123' }
  });
  const graphData = await response.json();
  
  // Use D3.js or similar library
  const svg = d3.select('#force-graph');
  const simulation = d3.forceSimulation(graphData.nodes)
    .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(d => 100 / d.value))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2));
  
  // Render nodes and links...
}
```

### Python

```python
import requests

BASE_URL = "http://192.168.124.133:8888"
HEADERS = {"KEY": "ADMIN123"}

# Get all dashboard data
metrics = requests.get(f"{BASE_URL}/api/v2/merlino/dashboard/metrics", headers=HEADERS).json()
abilities = requests.get(f"{BASE_URL}/api/v2/merlino/dashboard/abilities", headers=HEADERS).json()
health = requests.get(f"{BASE_URL}/api/v2/merlino/dashboard/operations-health", headers=HEADERS).json()
errors = requests.get(f"{BASE_URL}/api/v2/merlino/dashboard/errors", headers=HEADERS).json()
realtime = requests.get(f"{BASE_URL}/api/v2/merlino/dashboard/realtime", headers=HEADERS).json()
force_graph = requests.get(f"{BASE_URL}/api/v2/merlino/dashboard/force-graph", headers=HEADERS).json()

print(f"Total Operations: {metrics['total_operations']}")
print(f"Success Rate: {metrics['success_rate']}%")
print(f"Active Agents: {metrics['active_agents']}")
```

### cURL

```bash
# Test all APIs
curl -H "KEY: ADMIN123" "http://192.168.124.133:8888/api/v2/merlino/dashboard/metrics"
curl -H "KEY: ADMIN123" "http://192.168.124.133:8888/api/v2/merlino/dashboard/abilities"
curl -H "KEY: ADMIN123" "http://192.168.124.133:8888/api/v2/merlino/dashboard/operations-health"
curl -H "KEY: ADMIN123" "http://192.168.124.133:8888/api/v2/merlino/dashboard/errors"
curl -H "KEY: ADMIN123" "http://192.168.124.133:8888/api/v2/merlino/dashboard/realtime"
curl -H "KEY: ADMIN123" "http://192.168.124.133:8888/api/v2/merlino/dashboard/force-graph"
```

---

## Integration Notes

### Auto-Refresh Strategy
- **Metrics/Realtime**: Refresh every 3-5 seconds
- **Abilities/Health**: Refresh every 10-15 seconds
- **Errors**: Refresh every 30 seconds
- **Force Graph**: Refresh every 60 seconds or on-demand

### Error Handling
All APIs return HTTP 500 with error details if something fails:
```json
{
  "error": "Error message",
  "traceback": "Full Python traceback"
}
```

### Performance
- All APIs respond in <100ms for typical dataset (20-50 operations)
- Force graph may take longer (200-500ms) with 100+ nodes
- Consider caching and debouncing for rapid refresh intervals

### CORS
If accessing from browser, ensure Caldera allows CORS:
```python
# In conf/default.yml
app:
  cors: true
```

---

## Testing the APIs

Restart Morgana Arsenal server to load new endpoints:

```bash
cd /home/morgana/morgana-arsenal
pkill -f server.py
python3 server.py --insecure --log DEBUG
```

Then test all endpoints:

```bash
# Quick test script
for endpoint in metrics abilities operations-health errors realtime force-graph; do
  echo "Testing /api/v2/merlino/dashboard/$endpoint"
  curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/merlino/dashboard/$endpoint" | jq -r 'if type == "object" then "✅ OK" else "❌ ERROR" end'
  echo ""
done
```

---

## Dashboard Design Recommendations

### Layout Structure
1. **Top Row**: 4 metric cards (operations, abilities, success rate, agents)
2. **Second Row**: Ability success rate analysis (3 columns: top/attention/improvement)
3. **Third Row**: Operations health matrix table (sortable, filterable)
4. **Fourth Row**: Error analytics (cards + lists)
5. **Fifth Row**: Real-time metrics + recent activity
6. **Sixth Row (Full Width)**: Force graph visualization

### Color Scheme
- **Success**: Green (#48c774)
- **Warning**: Yellow (#ffdd57)
- **Error/Critical**: Red (#f14668)
- **Running**: Blue (#3273dc)
- **Neutral**: Purple (#7957d5)

### Interactive Elements
- Click operation in health matrix → show detailed view
- Click ability in success analysis → show all executions
- Click error message → show affected operations
- Hover force graph node → highlight connections
- Click force graph node → filter related data

---

## Future Enhancements

1. **Historical Trends**: Add time-series data for success rate trends
2. **Agent Performance**: Individual agent success rates and statistics
3. **TTP Coverage**: MITRE ATT&CK matrix coverage visualization
4. **Recommendations**: AI-powered suggestions for improving operation success
5. **Alerts**: Configurable thresholds for notifications
6. **Export**: CSV/JSON export for all API endpoints

---

**Version**: 1.0  
**Date**: December 23, 2025  
**Author**: Morgana Arsenal Team
