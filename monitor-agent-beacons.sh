#!/bin/bash
# Monitor Agent Beacons and Instructions in Real-Time
# Shows detailed interaction between agents and server

echo "=========================================="
echo "Morgana Arsenal - Agent Beacon Monitor"
echo "=========================================="
echo ""
echo "Monitoring files:"
echo "  - caldera.log (detailed beacon info)"
echo "  - caldera-output.log (server startup/errors)"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Use tail -f on both log files with color highlighting
tail -f caldera.log 2>/dev/null | grep --line-buffered -E '\[BEACON\]|\[GET_INSTRUCTIONS\]|\[ADD_AGENT\]|\[HEARTBEAT\]' | \
    sed 's/\[BEACON\]/\x1b[32m[BEACON]\x1b[0m/g' | \
    sed 's/\[GET_INSTRUCTIONS\]/\x1b[34m[GET_INSTRUCTIONS]\x1b[0m/g' | \
    sed 's/\[ADD_AGENT\]/\x1b[35m[ADD_AGENT]\x1b[0m/g' | \
    sed 's/\[HEARTBEAT\]/\x1b[36m[HEARTBEAT]\x1b[0m/g' | \
    sed 's/✓/\x1b[32m✓\x1b[0m/g' | \
    sed 's/✗/\x1b[31m✗\x1b[0m/g' | \
    sed 's/⚠/\x1b[33m⚠\x1b[0m/g'
