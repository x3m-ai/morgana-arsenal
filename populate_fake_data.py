#!/usr/bin/env python3
"""
Script to populate Morgana Arsenal with fake data for testing APIs.
Creates fake agents, operations, links, and tags.
"""

import requests
import json
import random
import string
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "http://localhost:8888"
API_KEY = "ADMIN123"
HEADERS = {"KEY": API_KEY, "Content-Type": "application/json"}

# Fake data pools
HOSTNAMES = [
    "WIN-SRV-2019-01", "WIN-SRV-2022-02", "WIN-DESKTOP-03",
    "UBUNTU-WEB-01", "UBUNTU-DB-02", "DEBIAN-APP-03",
    "MACOS-DEV-01", "MACOS-DESIGN-02",
    "WIN10-OFFICE-04", "WIN11-FINANCE-05"
]

PLATFORMS = ["windows", "linux", "darwin"]
EXECUTORS_MAP = {
    "windows": ["psh", "cmd", "pwsh"],
    "linux": ["sh", "bash"],
    "darwin": ["sh", "bash"]
}

GROUPS = ["red", "blue", "purple", "white", "black", "orange", "green"]

OPERATION_NAMES = [
    "Recon Mission Alpha", "Data Exfil Beta", "Lateral Movement Gamma",
    "Privilege Escalation Delta", "Persistence Test Epsilon",
    "Discovery Operation Zeta", "Collection Phase Eta",
    "Command Control Test Theta", "Impact Simulation Iota"
]

ADVERSARY_IDS = [
    "de07f52d-9928-4071-9142-cb1d437b4e6c",  # Example adversary
]

TAG_NAMES = ["production", "testing", "staging", "critical", "low-priority", "high-value", "compromised", "clean"]


def generate_paw():
    """Generate random 6-character PAW ID."""
    return ''.join(random.choices(string.ascii_lowercase, k=6))


def create_fake_agent():
    """Create a fake agent via API."""
    platform = random.choice(PLATFORMS)
    hostname = random.choice(HOSTNAMES)
    paw = generate_paw()
    
    agent_data = {
        "paw": paw,
        "host": hostname,
        "username": "fake_user",
        "platform": platform,
        "executors": EXECUTORS_MAP[platform],
        "privilege": random.choice(["User", "Elevated", "Administrator"]),
        "group": random.choice(GROUPS),
        "sleep_min": random.randint(30, 60),
        "sleep_max": random.randint(60, 120),
        "watchdog": 0,
        "contact": "http"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/agents",
            headers=HEADERS,
            json=agent_data
        )
        if response.status_code in [200, 201]:
            print(f"✓ Created agent: {paw} ({hostname} - {platform})")
            return paw
        else:
            print(f"✗ Failed to create agent: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error creating agent: {e}")
        return None


def create_fake_operation(agent_paws):
    """Create a fake operation via API."""
    op_name = random.choice(OPERATION_NAMES) + f"_{random.randint(1000, 9999)}"
    state = random.choice(["running", "running", "running", "paused"])  # More running ops
    group = random.choice(GROUPS)
    
    # Get available adversaries first
    try:
        resp = requests.get(f"{BASE_URL}/api/v2/adversaries", headers=HEADERS)
        adversaries = resp.json() if resp.status_code == 200 else []
        adversary_id = adversaries[0]['adversary_id'] if adversaries else None
    except:
        adversary_id = None
    
    # Get available planners
    try:
        resp = requests.get(f"{BASE_URL}/api/v2/planners", headers=HEADERS)
        planners = resp.json() if resp.status_code == 200 else []
        planner_id = planners[0]['id'] if planners else "atomic"
    except:
        planner_id = "atomic"
    
    operation_data = {
        "name": op_name,
        "group": group,
        "state": state,
        "planner": {"id": planner_id},
        "adversary": {"adversary_id": adversary_id} if adversary_id else None,
        "auto_close": random.choice([True, False]),
        "autonomous": random.randint(0, 1),
        "jitter": f"{random.randint(1, 5)}/{random.randint(5, 10)}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/operations",
            headers=HEADERS,
            json=operation_data
        )
        if response.status_code in [200, 201]:
            op_id = response.json().get('id')
            print(f"✓ Created operation: {op_name} (state: {state})")
            
            # Add some fake links if operation is running or finished
            if state in ["running", "finished"] and agent_paws and op_id:
                add_fake_links(op_id, agent_paws)
            
            return op_id
        else:
            print(f"✗ Failed to create operation: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error creating operation: {e}")
        return None


