#!/bin/bash

# ════════════════════════════════════════════════════════════════════════════
# MISP Integration Monitor - Morgana Arsenal
# ════════════════════════════════════════════════════════════════════════════
# Monitora le chiamate API da Merlino a MISP in tempo reale
# Mostra eventi creati, errori e statistiche
# ════════════════════════════════════════════════════════════════════════════

COLOR_RESET="\e[0m"
COLOR_GREEN="\e[32m"
COLOR_YELLOW="\e[33m"
COLOR_RED="\e[31m"
COLOR_BLUE="\e[34m"
COLOR_CYAN="\e[36m"
COLOR_MAGENTA="\e[35m"

MISP_LOG="/var/log/nginx/misp-access.log"
MISP_ERROR_LOG="/var/log/nginx/misp-error.log"

echo -e "${COLOR_CYAN}"
echo "════════════════════════════════════════════════════════════════════════════"
echo "  MISP INTEGRATION MONITOR - Morgana Arsenal"
echo "════════════════════════════════════════════════════════════════════════════"
echo -e "${COLOR_RESET}"
echo ""
echo -e "${COLOR_GREEN}📍 MISP Installation:${COLOR_RESET} /var/www/MISP"
echo -e "${COLOR_GREEN}🔌 HTTP Endpoint:${COLOR_RESET} http://192.168.124.133:8080"
echo -e "${COLOR_GREEN}🔒 HTTPS Endpoint:${COLOR_RESET} https://192.168.124.133:8443"
echo -e "${COLOR_GREEN}📊 Access Log:${COLOR_RESET} $MISP_LOG"
echo ""

# Funzione per mostrare statistiche
show_stats() {
    echo -e "${COLOR_YELLOW}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}  STATISTICHE ULTIME 24 ORE${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
    
    local total_requests=$(sudo grep -c "POST /events/add" "$MISP_LOG" 2>/dev/null || echo "0")
    local success_200=$(sudo grep "POST /events/add" "$MISP_LOG" 2>/dev/null | grep -c " 200 " || echo "0")
    local errors_4xx=$(sudo grep "POST /events/add" "$MISP_LOG" 2>/dev/null | grep -cE " 4[0-9]{2} " || echo "0")
    local errors_5xx=$(sudo grep "POST /events/add" "$MISP_LOG" 2>/dev/null | grep -cE " 5[0-9]{2} " || echo "0")
    
    echo -e "${COLOR_GREEN}✅ Richieste Totali:${COLOR_RESET} $total_requests"
    echo -e "${COLOR_GREEN}✅ Eventi Creati (200):${COLOR_RESET} $success_200"
    echo -e "${COLOR_RED}❌ Errori Client (4xx):${COLOR_RESET} $errors_4xx"
    echo -e "${COLOR_RED}❌ Errori Server (5xx):${COLOR_RESET} $errors_5xx"
    echo ""
}

# Funzione per estrarre info da evento
parse_event() {
    local log_line="$1"
    local timestamp=$(echo "$log_line" | awk '{print $4 " " $5}' | tr -d '[]')
    local status=$(echo "$log_line" | awk '{print $9}')
    local size=$(echo "$log_line" | awk '{print $10}')
    local protocol=$(echo "$log_line" | awk '{print $6}' | tr -d '"')
    
    if [[ "$status" == "200" ]]; then
        echo -e "${COLOR_GREEN}✅ EVENT CREATED${COLOR_RESET} | ${COLOR_CYAN}${timestamp}${COLOR_RESET} | Status: ${COLOR_GREEN}${status}${COLOR_RESET} | Size: ${size}B | ${protocol}"
    elif [[ "$status" =~ ^4 ]]; then
        echo -e "${COLOR_YELLOW}⚠️  CLIENT ERROR${COLOR_RESET} | ${COLOR_CYAN}${timestamp}${COLOR_RESET} | Status: ${COLOR_YELLOW}${status}${COLOR_RESET} | ${protocol}"
    elif [[ "$status" =~ ^5 ]]; then
        echo -e "${COLOR_RED}❌ SERVER ERROR${COLOR_RESET} | ${COLOR_CYAN}${timestamp}${COLOR_RESET} | Status: ${COLOR_RED}${status}${COLOR_RESET} | ${protocol}"
    else
        echo -e "${COLOR_BLUE}ℹ️  REQUEST${COLOR_RESET} | ${COLOR_CYAN}${timestamp}${COLOR_RESET} | Status: ${status} | ${protocol}"
    fi
}

