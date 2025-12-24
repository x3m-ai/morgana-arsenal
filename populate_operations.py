#!/usr/bin/env python3
"""
Morgana Arsenal - Populate Operations with Fake Links

Popola le operations con link fittizi per simulare esecuzione.
Perfetto per testare Merlino con operations complete.
"""

import requests
import json
import random
import uuid
import base64
from datetime import datetime, timedelta

URL = "http://localhost:8888"
HEADERS = {"KEY": "ADMIN123"}

# Stati link realistici
LINK_STATUSES = {
    0: "SUCCESS",      # 60% probabilità
    1: "ERROR",        # 20% probabilità  
    124: "TIMEOUT",    # 15% probabilità
    -1: "PAUSED"       # 5% probabilità
}

def get_operations():
    """Ottieni operations"""
    resp = requests.get(f"{URL}/api/v2/operations", headers=HEADERS)
    return resp.json() if resp.status_code == 200 else []

def get_agents(group=None):
    """Ottieni agenti"""
    resp = requests.get(f"{URL}/api/v2/agents", headers=HEADERS)
    agents = resp.json() if resp.status_code == 200 else []
    if group:
        return [a for a in agents if a['group'] == group]
    return agents

def get_adversary_abilities(adversary_id):
    """Ottieni abilities di un adversary"""
    resp = requests.get(f"{URL}/api/v2/adversaries/{adversary_id}", headers=HEADERS)
    if resp.status_code == 200:
        adv = resp.json()
        return adv.get('atomic_ordering', [])
    return []

def get_ability_details(ability_id):
    """Ottieni dettagli di una ability"""
    resp = requests.get(f"{URL}/api/v2/abilities/{ability_id}", headers=HEADERS)
    return resp.json() if resp.status_code == 200 else None

def create_fake_link_data(operation_id, ability, agent, index):
    """Crea dati per un link fittizio"""
    
    # Scegli stato casuale
    status = random.choices(
        list(LINK_STATUSES.keys()),
        weights=[60, 20, 15, 5],
        k=1
    )[0]
    
    # Output fittizio basato sullo stato
    if status == 0:  # SUCCESS
        output = f"Command executed successfully on {agent['host']}\nExit code: 0"
    elif status == 1:  # ERROR
        output = f"Error: Command failed on {agent['host']}\nAccess denied"
    elif status == 124:  # TIMEOUT
        output = f"Command timed out on {agent['host']}"
    else:  # PAUSED
        output = ""
    
    # Timestamp realistico (negli ultimi 30 minuti)
    finish_time = datetime.now() - timedelta(minutes=random.randint(1, 30))
    
    # Executor appropriato per piattaforma
    executors = agent.get('executors', [])
    executor = executors[0] if executors else 'sh'
    
    # Comando dall'ability
    ability_data = get_ability_details(ability['ability_id'])
    command = "echo 'fake command'"
    if ability_data:
        platforms = ability_data.get('platforms', {})
        agent_platform = agent.get('platform', 'linux')
        if agent_platform in platforms:
            platform_data = platforms[agent_platform]
            if executor in platform_data:
                command = platform_data[executor].get('command', command)
    
    link_data = {
        "id": str(uuid.uuid4()),
        "operation": operation_id,
        "paw": agent['paw'],
        "ability": {
            "ability_id": ability['ability_id'],
            "name": ability.get('name', 'Unknown'),
            "tactic": ability.get('tactic', 'unknown'),
            "technique_id": ability.get('technique_id', ''),
            "technique_name": ability.get('technique_name', '')
        },
        "executor": executor,
        "command": command,
        "status": status,
        "score": 0 if status == 0 else 1,
        "jitter": 2,
        "cleanup": 0,
        "pin": 0,
        "host": agent['host'],
        "output": base64.b64encode(output.encode()).decode() if output else "",
        "pid": str(random.randint(1000, 9999)),
        "finish": finish_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decide": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collect": finish_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "visibility": 50
    }
    
    return link_data

