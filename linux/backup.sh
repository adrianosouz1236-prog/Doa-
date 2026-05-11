#!/bin/bash
# backup.sh - Script de backup com rotação

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configurações
BACKUP_DIR="/backups/doacoes"
DB_NAME="doacoes_db"
DB_USER="doacoes_user"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup...${NC}"

# Criar diretórios
mkdir -p $BACKUP_DIR/{database,uploads,logs,config}

# ==================== BACKUP DO BANCO DE DADOS ====================
echo -e "${YELLOW}Backup do banco de dados...${NC}"

mysqldump -u $DB_USER -p $DB_NAME 2>/dev/null | gzip > $BACKUP_DIR/database/backup_${DATE}.sql.gz

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup do banco de dados concluído${NC}"
else
    echo -e "${RED}❌ Erro no backup do banco de dados${NC}"
fi

# ==================== BACKUP DOS ARQUIVOS ====================
echo -e "${YELLOW}Backup dos arquivos...${NC}"

# Backup de uploads
if [ -d "/var/www/doacoes/uploads" ]; then
    tar -czf $BACKUP_DIR/uploads/uploads_${DATE}.tar.gz /var/www/doacoes/uploads/ 2>/dev/null
    echo -e "${GREEN}✅ Backup de uploads concluído${NC}"
fi

# Backup de configurações
if [ -d "/etc/nginx/sites-available" ]; then
    tar -czf $BACKUP_DIR/config/nginx_${DATE}.tar.gz /etc/nginx/sites-available/ 2>/dev/null
    echo -e "${GREEN}✅ Backup de configurações Nginx concluído${NC}"
fi

# ==================== BACKUP DOS LOGS ====================
echo -e "${YELLOW}Backup dos logs...${NC}"

if [ -d "/var/log/doacoes" ]; then
    tar -czf $BACKUP_DIR/logs/logs_${DATE}.tar.gz /var/log/doacoes/ 2>/dev/null
    echo -e "${GREEN}✅ Backup de logs concluído${NC}"
fi

# ==================== REMOVER BACKUPS ANTIGOS ====================
echo -e "${YELLOW}Removendo backups com mais de $RETENTION_DAYS dias...${NC}"

find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# ==================== VERIFICAR INTEGRIDADE ====================
echo -e "${YELLOW}Verificando integridade do backup...${NC}"

if [ -f "$BACKUP_DIR/database/backup_${DATE}.sql.gz" ]; then
    if gzip -t $BACKUP_DIR/database/backup_${DATE}.sql.gz 2>/dev/null; then
        echo -e "${GREEN}✅ Backup do banco de dados íntegro${NC}"
    else
        echo -e "${RED}❌ Backup do banco de dados CORROMPIDO!${NC}"
    fi
fi

# ==================== ESTATÍSTICAS ====================
BACKUP_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Backup concluído com sucesso!${NC}"
echo -e "Data: ${YELLOW}$(date '+%d/%m/%Y %H:%M:%S')${NC}"
echo -e "Tamanho total: ${YELLOW}$BACKUP_SIZE${NC}"
echo -e "Diretório: ${YELLOW}$BACKUP_DIR${NC}"
echo -e "${GREEN}========================================${NC}"