#!/usr/bin/env python3
"""
Morgana Arsenal - Full Operations Simulator

Avvia operations e simula completamente l'esecuzione creando link manualmente
e popolandoli con risultati realistici. Perfetto per testare con agenti fittizi.
"""

import asyncio
import aiohttp
import json
import random
import base64
import uuid
from datetime import datetime

# Server configuration
CALDERA_URL = "http://localhost:8888"
API_KEY = "ADMIN123"

# Stati link
LINK_STATES = {
    "success": 0,
    "error": 1,
    "timeout": 124,
    "paused": -1
}

# Output realistici
SAMPLE_OUTPUTS = {
    "success": [
        "Command executed successfully",
        "Process completed with exit code 0",
        "File created successfully",
        "User enumerated: admin, testuser, guest",
        "Network connection established",
        "Registry key modified",
        "Service stopped successfully"
    ],
    "error": [
        "Access denied",
        "Permission denied",
        "Command not found",
        "No such file or directory",
        "Connection timeout",
        "Invalid syntax",
        "Authentication failed"
    ],
    "timeout": [
        "Operation timed out after 60 seconds",
        "No response from remote host",
        "Command execution exceeded timeout limit"
    ]
}

async def get_operations(session):
    """Ottieni tutte le operations"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/operations", headers=headers) as response:
        if response.status == 200:
            return await response.json()
        return []

async def get_adversary_abilities(session, adversary_id):
    """Ottieni le abilities di un adversary"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/adversaries/{adversary_id}", headers=headers) as response:
        if response.status == 200:
            adv = await response.json()
            return adv.get('atomic_ordering', [])
        return []

