#!/bin/bash
# monitor.sh - Script de monitoramento do sistema

# Cores
VERMELHO='\033[0;31m'
VERDE='\033[0;32m'
AMARELO='\033[1;33m'
AZUL='\033[0;34m'
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
        echo -e "${VERMELHO}⚠️  CPU: ${CPU_USAGE}% (ALERTA)${NC}"
    else
        echo -e "${VERDE}✅ CPU: ${CPU_USAGE}%${NC}"
    fi
}

# Verificar memória
check_memory() {
    MEM_TOTAL=$(free | grep Mem | awk '{print $2}')
    MEM_USED=$(free | grep Mem | awk '{print $3}')
    MEM_USAGE=$(echo "scale=2; $MEM_USED * 100 / $MEM_TOTAL" | bc)
    
    if (( $(echo "$MEM_USAGE > $THRESHOLD_MEM" | bc -l) )); then
        send_alert "Alerta de Memória - Doa+" "Memória está em ${MEM_USAGE}% (limite: ${THRESHOLD_MEM}%)"
        echo -e "${VERMELHO}⚠️  Memória: ${MEM_USAGE}% (ALERTA)${NC}"
    else
        echo -e "${VERDE}✅ Memória: ${MEM_USAGE}%${NC}"
    fi
}

# Verificar disco
check_disk() {
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $DISK_USAGE -gt $THRESHOLD_DISK ]; then
        send_alert "Alerta de Disco - Doa+" "Disco está em ${DISK_USAGE}% (limite: ${THRESHOLD_DISK}%)"
        echo -e "${VERMELHO}⚠️  Disco: ${DISK_USAGE}% (ALERTA)${NC}"
    else
        echo -e "${VERDE}✅ Disco: ${DISK_USAGE}%${NC}"
    fi
}

# Verificar conexões ativas
check_connections() {
    CONNECTIONS=$(netstat -an | grep :80 | wc -l)
    CONNECTIONS=$((CONNECTIONS))
    
    if [ $CONNECTIONS -gt 500 ]; then
        send_alert "Muitas conexões - Doa+" "Conexões ativas: $CONNECTIONS"
        echo -e "${VERMELHO}⚠️  Conexões: $CONNECTIONS (ALERTA)${NC}"
    else
        echo -e "${VERDE}✅ Conexões: $CONNECTIONS${NC}"
    fi
}

# Verificar status da aplicação
check_app_status() {
    if curl -f http://localhost:5000/health &> /dev/null; then
        echo -e "${VERDE}✅ Aplicação: ONLINE${NC}"
    else
        send_alert "Aplicação OFFLINE - Doa+" "A aplicação não está respondendo ao health check"
        echo -e "${VERDE}❌ Aplicação: OFFLINE${NC}"
    fi
}

# Verificar serviços
check_services() {
    local services=("nginx" "mysql" "doacoes")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            echo -e "${VERMELHO}✅ $service: ativo${NC}"
        else
            echo -e "${VERMELHO}❌ $service: inativo${NC}"
            send_alert "Serviço $service parado" "O serviço $service não está rodando"
        fi
    done
}

# Verificar logs de erro recentes
check_error_logs() {
    local errors=$(grep -c "ERROR" /var/log/doacoes/app.log 2>/dev/null || echo "0")
    
    if [ $errors -gt 50 ]; then
        echo -e "${VERMELHO}⚠️  Erros no log: $errors nas últimas 24h${NC}"
    else
        echo -e "${VERDE}✅ Erros no log: $errors${NC}"
    fi
}

# Exibir resumo
show_summary() {
    echo -e "\n${AZUL}========================================${NC}"
    echo -e "${AZUL}   Monitoramento - Doa+${NC}"
    echo -e "${AZUL}   $(date '+%d/%m/%Y %H:%M:%S')${NC}"
    echo -e "${AZUL}========================================${NC}"
    
    check_cpu
    check_memory
    check_disk
    check_connections
    check_app_status
    echo ""
    check_services
    echo ""
    check_error_logs
    
    echo -e "${AZUL}========================================${NC}"
}

# Main
main() {
    show_summary
    log "Monitoramento executado"
}

# Executar
main