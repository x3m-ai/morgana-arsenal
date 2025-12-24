#!/usr/bin/env python3
"""
Morgana Arsenal - Link Simulator

Avvia operations e simula l'esecuzione di abilities con risultati realistici.
Crea link in vari stati: success, error, timeout, high_viz per testare
l'integrazione e sviluppare nuove feature.
"""

import asyncio
import aiohttp
import json
import random
import base64
from datetime import datetime

# Server configuration
CALDERA_URL = "http://localhost:8888"
API_KEY = "ADMIN123"

# Simulazione output realistici per piattaforma/executor
REALISTIC_OUTPUTS = {
    "windows": {
        "cmd": [
            "Microsoft Windows [Version 10.0.19045.3803]\nC:\\Users\\testuser>",
            "The command completed successfully.",
            "Access is denied.",
            "The system cannot find the file specified.",
            "1 file(s) copied."
        ],
        "psh": [
            "Name                           Value\n----                           -----\nPSVersion                      5.1.19041.3803",
            "Get-Process : Cannot find a process with the name 'notepad'.",
            "Directory: C:\\Users\\testuser\\Desktop\n\nMode                LastWriteTime     Length Name",
            "[System.Management.Automation.PSCredential]",
            "True\nFalse"
        ]
    },
    "linux": {
        "sh": [
            "total 128\ndrwxr-xr-x  2 root root  4096 Dec 23 10:30 bin",
            "uid=1000(testuser) gid=1000(testuser) groups=1000(testuser)",
            "bash: command not found",
            "Linux ubuntu-525 5.15.0-91-generic #101-Ubuntu SMP",
            "testuser  pts/0    2025-12-23 10:30 (192.168.1.10)"
        ],
        "bash": [
            "#!/bin/bash\nexport PATH=/usr/local/bin:$PATH",
            "Permission denied",
            "No such file or directory",
            "testuser ALL=(ALL:ALL) NOPASSWD:ALL",
            "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=15.2 ms"
        ]
    },
    "darwin": {
        "sh": [
            "Darwin macbook-651.local 22.6.0 Darwin Kernel Version 22.6.0",
            "testuser   console  Dec 23 10:30",
            "total 0\ndrwx------+  5 testuser  staff   160 Dec 23 10:30 Desktop",
            "/usr/bin/python3\nPython 3.11.4",
            "bash: command not found"
        ]
    }
}

# Stati possibili per i link
LINK_STATES = {
    "success": 0,      # Esecuzione riuscita
    "error": 1,        # Errore generico
    "timeout": 124,    # Timeout
    "paused": -1,      # Link in pausa
    "high_viz": -5     # High visibility (richiede conferma)
}

async def get_operations(session, state=None):
    """Ottieni operations"""
    headers = {"KEY": API_KEY}
    url = f"{CALDERA_URL}/api/v2/operations"
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            ops = await response.json()
            # Filtra per stato se specificato
            if state:
                return [op for op in ops if op.get('state') == state]
            return ops
        return []