async def get_agents(session, group):
    """Ottieni agenti per gruppo"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/agents", headers=headers) as response:
        if response.status == 200:
            agents = await response.json()
            if group:
                return [a for a in agents if a['group'] == group]
            return agents
        return []

async def start_operation(session, op_id):
    """Avvia operation"""
    headers = {"KEY": API_KEY, "Content-Type": "application/json"}
    data = {"state": "running"}
    async with session.patch(f"{CALDERA_URL}/api/v2/operations/{op_id}", json=data, headers=headers) as response:
        return response.status == 200

async def create_link_via_internal_api(session, op_id, agent_paw, ability_id):
    """
    Crea un link usando l'API interna (non documentata ma usata dalla UI).
    Questo è l'unico modo per creare link con agenti fittizi.
    """
    headers = {
        "KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Usa l'endpoint /plugin/access/exploit che permette di eseguire abilities su agenti
    link_data = {
        "paw": agent_paw,
        "ability_id": ability_id,
        "obfuscator": "plain-text",
        "facts": []
    }
    
    try:
        async with session.post(f"{CALDERA_URL}/plugin/access/exploit", json=link_data, headers=headers) as response:
            if response.status == 200:
                return True, await response.text()
            else:
                return False, await response.text()
    except Exception as e:
        return False, str(e)

async def simulate_full_operation(session, operation, num_links_per_agent=3):
    """Simula completamente una operation con link reali"""
    op_id = operation['id']
    op_name = operation['name']
    group = operation.get('group', '')
    adv_id = operation.get('adversary', {}).get('adversary_id')
    
    print(f"\n{'='*70}")
    print(f"🎯 Operation: {op_name}")
    print(f"   ID: {op_id}")
    print(f"   Gruppo: {group}")
    print(f"{'='*70}")
    
    # 1. Avvia operation
    print(f"\n▶️  Step 1: Avvio operation...")
    if not await start_operation(session, op_id):
        print(f"❌ Errore nell'avvio")
        return False
    print(f"✅ Operation avviata")
    
    # 2. Ottieni abilities dell'adversary
    print(f"\n📋 Step 2: Recupero abilities dell'adversary...")
    abilities = await get_adversary_abilities(session, adv_id)
    if not abilities:
        print(f"⚠️  Nessuna ability trovata per questo adversary")
        return True
    print(f"✅ Trovate {len(abilities)} abilities")
    
    # 3. Ottieni agenti del gruppo
    print(f"\n👥 Step 3: Recupero agenti del gruppo '{group}'...")
    agents = await get_agents(session, group)
    if not agents:
        print(f"❌ Nessun agente trovato nel gruppo")
        return False
    print(f"✅ Trovati {len(agents)} agenti")
    
    # 4. Crea link distribuendo abilities sugli agenti
    print(f"\n🔗 Step 4: Creazione link...")
    links_created = 0
    links_failed = 0
    
    # Distribuisci le prime N abilities su agenti casuali
    abilities_to_use = abilities[:min(num_links_per_agent * len(agents), len(abilities))]
    
    for i, ability_id in enumerate(abilities_to_use, 1):
        # Scegli un agente casuale
        agent = random.choice(agents)
        agent_paw = agent['paw']
        agent_host = agent['host']
        
        print(f"   [{i}/{len(abilities_to_use)}] Assegno ability {ability_id[:8]}... a {agent_host} ({agent_paw})...", end=" ")
        
        success, result = await create_link_via_internal_api(session, op_id, agent_paw, ability_id)
        
        if success:
            links_created += 1
            print(f"✅")
        else:
            links_failed += 1
            print(f"❌ ({result[:50]})")
        
        # Pausa per non sovraccaricare
        await asyncio.sleep(0.3)
    
    print(f"\n📊 Riepilogo link:")
    print(f"   ✅ Creati: {links_created}")
    print(f"   ❌ Falliti: {links_failed}")
    
    if links_created == 0:
        print(f"\n⚠️  Nessun link creato - operation vuota")
        return True
    
    # 5. Attendi un po' per lasciare che il sistema processi
    print(f"\n⏳ Step 5: Attendo elaborazione link...")
    await asyncio.sleep(2)
    
    # 6. Simula risultati per i link creati
    print(f"\n🎲 Step 6: Simulazione risultati...")
    
    # Ottieni i link attuali dell'operation
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/operations/{op_id}", headers=headers) as response:
        if response.status == 200:
            op_data = await response.json()
            chain = op_data.get('chain', [])
            print(f"   Trovati {len(chain)} link nel chain")
            
            # Simula risultati per ogni link
            results_summary = {"success": 0, "error": 0, "timeout": 0}
            
            for link in chain[:20]:  # Limita a 20
                link_id = link.get('id')
                agent_paw = link.get('paw')
                
                # Scegli stato casuale
                state_type = random.choices(
                    ["success", "error", "timeout"],
                    weights=[70, 20, 10],
                    k=1
                )[0]
                
                status = LINK_STATES[state_type]
                output = random.choice(SAMPLE_OUTPUTS[state_type])
                stderr = random.choice(SAMPLE_OUTPUTS["error"]) if state_type == "error" else ""
                
                # Simula invio risultato
                result_data = {
                    "paw": agent_paw,
                    "results": [{
                        "id": link_id,
                        "output": base64.b64encode(output.encode()).decode(),
                        "stderr": base64.b64encode(stderr.encode()).decode() if stderr else "",
                        "exit_code": status if status >= 0 else 0,
                        "status": status,
                        "pid": random.randint(1000, 9999)
                    }]
                }
                
                beacon_b64 = base64.b64encode(json.dumps(result_data).encode()).decode()
                
                try:
                    async with session.post(f"{CALDERA_URL}/beacon?paw={agent_paw}", data=beacon_b64) as resp:
                        if resp.status == 200:
                            results_summary[state_type] += 1
                except:
                    pass
                
                await asyncio.sleep(0.2)
            
            print(f"\n   ✅ Success: {results_summary['success']}")
            print(f"   ❌ Error: {results_summary['error']}")
            print(f"   ⏱️  Timeout: {results_summary['timeout']}")
    
    print(f"\n{'='*70}")
    print(f"✅ Operation simulata completamente!")
    print(f"{'='*70}\n")
    
    return True

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Simula completamente operations con link")
    parser.add_argument("--count", type=int, default=3, help="Numero operations da simulare")
    parser.add_argument("--group", type=str, help="Solo operations di un gruppo")
    parser.add_argument("--links-per-agent", type=int, default=3, help="Link per agente (default: 3)")
    
    args = parser.parse_args()
    
    async with aiohttp.ClientSession() as session:
        print("\n" + "="*70)
        print("🎬 MORGANA ARSENAL - FULL OPERATIONS SIMULATOR")
        print("="*70)
        print("\nQuesto script:")
        print("  1. Avvia operations in paused")
        print("  2. Crea link manualmente assegnando abilities")
        print("  3. Simula risultati realistici")
        print("="*70)
        
        # Ottieni operations
        ops = await get_operations(session)
        test_ops = [o for o in ops if o['name'].startswith('Test_') and o.get('state') == 'paused']
        
        if args.group:
            test_ops = [o for o in test_ops if o.get('group') == args.group]
        
        if not test_ops:
            print(f"\n❌ Nessuna test operation in paused trovata!")
            return
        
        ops_to_run = test_ops[:args.count]
        
        print(f"\n📋 Trovate {len(test_ops)} test operations in paused")
        print(f"🎯 Operations da simulare: {len(ops_to_run)}\n")
        
        for op in ops_to_run:
            try:
                await simulate_full_operation(session, op, args.links_per_agent)
            except Exception as e:
                print(f"❌ Errore: {e}\n")
        
        print("\n" + "="*70)
        print("💡 NEXT STEPS:")
        print("="*70)
        print("  1. Apri http://localhost:8888")
        print("  2. Vai su Campaigns → Operations")
        print("  3. Visualizza le operations con link e risultati")
        print("  4. Controlla il graph e i dettagli dei link")
        print("  5. Usa Merlino per sincronizzare e analizzare!")
        print("="*70 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted!")
