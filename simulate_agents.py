#!/usr/bin/env python3
"""
Morgana Arsenal - Fake Agents Simulator

Creates and maintains fake agents for testing multi-agent scenarios
without needing to install real agents on target machines.

Usage:
    python3 simulate_agents.py --count 5 --groups "red,blue,production"
    python3 simulate_agents.py --create-only  # Create agents once without beaconing
    python3 simulate_agents.py --beacon-interval 30  # Beacon every 30 seconds
"""

import argparse
import asyncio
import aiohttp
import json
import random
import string
import sys
import base64
from datetime import datetime

# Server configuration
CALDERA_URL = "http://localhost:8888"
API_KEY = "ADMIN123"

# Agent templates
PLATFORMS = ["windows", "linux", "darwin"]
EXECUTORS = {
    "windows": ["cmd", "psh", "pwsh"],
    "linux": ["sh", "bash"],
    "darwin": ["sh", "bash", "zsh"]
}
PRIVILEGES = ["User", "Elevated", "SYSTEM"]

# Fake hostnames
HOSTNAMES = {
    "windows": ["WIN-DESKTOP-{}", "WIN-SRV-{}", "WORKSTATION-{}", "DC-{}"],
    "linux": ["ubuntu-{}", "centos-{}", "debian-{}", "kali-{}"],
    "darwin": ["macbook-{}", "imac-{}", "mac-mini-{}"]
}

def generate_paw():
    """Generate a random PAW (agent identifier)"""
    return ''.join(random.choices(string.ascii_lowercase, k=6))

def generate_hostname(platform):
    """Generate a realistic hostname for the platform"""
    template = random.choice(HOSTNAMES[platform])
    number = random.randint(100, 999)
    return template.format(number)

def generate_agent(platform=None, group=None):
    """Generate a fake agent profile"""
    if not platform:
        platform = random.choice(PLATFORMS)
    
    if not group:
        group = random.choice(["red", "blue", "production", "dev", "test"])
    
    hostname = generate_hostname(platform)
    privilege = random.choice(PRIVILEGES) if platform == "windows" else random.choice(["User", "root"])
    
    # Build agent profile for beacon
    # NOTE: Don't include 'paw' - API will assign it
    agent_profile = {
        "server": CALDERA_URL,
        "group": group,
        "host": hostname,
        "username": "testuser",
        "architecture": "x86_64",
        "platform": platform,
        "location": f"/tmp/fake_agent" if platform != "windows" else f"C:\\Temp\\fake_agent.exe",
        "pid": random.randint(1000, 9999),
        "ppid": random.randint(100, 999),
        "executors": EXECUTORS[platform],
        "privilege": privilege,
        "exe_name": f"fake_agent.exe" if platform == "windows" else f"fake_agent",
        "sleep_min": random.randint(30, 45),
        "sleep_max": random.randint(50, 60),
        "watchdog": 0,
        "contact": "http"
    }
    
    return agent_profile

