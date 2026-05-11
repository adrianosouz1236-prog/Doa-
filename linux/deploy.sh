#!/bin/bash
# deploy.sh - Script de deploy automatizado

set -e  # Para o script em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Plataforma Doa+ - Deploy Automático   ${NC}"
echo -e "${BLUE}========================================${NC}"

# ==================== CONFIGURAÇÕES ====================
PROJECT_DIR="/var/www/doacoes"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/var/log/doacoes"
BACKUP_DIR="/backups/doacoes"
DB_NAME="doacoes_db"
DB_USER="doacoes_user"
APP_USER="www-data"

# ==================== FUNÇÕES ====================

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERRO]${NC} $1"
    exit 1
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        error "Não execute este script como root! Use um usuário normal com sudo."
    fi
}

check_dependencies() {
    log "Verificando dependências do sistema..."
    
    # Python3
    if ! command -v python3 &> /dev/null; then
        log "Instalando Python3..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    fi
    
    # MySQL
    if ! command -v mysql &> /dev/null; then
        log "Instalando MySQL..."
        sudo apt-get install -y mysql-server
        sudo systemctl enable mysql
        sudo systemctl start mysql
    fi
    
    # Nginx
    if ! command -v nginx &> /dev/null; then
        log "Instalando Nginx..."
        sudo apt-get install -y nginx
    fi
    
    log "✅ Dependências verificadas"
}

setup_directories() {
    log "Criando diretórios do projeto..."
    
    sudo mkdir -p $PROJECT_DIR
    sudo mkdir -p $LOG_DIR
    sudo mkdir -p $BACKUP_DIR
    
    sudo chown -R $USER:$USER $PROJECT_DIR
    sudo chmod 755 $PROJECT_DIR
    
    log "✅ Diretórios criados"
}

setup_virtualenv() {
    log "Configurando ambiente virtual..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv $VENV_DIR
    fi
    
    source $VENV_DIR/bin/activate
    pip install --upgrade pip
    pip install -r $PROJECT_DIR/requirements.txt
    
    log "✅ Ambiente virtual configurado"
}

setup_database() {
    log "Configurando banco de dados..."
    
    # Criar banco de dados se não existir
    mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Importar schema
    mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < $PROJECT_DIR/database/schema/full_schema.sql
    
    log "✅ Banco de dados configurado"
}

configure_nginx() {
    log "Configurando Nginx..."
    
    sudo cp $PROJECT_DIR/linux/config/nginx/doacoes.conf /etc/nginx/sites-available/doacoes
    sudo ln -sf /etc/nginx/sites-available/doacoes /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    sudo nginx -t || error "Configuração do Nginx inválida"
    sudo systemctl restart nginx
    
    log "✅ Nginx configurado"
}

configure_systemd() {
    log "Configurando serviço systemd..."
    
    sudo cp $PROJECT_DIR/linux/config/systemd/doacoes.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable doacoes
    sudo systemctl restart doacoes
    
    log "✅ Serviço configurado"
}

configure_firewall() {
    log "Configurando firewall..."
    
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    
    log "✅ Firewall configurado"
}

configure_fail2ban() {
    log "Configurando fail2ban..."
    
    if ! command -v fail2ban-client &> /dev/null; then
        sudo apt-get install -y fail2ban
    fi
    
    sudo cp $PROJECT_DIR/linux/config/fail2ban/jail.local /etc/fail2ban/
    sudo cp $PROJECT_DIR/linux/config/fail2ban/filter.d/doacoes.conf /etc/fail2ban/filter.d/
    
    sudo systemctl restart fail2ban
    
    log "✅ Fail2ban configurado"
}

setup_logrotate() {
    log "Configurando rotação de logs..."
    
    sudo cp $PROJECT_DIR/linux/config/logrotate/doacoes /etc/logrotate.d/
    sudo chmod 644 /etc/logrotate.d/doacoes
    
    log "✅ Rotação de logs configurada"
}

setup_backup() {
    log "Configurando backup automático..."
    
    # Adicionar cron job para backup diário
    (crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/linux/scripts/backup.sh") | crontab -
    
    log "✅ Backup configurado"
}

health_check() {
    log "Realizando health check..."
    
    sleep 5
    
    # Verificar se a aplicação está rodando
    if curl -f http://localhost:5000/health &> /dev/null; then
        log "✅ Aplicação está rodando"
    else
        error "Aplicação não respondeu ao health check"
    fi
    
    # Verificar Nginx
    if curl -f http://localhost &> /dev/null; then
        log "✅ Nginx está funcionando"
    else
        error "Nginx não está respondendo"
    fi
}

show_summary() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${GREEN}🎉 DEPLOY CONCLUÍDO COM SUCESSO! 🎉${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Acesse a aplicação: ${GREEN}http://$(hostname -I | awk '{print $1}')${NC}"
    echo -e "Logs da aplicação: ${YELLOW}$LOG_DIR/app.log${NC}"
    echo -e "Logs de segurança: ${YELLOW}$LOG_DIR/security.log${NC}"
    echo -e "Backups: ${YELLOW}$BACKUP_DIR${NC}"
    echo -e "\nComandos úteis:"
    echo -e "  sudo systemctl status doacoes  # Verificar status da aplicação"
    echo -e "  sudo tail -f $LOG_DIR/app.log  # Acompanhar logs"
    echo -e "  $PROJECT_DIR/linux/scripts/backup.sh  # Executar backup manual"
    echo -e "${BLUE}========================================${NC}"
}

# ==================== MAIN ====================

main() {
    check_root
    check_dependencies
    setup_directories
    setup_virtualenv
    setup_database
    configure_nginx
    configure_systemd
    configure_firewall
    configure_fail2ban
    setup_logrotate
    setup_backup
    health_check
    show_summary
}

# Executar main
main