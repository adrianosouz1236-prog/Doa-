#!/bin/bash
# monitor.sh - Script de monitoramento do sistema

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
LOG_FILE="/var/log/doacoes/monitor.log"
ALERT_EMAIL="admin@doacoes.org"
THRESHOLD_CPU=80
THRESHOLD_MEM=85
THRESHOLD_DISK=85

# Função para log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# Função para enviar alerta
send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" $ALERT_EMAIL
    log "ALERTA: $subject"
}

# Verificar CPU
check_cpu() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    CPU_USAGE=${CPU_USAGE:-0}
    
    if (( $(echo "$CPU_USAGE > $THRESHOLD_CPU" | bc -l) )); then
        send_alert "Alerta de CPU - Doa+" "CPU está em ${CPU_USAGE}% (limite: ${THRESHOLD_CPU}%)"
        echo -e "${RED}⚠️  CPU: ${CPU_USAGE}% (ALERTA)${NC}"
    else
        echo -e "${GREEN}✅ CPU: ${CPU_USAGE}%${NC}"
    fi
}

# Verificar memória
check_memory() {
    MEM_TOTAL=$(free | grep Mem | awk '{print $2}')
    MEM_USED=$(free | grep Mem | awk '{print $3}')
    MEM_USAGE=$(echo "scale=2; $MEM_USED * 100 / $MEM_TOTAL" | bc)
    
    if (( $(echo "$MEM_USAGE > $THRESHOLD_MEM" | bc -l) )); then
        send_alert "Alerta de Memória - Doa+" "Memória está em ${MEM_USAGE}% (limite: ${THRESHOLD_MEM}%)"
        echo -e "${RED}⚠️  Memória: ${MEM_USAGE}% (ALERTA)${NC}"
    else
        echo -e "${GREEN}✅ Memória: ${MEM_USAGE}%${NC}"
    fi
}

# Verificar disco
check_disk() {
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $DISK_USAGE -gt $THRESHOLD_DISK ]; then
        send_alert "Alerta de Disco - Doa+" "Disco está em ${DISK_USAGE}% (limite: ${THRESHOLD_DISK}%)"
        echo -e "${RED}⚠️  Disco: ${DISK_USAGE}% (ALERTA)${NC}"
    else
        echo -e "${GREEN}✅ Disco: ${DISK_USAGE}%${NC}"
    fi
}

# Verificar conexões ativas
check_connections() {
    CONNECTIONS=$(netstat -an | grep :80 | wc -l)
    CONNECTIONS=$((CONNECTIONS))
    
    if [ $CONNECTIONS -gt 500 ]; then
        send_alert "Muitas conexões - Doa+" "Conexões ativas: $CONNECTIONS"
        echo -e "${RED}⚠️  Conexões: $CONNECTIONS (ALERTA)${NC}"
    else
        echo -e "${GREEN}✅ Conexões: $CONNECTIONS${NC}"
    fi
}

# Verificar status da aplicação
check_app_status() {
    if curl -f http://localhost:5000/health &> /dev/null; then
        echo -e "${GREEN}✅ Aplicação: ONLINE${NC}"
    else
        send_alert "Aplicação OFFLINE - Doa+" "A aplicação não está respondendo ao health check"
        echo -e "${RED}❌ Aplicação: OFFLINE${NC}"
    fi
}

# Verificar serviços
check_services() {
    local services=("nginx" "mysql" "doacoes")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            echo -e "${GREEN}✅ $service: ativo${NC}"
        else
            echo -e "${RED}❌ $service: inativo${NC}"
            send_alert "Serviço $service parado" "O serviço $service não está rodando"
        fi
    done
}

# Verificar logs de erro recentes
check_error_logs() {
    local errors=$(grep -c "ERROR" /var/log/doacoes/app.log 2>/dev/null || echo "0")
    
    if [ $errors -gt 50 ]; then
        echo -e "${RED}⚠️  Erros no log: $errors nas últimas 24h${NC}"
    else
        echo -e "${GREEN}✅ Erros no log: $errors${NC}"
    fi
}

# Exibir resumo
show_summary() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}   Monitoramento - Doa+${NC}"
    echo -e "${BLUE}   $(date '+%d/%m/%Y %H:%M:%S')${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    check_cpu
    check_memory
    check_disk
    check_connections
    check_app_status
    echo ""
    check_services
    echo ""
    check_error_logs
    
    echo -e "${BLUE}========================================${NC}"
}

# Main
main() {
    show_summary
    log "Monitoramento executado"
}

# Executar
main