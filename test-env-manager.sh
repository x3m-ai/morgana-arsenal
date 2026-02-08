#!/bin/bash
# Morgana Arsenal - Test Environment Manager
# Gestione rapida dell'ambiente di test multi-agent

CALDERA_URL="http://localhost:8888"
API_KEY="ADMIN123"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_info() {
    echo -e "${YELLOW}💡 $1${NC}"
}

function show_status() {
    print_header "STATO AMBIENTE TEST MORGANA ARSENAL"
    
    # Conta agenti
    agents_count=$(curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/agents" | jq '. | length' 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_success "Agenti: $agents_count"
        
        # Raggruppa per gruppo
        echo ""
        curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/agents" | \
        jq -r '.[] | .group' | sort | uniq -c | \
        awk '{printf "  🔹 %-15s → %2d agenti\n", $2, $1}'
    else
        print_error "Impossibile recuperare gli agenti"
    fi
    
    echo ""
    
    # Conta operations
    ops_count=$(curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/operations" | jq '. | length' 2>/dev/null)
    if [ $? -eq 0 ]; then
        test_ops=$(curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/operations" | jq '[.[] | select(.name | startswith("Test_"))] | length' 2>/dev/null)
        print_success "Operations: $ops_count totali ($test_ops test operations)"
        
        # Raggruppa per stato
        echo ""
        curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/operations" | \
        jq -r '.[] | .state' | sort | uniq -c | \
        awk '{printf "  🔸 %-15s → %2d operations\n", $2, $1}'
    else
        print_error "Impossibile recuperare le operations"
    fi
    
    echo ""
}

function create_agents() {
    print_header "CREAZIONE AGENTI FITTIZI"
    
    count=${1:-10}
    groups=${2:-"red,blue"}
    
    print_info "Creazione di $count agenti nei gruppi: $groups"
    python3 simulate_agents.py --count $count --groups "$groups" --create-only
}

function create_operations() {
    print_header "CREAZIONE OPERATIONS DI TEST"
    
    python3 create_test_operations.py
}

function cleanup_test_ops() {
    print_header "PULIZIA TEST OPERATIONS"
    
    test_ops=$(curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/operations" | \
               jq -r '.[] | select(.name | startswith("Test_")) | .id')
    
    if [ -z "$test_ops" ]; then
        print_info "Nessuna test operation da eliminare"
        return
    fi
    
    count=0
    for op_id in $test_ops; do
        op_name=$(curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/operations/$op_id" | jq -r '.name' 2>/dev/null)
        echo -e "🗑️  Eliminando: $op_name"
        curl -s -H "KEY: $API_KEY" -X DELETE "$CALDERA_URL/api/v2/operations/$op_id" > /dev/null 2>&1
        ((count++))
    done
    
    print_success "Eliminate $count test operations"
}

function cleanup_fake_agents() {
    print_header "PULIZIA AGENTI FITTIZI"
    
    fake_agents=$(curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/agents" | \
                  jq -r '.[] | select(.host | test("WIN-|ubuntu-|kali-|centos-|debian-|macbook-|imac-|DC-|fake-|test-")) | .paw')
    
    if [ -z "$fake_agents" ]; then
        print_info "Nessun agente fittizio da eliminare"
        return
    fi
    
    count=0
    for paw in $fake_agents; do
        host=$(curl -s -H "KEY: $API_KEY" "$CALDERA_URL/api/v2/agents/$paw" | jq -r '.host' 2>/dev/null)
        echo -e "🗑️  Eliminando: $host ($paw)"
        curl -s -H "KEY: $API_KEY" -X DELETE "$CALDERA_URL/api/v2/agents/$paw" > /dev/null 2>&1
        ((count++))
    done
    
    print_success "Eliminati $count agenti fittizi"
}

function full_cleanup() {
    print_header "PULIZIA COMPLETA AMBIENTE TEST"
    
    echo ""
    cleanup_test_ops
    echo ""
    cleanup_fake_agents
    echo ""
    
    print_success "Ambiente test pulito!"
}

function setup_full_environment() {
    print_header "SETUP AMBIENTE COMPLETO"
    
    echo ""
    print_info "Step 1/2: Creazione agenti fittizi..."
    create_agents 20 "red,blue,production"
    
    echo ""
    print_info "Step 2/2: Creazione operations di test..."
    create_operations
    
    echo ""
    print_success "Ambiente test completo configurato!"
    echo ""
    show_status
}

function show_help() {
    print_header "MORGANA ARSENAL - TEST ENVIRONMENT MANAGER"
    
    cat << EOF

COMANDI DISPONIBILI:

  status              Mostra lo stato corrente dell'ambiente
  
  create-agents       Crea agenti fittizi
                      Uso: $0 create-agents [count] [groups]
                      Esempio: $0 create-agents 15 "red,blue,production"
  
  create-ops          Crea operations di test
  
  setup               Setup completo (20 agenti + operations)
  
  cleanup-ops         Elimina tutte le test operations
  
  cleanup-agents      Elimina tutti gli agenti fittizi
  
  cleanup-all         Pulizia completa (operations + agenti)
  
  help                Mostra questo aiuto

ESEMPI:

  # Stato corrente
  $0 status
  
  # Setup completo
  $0 setup
  
  # Crea 10 agenti red team
  $0 create-agents 10 "red"
  
  # Crea operations di test
  $0 create-ops
  
  # Pulizia completa
  $0 cleanup-all

EOF
}

# Main
case "$1" in
    status)
        show_status
        ;;
    create-agents)
        create_agents "$2" "$3"
        ;;
    create-ops)
        create_operations
        ;;
    setup)
        setup_full_environment
        ;;
    cleanup-ops)
        cleanup_test_ops
        ;;
    cleanup-agents)
        cleanup_fake_agents
        ;;
    cleanup-all)
        full_cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            print_error "Comando sconosciuto: $1"
            echo ""
            show_help
            exit 1
        fi
        ;;
esac
