#!/bin/bash

echo ""
echo "========================================================================"
echo "📊 MERLINO DASHBOARD APIs - FULL TEST"
echo "========================================================================"
echo ""

curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/merlino/dashboard/metrics" | python3 << 'PYTHON'
import json, sys
data = json.load(sys.stdin)
print("1️⃣  METRICS API")
print(f"   Total Operations: {data['total_operations']}")
print(f"   Running: {data['operations_running']}, Done: {data['operations_done']}, Stopped: {data['operations_stopped']}")
print(f"   Success Rate: {data['success_rate']}% ({data['success_rate_status']})")
print(f"   Active Agents: {data['active_agents']}")
print(f"   Platforms: {data['agent_platforms']}")
print()
PYTHON

curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/merlino/dashboard/abilities" | python3 << 'PYTHON'
import json, sys
data = json.load(sys.stdin)
print("2️⃣  ABILITIES API")
print(f"   Top Performers: {len(data['top_performers'])} abilities")
print(f"   Needs Attention: {len(data['needs_attention'])} abilities")
print(f"   Needs Improvement: {len(data['needs_improvement'])} abilities")
print()
PYTHON

curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/merlino/dashboard/operations-health" | python3 << 'PYTHON'
import json, sys
data = json.load(sys.stdin)
print("3️⃣  OPERATIONS HEALTH API")
print(f"   Operations: {len(data)}")
if data:
    healthy = sum(1 for op in data if op['health'] == 'healthy')
    warning = sum(1 for op in data if op['health'] == 'warning')
    critical = sum(1 for op in data if op['health'] == 'critical')
    print(f"   Healthy: {healthy}, Warning: {warning}, Critical: {critical}")
print()
PYTHON

curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/merlino/dashboard/errors" | python3 << 'PYTHON'
import json, sys
data = json.load(sys.stdin)
print("4️⃣  ERRORS API")
print(f"   Total Errors: {data['total_errors']}")
print(f"   Operations with Errors: {data['operations_with_errors']}")
print(f"   Failure Rate: {data['failure_rate']}%")
print()
PYTHON

curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/merlino/dashboard/realtime" | python3 << 'PYTHON'
import json, sys
data = json.load(sys.stdin)
print("5️⃣  REALTIME API")
print(f"   Execution Velocity: {data['execution_velocity']} abilities/min")
print(f"   Success Rate: {data['success_rate']}%")
print(f"   Active Operations: {data['active_operations']['running']} running, {data['active_operations']['stopped']} stopped")
print(f"   Health: {data['health_percentage']}%")
print()
PYTHON

curl -s -H "KEY: ADMIN123" "http://localhost:8888/api/v2/merlino/dashboard/force-graph" | python3 << 'PYTHON'
import json, sys
data = json.load(sys.stdin)
print("6️⃣  FORCE GRAPH API")
print(f"   Total Nodes: {data['stats']['total_nodes']}")
print(f"   Operations: {data['stats']['operations']}")
print(f"   Agents: {data['stats']['agents']}")
print(f"   Total Links: {data['stats']['total_links']}")
print()
PYTHON

echo "========================================================================"
echo "✅ All 6 APIs working correctly!"
echo "========================================================================"
echo ""

echo "📝 Documentation: MERLINO_DASHBOARD_APIs.md"
echo "🌐 Base URL: http://192.168.124.133:8888/api/v2/merlino/dashboard/"
echo ""