async def start_operation(session, op_id):
    """Avvia una operation"""
    headers = {
        "KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {"state": "running"}
    
    async with session.patch(f"{CALDERA_URL}/api/v2/operations/{op_id}", json=data, headers=headers) as response:
        return response.status == 200

async def get_operation_details(session, op_id):
    """Ottieni dettagli completi di una operation"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/operations/{op_id}", headers=headers) as response:
        if response.status == 200:
            return await response.json()
        return None

async def get_agents_for_operation(session, group):
    """Ottieni agenti per un gruppo specifico"""
    headers = {"KEY": API_KEY}
    async with session.get(f"{CALDERA_URL}/api/v2/agents", headers=headers) as response:
        if response.status == 200:
            agents = await response.json()
            return [a for a in agents if a['group'] == group]
        return []

async def create_manual_link(session, op_id, agent_paw, ability_id):
    """Crea manualmente un link per simulare l'assegnazione di un'ability"""
    headers = {
        "KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    link_data = {
        "paw": agent_paw,
        "ability_id": ability_id,
        "operation_id": op_id
    }
    
    try:
        # Usa l'endpoint per taskare manualmente un agente
        async with session.post(f"{CALDERA_URL}/plugin/access/exploit", json=link_data, headers=headers) as response:
            return response.status == 200
    except Exception as e:
        return False
    """Simula il risultato di un link"""
    headers = {
        "KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Scegli stato casuale con probabilità diverse
    state_choice = random.choices(
        list(LINK_STATES.keys()),
        weights=[70, 15, 10, 3, 2],  # 70% success, 15% error, 10% timeout, 3% paused, 2% high_viz
        k=1
    )[0]
    
    status = LINK_STATES[state_choice]
    
    # Genera output realistico
    platform_outputs = REALISTIC_OUTPUTS.get(platform, REALISTIC_OUTPUTS["linux"])
    executor_outputs = platform_outputs.get(executor, platform_outputs.get("sh", ["Command executed"]))
    output = random.choice(executor_outputs)
    
    # Stderr solo per errori
    stderr = ""
    if status == 1:  # error
        stderr = random.choice([
            "Error: Command failed with exit code 1",
            "Permission denied",
            "No such file or directory",
            "Access denied",
            "Command not found"
        ])
    
    # Exit code
    exit_code = status if status >= 0 else 0
    
    # Encode in base64 (come fa Caldera)
    output_b64 = base64.b64encode(output.encode()).decode()
    stderr_b64 = base64.b64encode(stderr.encode()).decode() if stderr else ""
    
    # Crea il payload del risultato
    result_data = {
        "paw": agent_paw,
        "results": [{
            "id": link_id,
            "output": output_b64,
            "stderr": stderr_b64,
            "exit_code": exit_code,
            "status": status,
            "pid": random.randint(1000, 9999)
        }]
    }
    
    # Invia tramite beacon (come farebbe un vero agente)
    beacon_data = json.dumps(result_data)
    beacon_b64 = base64.b64encode(beacon_data.encode()).decode()
    
    try:
        async with session.post(f"{CALDERA_URL}/beacon?paw={agent_paw}", data=beacon_b64, headers={}) as response:
            return response.status == 200, state_choice
    except Exception as e:
        return False, f"error: {e}"

async def simulate_operation_execution(session, operation, simulate_results=True):
    """Simula l'esecuzione di una operation"""
    op_id = operation['id']
    op_name = operation['name']
    group = operation.get('group', 'N/A')
    
    print(f"\n🎯 Operation: {op_name}")
    print(f"   ID: {op_id}")
    print(f"   Gruppo: {group}")
    
    # Avvia la operation
    print(f"   ▶️  Avvio operation...")
    success = await start_operation(session, op_id)
    if not success:
        print(f"   ❌ Errore nell'avvio")
        return False
    
    print(f"   ✅ Operation avviata!")
    
    # Attendi che vengano creati i link (il planner assegna le abilities)
    print(f"   ⏳ Attendo creazione link...")
    await asyncio.sleep(3)
    
    # Ottieni i dettagli con i link creati
    op_details = await get_operation_details(session, op_id)
    if not op_details:
        print(f"   ❌ Impossibile ottenere dettagli operation")
        return False
    
    chain = op_details.get('chain', [])
    print(f"   📊 Link creati: {len(chain)}")
    
    if not simulate_results or len(chain) == 0:
        return True
    
    # Simula risultati per i link
    print(f"   🔄 Simulazione risultati...")
    
    results_summary = {
        "success": 0,
        "error": 0,
        "timeout": 0,
        "paused": 0,
        "high_viz": 0
    }
    
    for i, link in enumerate(chain[:10], 1):  # Limita a 10 link per non sovraccaricare
        link_id = link.get('id')
        agent_paw = link.get('paw')
        ability_name = link.get('ability', {}).get('name', 'Unknown')
        executor = link.get('executor', 'sh')
        
        # Ottieni la piattaforma dell'agente
        platform = "linux"  # default
        if 'command' in link:
            cmd = link['command']
            if 'powershell' in cmd.lower() or 'cmd.exe' in cmd.lower():
                platform = "windows"
            elif 'darwin' in cmd.lower() or '/usr/bin' in cmd:
                platform = "darwin"
        
        success, state = await simulate_link_result(session, op_id, link_id, agent_paw, platform, executor)
        
        if success:
            results_summary[state] += 1
            emoji = "✅" if state == "success" else "❌" if state == "error" else "⏱️" if state == "timeout" else "⏸️"
            print(f"      {emoji} Link {i}/{len(chain)}: {ability_name[:30]:<30} [{state.upper()}]")
        else:
            print(f"      ❌ Link {i}: Errore simulazione")
        
        # Piccola pausa tra i link
        await asyncio.sleep(0.5)
    
    # Riepilogo
    print(f"\n   📈 Riepilogo risultati:")
    print(f"      ✅ Success: {results_summary['success']}")
    print(f"      ❌ Error: {results_summary['error']}")
    print(f"      ⏱️  Timeout: {results_summary['timeout']}")
    print(f"      ⏸️  Paused: {results_summary['paused']}")
    print(f"      🔒 High Viz: {results_summary['high_viz']}")
    
    return True

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Simula esecuzione operations con link realistici")
    parser.add_argument("--all", action="store_true", help="Avvia tutte le test operations")
    parser.add_argument("--count", type=int, default=3, help="Numero di operations da avviare (default: 3)")
    parser.add_argument("--group", type=str, help="Avvia solo operations di un gruppo specifico")
    parser.add_argument("--no-results", action="store_true", help="Avvia senza simulare risultati")
    parser.add_argument("--operation-id", type=str, help="Avvia una operation specifica per ID")
    
    args = parser.parse_args()
    
    async with aiohttp.ClientSession() as session:
        print("\n" + "="*70)
        print("🎬 MORGANA ARSENAL - LINK SIMULATOR")
        print("="*70)
        
        # Ottieni operations in paused
        paused_ops = await get_operations(session, state="paused")
        
        # Filtra test operations
        test_ops = [op for op in paused_ops if op['name'].startswith('Test_')]
        
        if args.operation_id:
            # Avvia operation specifica
            op_details = await get_operation_details(session, args.operation_id)
            if op_details:
                test_ops = [op_details]
            else:
                print(f"\n❌ Operation {args.operation_id} non trovata!")
                return
        elif args.group:
            # Filtra per gruppo
            test_ops = [op for op in test_ops if op.get('group') == args.group]
        
        if not test_ops:
            print(f"\n❌ Nessuna test operation in paused trovata!")
            print(f"💡 Esegui prima: python3 create_test_operations.py")
            return
        
        print(f"\n📋 Trovate {len(test_ops)} test operations in paused")
        
        # Determina quante operations avviare
        if args.all:
            ops_to_run = test_ops
        else:
            ops_to_run = test_ops[:args.count]
        
        print(f"🎯 Operations da avviare: {len(ops_to_run)}")
        print()
        
        # Avvia e simula ogni operation
        success_count = 0
        for op in ops_to_run:
            try:
                result = await simulate_operation_execution(
                    session, 
                    op, 
                    simulate_results=not args.no_results
                )
                if result:
                    success_count += 1
            except Exception as e:
                print(f"   ❌ Errore: {e}")
        
        print("\n" + "="*70)
        print(f"✅ Completato: {success_count}/{len(ops_to_run)} operations simulate con successo")
        print("="*70)
        print("\n💡 NEXT STEPS:")
        print("   1. Apri http://localhost:8888")
        print("   2. Vai su Campaigns → Operations")
        print("   3. Visualizza i risultati e il graph delle operations")
        print("   4. Usa questa base per implementare feature in Merlino!")
        print("="*70 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted!")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
