#!/usr/bin/env python3
"""
Script to add fake links to existing operations in Morgana Arsenal.
Manipulates operations directly via API to add completed ability executions.
"""

import requests
import json
import random
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8888"
API_KEY = "ADMIN123"
HEADERS = {"KEY": API_KEY, "Content-Type": "application/json"}


def get_operations():
    """Get all operations."""
    try:
        resp = requests.get(f"{BASE_URL}/api/v2/operations", headers=HEADERS)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"Error getting operations: {e}")
        return []


def get_agents():
    """Get all agents."""
    try:
        resp = requests.get(f"{BASE_URL}/api/v2/agents", headers=HEADERS)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"Error getting agents: {e}")
        return []


def get_abilities():
    """Get all abilities."""
    try:
        resp = requests.get(f"{BASE_URL}/api/v2/abilities", headers=HEADERS)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"Error getting abilities: {e}")
        return []


def add_fake_link_to_operation(op_id, op_name, agent_paw, ability):
    """Add a fake completed link to an operation."""
    status = random.choice([0, 0, 0, 1, 124, -1])  # 0=success, 1=fail, 124=timeout, -1=running
    
    now = datetime.utcnow()
    start_time = now - timedelta(minutes=random.randint(10, 240))
    
    # Only set finish time if not running
    if status != -1:
        finish_time = start_time + timedelta(seconds=random.randint(5, 120))
        finish_str = finish_time.isoformat() + "Z"
    else:
        finish_str = None
    
    # Generate fake output
    if status == 0:
        outputs = [
            "Command executed successfully\nFiles processed: 42\nData collected: 1.2 MB",
            "Process completed\nItems found: 15\nStatus: OK",
            "Operation successful\nTarget reached\nPayload delivered",
            "Execution completed\nNo errors detected\nResult: SUCCESS"
        ]
        output = random.choice(outputs)
    elif status == 1:
        outputs = [
            "Error: Access denied\nPermission required: Administrator\nFailed to execute command",
            "Command failed\nException: FileNotFoundException\nCould not locate target file",
            "Execution error\nTimeout occurred after 30 seconds\nOperation aborted",
            "Failed: Network unreachable\nCannot connect to target\nRetry recommended"
        ]
        output = random.choice(outputs)
    elif status == 124:
        output = "Command timed out after 60 seconds\nNo response received\nProcess killed"
    else:
        output = "Waiting for command execution...\nStatus: In progress"
    
    # Create link data using the raw link injection approach
    link_data = {
        "operation": op_id,
        "paw": agent_paw,
        "ability": ability['ability_id'],
        "command": f"echo 'Fake command execution for {ability['name']}'",
        "status": status,
        "score": random.randint(0, 100),
        "jitter": random.randint(1, 5),
        "decide": start_time.isoformat() + "Z",
        "collect": finish_str,
        "finish": finish_str,
        "output": output,
        "pid": random.randint(1000, 9999) if status != -1 else None
    }
    
    # Try to inject link via operation update
    try:
        # First, get current operation state
        resp = requests.get(f"{BASE_URL}/api/v2/operations/{op_id}", headers=HEADERS)
        if resp.status_code != 200:
            print(f"  ✗ Cannot get operation {op_id}")
            return False
        
        op_data = resp.json()
        chain = op_data.get('chain', [])
        
        # Add new link to chain
        chain.append(link_data)
        
        # Update operation with new chain
        update_data = {"chain": chain}
        resp = requests.patch(
            f"{BASE_URL}/api/v2/operations/{op_id}",
            headers=HEADERS,
            json=update_data
        )
        
        if resp.status_code == 200:
            status_str = {0: "success", 1: "failed", 124: "timeout", -1: "running"}.get(status, "unknown")
            print(f"  ✓ Added link to '{op_name}': {ability['name']} ({status_str})")
            return True
        else:
            print(f"  ✗ Failed to add link: {resp.status_code} - {resp.text[:100]}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error adding link: {e}")
        return False


def main():
    print("=" * 70)
    print("Morgana Arsenal - Fake Links Population Script")
    print("=" * 70)
    
    # Get data
    print("\n[1/4] Fetching operations...")
    operations = get_operations()
    print(f"Found {len(operations)} operations")
    
    print("\n[2/4] Fetching agents...")
    agents = get_agents()
    print(f"Found {len(agents)} agents")
    
    print("\n[3/4] Fetching abilities...")
    abilities = get_abilities()
    print(f"Found {len(abilities)} abilities")
    
    if not operations or not agents or not abilities:
        print("\n✗ Missing required data. Cannot proceed.")
        return
    
    print("\n[4/4] Adding fake links to operations...")
    print("-" * 70)
    
    total_links = 0
    for op in operations:
        op_id = op.get('id')
        op_name = op.get('name')
        op_state = op.get('state')
        
        # Skip if operation already has many links
        existing_links = len(op.get('chain', []))
        if existing_links > 10:
            print(f"Skipping '{op_name}' (already has {existing_links} links)")
            continue
        
        # Add 3-8 fake links per operation
        num_links = random.randint(3, 8)
        print(f"\nOperation: {op_name} (state: {op_state})")
        
        for i in range(num_links):
            agent = random.choice(agents)
            ability = random.choice(abilities)
            
            if add_fake_link_to_operation(op_id, op_name, agent['paw'], ability):
                total_links += 1
    
    print("\n" + "=" * 70)
    print(f"✓ Added {total_links} fake links to operations!")
    print("=" * 70)


if __name__ == "__main__":
    main()