async def beacon_agent(session, agent_profile, debug=False):
    """Send a beacon to register/update an agent"""
    # Use REST API instead of beacon endpoint (more reliable)
    api_url = f"{CALDERA_URL}/api/v2/agents"
    
    headers = {
        "KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    if debug:
        print(f"  DEBUG: Creating agent via POST {api_url}")
        print(f"  DEBUG: Profile: {json.dumps(agent_profile, indent=2)[:300]}...")
    
    try:
        async with session.post(api_url, json=agent_profile, headers=headers) as response:
            if debug:
                print(f"  DEBUG: Response status: {response.status}")
            
            if response.status == 200:
                response_data = await response.json()
                if debug:
                    print(f"  DEBUG: Created agent with paw: {response_data.get('paw')}")
                
                # Update agent with received PAW
                agent_profile['paw'] = response_data['paw']
                
                return True, agent_profile['paw']
            else:
                text = await response.text()
                if debug:
                    print(f"  DEBUG: Error response: {text}")
                return False, f"HTTP {response.status}: {text}"
    except Exception as e:
        if debug:
            print(f"  DEBUG: Exception: {e}")
        return False, str(e)

async def update_agent_beacon(session, agent_profile):
    """Update an existing agent (simulates heartbeat)"""
    # Use PUT endpoint to update the agent
    paw = agent_profile.get('paw')
    if not paw:
        return False, "No PAW provided"
    
    api_url = f"{CALDERA_URL}/api/v2/agents/{paw}"
    headers = {
        "KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Only send fields that can be updated
    update_data = {
        "group": agent_profile.get("group"),
        "sleep_min": agent_profile.get("sleep_min", 30),
        "sleep_max": agent_profile.get("sleep_max", 60),
        "watchdog": agent_profile.get("watchdog", 0)
    }
    
    try:
        async with session.put(api_url, json=update_data, headers=headers) as response:
            if response.status == 200:
                return True, paw
            else:
                text = await response.text()
                return False, f"HTTP {response.status}: {text}"
    except Exception as e:
        return False, str(e)

async def create_fake_agents(count, groups=None, platforms=None):
    """Create multiple fake agents"""
    async with aiohttp.ClientSession() as session:
        agents = []
        group_list = groups.split(',') if groups else None
        platform_list = platforms.split(',') if platforms else None
        
        print(f"\n🤖 Creating {count} fake agents...")
        print(f"   Groups: {group_list or 'random'}")
        print(f"   Platforms: {platform_list or 'random'}\n")
        
        for i in range(count):
            group = random.choice(group_list) if group_list else None
            platform = random.choice(platform_list) if platform_list else None
            
            agent = generate_agent(platform, group)
            success, result = await beacon_agent(session, agent, debug=(i==0))  # Debug first only
            
            if success:
                agents.append(agent)
                print(f"✅ Created agent {i+1}/{count}: {agent['paw']} ({agent['platform']}/{agent['group']}) - {agent['host']}")
            else:
                print(f"❌ Failed to create agent {i+1}/{count}: {result}")
        
        print(f"\n✅ Successfully created {len(agents)} agents!")
        return agents

async def maintain_agents(agents, interval=30):
    """Maintain agents by sending periodic updates"""
    async with aiohttp.ClientSession() as session:
        print(f"\n🔄 Maintaining {len(agents)} agents (update interval: {interval}s)")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while True:
                for agent in agents:
                    success, result = await update_agent_beacon(session, agent)
                    status = "✅" if success else "❌"
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"{status} [{timestamp}] Update: {agent['paw']} ({agent['host']})")
                
                print(f"\n⏳ Waiting {interval}s before next update...\n")
                await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping agent simulation...")

async def main():
    # Update globals with arguments
    global CALDERA_URL, API_KEY
    
    parser = argparse.ArgumentParser(description="Simulate fake Caldera agents for testing")
    parser.add_argument("--count", type=int, default=5, help="Number of fake agents to create (default: 5)")
    parser.add_argument("--groups", type=str, help="Comma-separated list of groups (e.g., 'red,blue,production')")
    parser.add_argument("--platforms", type=str, help="Comma-separated list of platforms (e.g., 'windows,linux')")
    parser.add_argument("--create-only", action="store_true", help="Only create agents without maintaining beacons")
    parser.add_argument("--beacon-interval", type=int, default=30, help="Beacon interval in seconds (default: 30)")
    parser.add_argument("--server", type=str, default=CALDERA_URL, help=f"Caldera server URL (default: {CALDERA_URL})")
    parser.add_argument("--api-key", type=str, default=API_KEY, help="API key for authentication")
    
    args = parser.parse_args()
    
    CALDERA_URL = args.server
    API_KEY = args.api_key
    
    # Create fake agents
    agents = await create_fake_agents(args.count, args.groups, args.platforms)
    
    if not agents:
        print("\n❌ No agents were created successfully!")
        sys.exit(1)
    
    # Optionally maintain them with periodic beacons
    if not args.create_only:
        await maintain_agents(agents, args.beacon_interval)
    else:
        print("\n✅ Agents created! (use without --create-only to maintain beacons)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