# Menu principale
echo -e "${COLOR_MAGENTA}Seleziona modalità:${COLOR_RESET}"
echo "1) Monitor in Tempo Reale (tail -f)"
echo "2) Mostra Statistiche"
echo "3) Ultimi 20 Eventi"
echo "4) Ultimi Errori"
echo "5) Test API Call"
echo ""
read -p "Scelta [1-5]: " choice

case $choice in
    1)
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo -e "${COLOR_CYAN}  MONITOR TEMPO REALE - Premi Ctrl+C per uscire${COLOR_RESET}"
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo ""
        sudo tail -f "$MISP_LOG" | grep --line-buffered "POST /events/add" | while read -r line; do
            parse_event "$line"
        done
        ;;
    
    2)
        show_stats
        ;;
    
    3)
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo -e "${COLOR_CYAN}  ULTIMI 20 EVENTI${COLOR_RESET}"
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo ""
        sudo grep "POST /events/add" "$MISP_LOG" | tail -20 | while read -r line; do
            parse_event "$line"
        done
        echo ""
        ;;
    
    4)
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo -e "${COLOR_CYAN}  ULTIMI ERRORI${COLOR_RESET}"
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo ""
        echo -e "${COLOR_YELLOW}Errori Nginx:${COLOR_RESET}"
        sudo tail -20 "$MISP_ERROR_LOG" 2>/dev/null || echo "Nessun errore recente"
        echo ""
        echo -e "${COLOR_YELLOW}Errori 4xx/5xx nelle richieste:${COLOR_RESET}"
        sudo grep "POST /events/add" "$MISP_LOG" | grep -E " [45][0-9]{2} " | tail -10 | while read -r line; do
            parse_event "$line"
        done
        ;;
    
    5)
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo -e "${COLOR_CYAN}  TEST API CALL${COLOR_RESET}"
        echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
        echo ""
        echo -e "${COLOR_YELLOW}Scegli protocollo:${COLOR_RESET}"
        echo "1) HTTP (8080)"
        echo "2) HTTPS (8443)"
        read -p "Scelta [1-2]: " proto_choice
        
        if [[ "$proto_choice" == "1" ]]; then
            endpoint="http://192.168.124.133:8080/events/add"
            curl_opts=""
        else
            endpoint="https://192.168.124.133:8443/events/add"
            curl_opts="-k"
        fi
        
        echo ""
        echo -e "${COLOR_GREEN}Invio richiesta a: $endpoint${COLOR_RESET}"
        echo ""
        
        response=$(curl $curl_opts -X POST "$endpoint" \
            -H "Authorization: 3B1Vnm9Il6Gaj3LRoS3qeRtwT8uHLoqWOK6z5Wjm" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            -w "\nHTTP_CODE:%{http_code}" \
            -d '{
              "Event": {
                "info": "TEST: Monitor Script",
                "threat_level_id": "2",
                "analysis": "1",
                "distribution": "0",
                "Tag": [
                  {"name": "merlino:export"},
                  {"name": "merlino:test=\"monitor-script\""}
                ],
                "Attribute": [
                  {
                    "type": "comment",
                    "value": "Test from monitor script",
                    "category": "Internal reference",
                    "comment": "Test"
                  }
                ]
              }
            }' 2>&1)
        
        http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
        event_data=$(echo "$response" | grep -v "HTTP_CODE:")
        
        if [[ "$http_code" == "200" ]]; then
            event_id=$(echo "$event_data" | grep -oP '"id"\s*:\s*"\K[^"]+' | head -1)
            event_uuid=$(echo "$event_data" | grep -oP '"uuid"\s*:\s*"\K[^"]+' | head -1)
            echo -e "${COLOR_GREEN}✅ SUCCESSO!${COLOR_RESET}"
            echo -e "${COLOR_GREEN}   Event ID: $event_id${COLOR_RESET}"
            echo -e "${COLOR_GREEN}   UUID: $event_uuid${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}❌ ERRORE! HTTP $http_code${COLOR_RESET}"
            echo ""
            echo "$event_data"
        fi
        echo ""
        ;;
    
    *)
        echo -e "${COLOR_RED}Scelta non valida${COLOR_RESET}"
        exit 1
        ;;
esac

echo -e "${COLOR_CYAN}════════════════════════════════════════════════════════════════════════════${COLOR_RESET}"