def populate_operation_with_links(operation, num_links=5):
    """Popola una operation con link fittizi"""
    
    op_id = operation['id']
    op_name = operation['name']
    op_group = operation.get('group', '')
    adversary_id = operation.get('adversary', {}).get('adversary_id')
    
    print(f"\n{'='*70}")
    print(f"🎯 Operation: {op_name}")
    print(f"   ID: {op_id}")
    print(f"   Gruppo: {op_group}")
    print(f"{'='*70}")
    
    # Ottieni agenti del gruppo
    agents = get_agents(op_group)
    if not agents:
        print(f"❌ Nessun agente nel gruppo '{op_group}'")
        return False
    
    print(f"✅ Trovati {len(agents)} agenti nel gruppo")
    
    # Ottieni abilities dell'adversary
    ability_ids = get_adversary_abilities(adversary_id)
    if not ability_ids:
        print(f"⚠️  Nessuna ability nell'adversary")
        return False
    
    print(f"✅ Trovate {len(ability_ids)} abilities nell'adversary")
    
    # Ottieni dettagli abilities
    abilities = []
    for ab_id in ability_ids[:num_links]:
        ab = get_ability_details(ab_id)
        if ab:
            abilities.append(ab)
    
    print(f"✅ Caricate {len(abilities)} abilities")
    
    # Crea link distribuendo sugli agenti
    print(f"\n🔗 Creazione {num_links} link fittizi...")
    
    links = []
    for i, ability in enumerate(abilities[:num_links], 1):
        # Scegli agente casuale dal gruppo
        agent = random.choice(agents)
        
        # Crea link fittizio
        link = create_fake_link_data(op_id, ability, agent, i)
        links.append(link)
        
        status_emoji = "✅" if link['status'] == 0 else "❌" if link['status'] == 1 else "⏱️" if link['status'] == 124 else "⏸️"
        status_name = LINK_STATUSES[link['status']]
        
        print(f"   [{i}/{num_links}] {status_emoji} {agent['host'][:15]:<15} | {ability['name'][:30]:<30} | {status_name}")
    
    # Aggiorna l'operation con i link tramite API
    print(f"\n📤 Invio link all'operation...")
    
    # Prepara il payload per l'update
    # NOTA: Questo usa un endpoint interno che potrebbe non funzionare direttamente
    # L'alternativa è usare il meccanismo di beacon per ogni link
    
    for link in links:
        # Simula che l'agente invii il risultato del link
        agent_paw = link['paw']
        
        result_payload = {
            "paw": agent_paw,
            "results": [{
                "id": link['id'],
                "output": link['output'],
                "stderr": "",
                "exit_code": 0 if link['status'] == 0 else link['status'],
                "status": link['status'],
                "pid": int(link['pid'])
            }]
        }
        
        # Converti in base64 come fa un vero agente
        beacon_data = json.dumps(result_payload)
        beacon_b64 = base64.b64encode(beacon_data.encode()).decode()
        
        # Invia tramite beacon
        try:
            resp = requests.post(
                f"{URL}/beacon?paw={agent_paw}",
                data=beacon_b64,
                headers={"Content-Type": "application/octet-stream"}
            )
            
            if resp.status_code != 200:
                print(f"      ⚠️  Link {link['id'][:8]}: errore invio (HTTP {resp.status_code})")
        except Exception as e:
            print(f"      ❌ Link {link['id'][:8]}: {e}")
    
    print(f"✅ Link popolati per operation!")
    print(f"{'='*70}\n")
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Popola operations con link fittizi")
    parser.add_argument("--count", type=int, default=3, help="Numero operations da popolare")
    parser.add_argument("--links", type=int, default=5, help="Link per operation")
    parser.add_argument("--group", type=str, help="Solo operations di un gruppo")
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🎬 MORGANA ARSENAL - POPULATE OPERATIONS")
    print("="*70)
    print("\nQuesto script popola operations con link fittizi")
    print("per simulare esecuzione e permettere sync con Merlino.")
    print("="*70)
    
    # Ottieni operations
    ops = get_operations()
    test_ops = [o for o in ops if o['name'].startswith('Test_')]
    
    if args.group:
        test_ops = [o for o in test_ops if o.get('group') == args.group]
    
    if not test_ops:
        print(f"\n❌ Nessuna test operation trovata!")
        return
    
    # Limita al numero richiesto
    ops_to_populate = test_ops[:args.count]
    
    print(f"\n📋 Trovate {len(test_ops)} test operations")
    print(f"🎯 Operations da popolare: {len(ops_to_populate)}")
    print(f"🔗 Link per operation: {args.links}\n")
    
    success_count = 0
    for op in ops_to_populate:
        try:
            if populate_operation_with_links(op, args.links):
                success_count += 1
        except Exception as e:
            print(f"❌ Errore: {e}\n")
    
    print("\n" + "="*70)
    print(f"✅ Completato: {success_count}/{len(ops_to_populate)} operations popolate")
    print("="*70)
    print("\n💡 NEXT STEPS:")
    print("   1. Apri Merlino Excel")
    print("   2. Fai Sync per vedere le operations con link")
    print("   3. Analizza gli agenti assegnati e i risultati")
    print("   4. Testa le nuove feature!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