def add_fake_links(operation_id, agent_paws):
    """Add fake ability execution links to an operation."""
    # Get available abilities
    try:
        resp = requests.get(f"{BASE_URL}/api/v2/abilities", headers=HEADERS)
        abilities = resp.json() if resp.status_code == 200 else []
        if not abilities:
            print("  No abilities found, skipping links")
            return
    except Exception as e:
        print(f"  Failed to get abilities: {e}")
        return
    
    # Create 2-5 fake links
    num_links = random.randint(2, 5)
    for i in range(num_links):
        agent_paw = random.choice(agent_paws)
        ability = random.choice(abilities)
        status = random.choice([0, 0, 0, 1, 124])  # More success than failures
        
        now = datetime.utcnow()
        finish_time = now - timedelta(minutes=random.randint(5, 120))
        
        link_data = {
            "paw": agent_paw,
            "ability": {
                "ability_id": ability.get('ability_id'),
                "name": ability.get('name')
            },
            "command": f"fake command {i+1}",
            "status": status,
            "finish": finish_time.isoformat() + "Z",
            "output": f"Fake output for link {i+1}\nStatus: {'Success' if status == 0 else 'Failed'}\nData: {random.randint(100, 999)}"
        }
        
        try:
            # Use operation patch endpoint to add link
            response = requests.patch(
                f"{BASE_URL}/api/v2/operations/{operation_id}",
                headers=HEADERS,
                json={"add_link": link_data}
            )
            if response.status_code == 200:
                status_str = "success" if status == 0 else "failed"
                print(f"  ✓ Added link: {ability.get('name')} ({status_str})")
            else:
                print(f"  ✗ Failed to add link: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error adding link: {e}")


def add_tags_to_agent(paw):
    """Add random tags to an agent."""
    num_tags = random.randint(1, 3)
    tags = random.sample(TAG_NAMES, num_tags)
    
    for tag in tags:
        try:
            response = requests.patch(
                f"{BASE_URL}/api/v2/agents/{paw}",
                headers=HEADERS,
                json={"tag": tag}
            )
            if response.status_code == 200:
                print(f"  ✓ Added tag '{tag}' to agent {paw}")
        except Exception as e:
            print(f"  ✗ Error adding tag: {e}")


def add_tags_to_operation(op_id):
    """Add random tags to an operation."""
    num_tags = random.randint(1, 2)
    tags = random.sample(TAG_NAMES, num_tags)
    
    for tag in tags:
        try:
            response = requests.patch(
                f"{BASE_URL}/api/v2/operations/{op_id}",
                headers=HEADERS,
                json={"tag": tag}
            )
            if response.status_code == 200:
                print(f"  ✓ Added tag '{tag}' to operation {op_id}")
        except Exception as e:
            print(f"  ✗ Error adding tag: {e}")


def main():
    """Main function to populate fake data."""
    print("=" * 60)
    print("Morgana Arsenal - Fake Data Population Script")
    print("=" * 60)
    
    # Check server availability
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if resp.status_code != 200:
            print("✗ Server not responding properly")
            return
    except:
        print("✗ Cannot connect to server. Is it running?")
        return
    
    print("\n[1/4] Creating fake agents...")
    print("-" * 60)
    agent_paws = []
    for i in range(10):  # Create 10 fake agents
        paw = create_fake_agent()
        if paw:
            agent_paws.append(paw)
    
    print(f"\nCreated {len(agent_paws)} agents")
    
    if agent_paws:
        print("\n[2/4] Adding tags to agents...")
        print("-" * 60)
        for paw in random.sample(agent_paws, min(5, len(agent_paws))):
            add_tags_to_agent(paw)
    
    print("\n[3/4] Creating fake operations...")
    print("-" * 60)
    operation_ids = []
    for i in range(8):  # Create 8 fake operations
        op_id = create_fake_operation(agent_paws)
        if op_id:
            operation_ids.append(op_id)
    
    print(f"\nCreated {len(operation_ids)} operations")
    
    if operation_ids:
        print("\n[4/4] Adding tags to operations...")
        print("-" * 60)
        for op_id in random.sample(operation_ids, min(4, len(operation_ids))):
            add_tags_to_operation(op_id)
    
    print("\n" + "=" * 60)
    print("✓ Fake data population complete!")
    print("=" * 60)
    print(f"Agents created: {len(agent_paws)}")
    print(f"Operations created: {len(operation_ids)}")
    print("\nYou can now test the Merlino APIs with this data.")


if __name__ == "__main__":
    main()
