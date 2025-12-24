#!/usr/bin/env python3
"""
Morgana Arsenal - Test Operations Creator

Crea operations di test con adversaries casuali e agenti distribuiti
per simulare scenari realistici multi-agent.
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime

# Server configuration
CALDERA_URL = "http://localhost:8888"
API_KEY = "ADMIN123"

async def get_agents(session):
    """Ottieni tutti gli agenti disponibili"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/agents", headers=headers) as response:
        if response.status == 200:
            agents = await response.json()
            return agents
        return []

async def get_adversaries(session):
    """Ottieni tutti gli adversaries disponibili"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/adversaries", headers=headers) as response:
        if response.status == 200:
            adversaries = await response.json()
            # Filtra adversaries che hanno abilities
            return [adv for adv in adversaries if adv.get('atomic_ordering') and len(adv['atomic_ordering']) > 0]
        return []

async def get_planners(session):
    """Ottieni tutti i planners disponibili"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/planners", headers=headers) as response:
        if response.status == 200:
            planners = await response.json()
            return planners
        return []

async def get_sources(session):
    """Ottieni tutte le fact sources disponibili"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/sources", headers=headers) as response:
        if response.status == 200:
            sources = await response.json()
            return sources
        return []

async def create_operation(session, name, adversary_id, group, planner_id, source_id, state="paused"):
    """Crea una nuova operation"""
    headers = {
        "KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    operation_data = {
        "name": name,
        "adversary": {"adversary_id": adversary_id},
        "auto_close": False,
        "state": state,
        "group": group,
        "planner": {"id": planner_id},
        "source": {"id": source_id},
        "jitter": "2/8",
        "visibility": 50,
        "autonomous": 1,
        "obfuscator": "plain-text"
    }
    
    try:
        async with session.post(f"{CALDERA_URL}/api/v2/operations", json=operation_data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return True, result
            else:
                text = await response.text()
                return False, f"HTTP {response.status}: {text}"
    except Exception as e:
        return False, str(e)

async def main():
    async with aiohttp.ClientSession() as session:
        print("\n🔍 Recupero dati dal server...\n")
        
        # Ottieni risorse disponibili
        agents = await get_agents(session)
        adversaries = await get_adversaries(session)
        planners = await get_planners(session)
        sources = await get_sources(session)
        
        if not agents:
            print("❌ Nessun agente trovato! Crea prima degli agenti con simulate_agents.py")
            return
        
        if not adversaries:
            print("❌ Nessun adversary trovato!")
            return
        
        if not planners:
            print("❌ Nessun planner trovato!")
            return
        
        # Usa il primo source disponibile o basic
        source_id = sources[0]['id'] if sources else "ed32b9c3-9593-4c33-b0db-e2007315096b"
        
        print(f"✅ Trovati {len(agents)} agenti")
        print(f"✅ Trovati {len(adversaries)} adversaries")
        print(f"✅ Trovati {len(planners)} planners")
        print(f"✅ Source ID: {source_id}\n")
        
        # Raggruppa agenti per gruppo
        agents_by_group = {}
        for agent in agents:
            group = agent['group']
            if group not in agents_by_group:
                agents_by_group[group] = []
            agents_by_group[group].append(agent)
        
        print(f"📋 Gruppi disponibili:")
        for group, group_agents in agents_by_group.items():
            platforms = {}
            for a in group_agents:
                platform = a['platform']
                platforms[platform] = platforms.get(platform, 0) + 1
            platform_str = ", ".join([f"{k}({v})" for k, v in platforms.items()])
            print(f"   - {group}: {len(group_agents)} agenti [{platform_str}]")
        
        print("\n🎯 Creazione operations...\n")
        
        # Crea operations per ogni gruppo con adversaries casuali
        operations_created = []
        available_planners = [p for p in planners if p['id'] != 'gameplan']  # Escludi gameplan
        
        for group_name, group_agents in agents_by_group.items():
            # Crea 2-3 operations per gruppo
            num_operations = min(random.randint(2, 3), len(adversaries))
            
            for i in range(num_operations):
                # Scegli adversary e planner casuali
                adversary = random.choice(adversaries)
                planner = random.choice(available_planners) if available_planners else planners[0]
                
                # Nome operation con timestamp
                timestamp = datetime.now().strftime("%H%M%S")
                op_name = f"Test_{group_name}_{adversary['name'][:15]}_{timestamp}_{i+1}"
                
                # Crea operation in stato paused
                success, result = await create_operation(
                    session,
                    name=op_name,
                    adversary_id=adversary['adversary_id'],
                    group=group_name,
                    planner_id=planner['id'],
                    source_id=source_id,
                    state="paused"
                )
                
                if success:
                    op_id = result.get('id', 'unknown')
                    num_abilities = len(adversary.get('atomic_ordering', []))
                    print(f"✅ Creata: {op_name}")
                    print(f"   └─ ID: {op_id}")
                    print(f"   └─ Adversary: {adversary['name']} ({num_abilities} abilities)")
                    print(f"   └─ Planner: {planner['name']}")
                    print(f"   └─ Gruppo: {group_name} ({len(group_agents)} agenti)")
                    print(f"   └─ Stato: PAUSED")
                    print()
                    operations_created.append({
                        'name': op_name,
                        'id': op_id,
                        'group': group_name,
                        'adversary': adversary['name'],
                        'num_agents': len(group_agents)
                    })
                else:
                    print(f"❌ Errore creando operation per {group_name}: {result}\n")
        
        # Riepilogo finale
        print("\n" + "="*60)
        print(f"📊 RIEPILOGO")
        print("="*60)
        print(f"✅ Operations create: {len(operations_created)}")
        
        # Raggruppa per gruppo
        ops_by_group = {}
        for op in operations_created:
            group = op['group']
            if group not in ops_by_group:
                ops_by_group[group] = []
            ops_by_group[group].append(op)
        
        for group, ops in ops_by_group.items():
            print(f"\n🔹 Gruppo '{group}': {len(ops)} operations")
            for op in ops:
                print(f"   • {op['name']}")
                print(f"     Adversary: {op['adversary']}, Agenti: {op['num_agents']}")
        
        print(f"\n💡 Le operations sono in stato PAUSED.")
        print(f"   Vai su Campaigns → Operations nella UI per avviarle!")
        print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Interrupted!")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
