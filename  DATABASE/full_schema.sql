-- =====================================================
-- Banco de Dados: doacoes_db
-- Plataforma Doa+ - Conectando Doadores e ONGs
-- =====================================================

-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS doacoes_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE doacoes_db;

-- =====================================================
-- TABELAS PRINCIPAIS
-- =====================================================

-- Tabela de ONGs
CREATE TABLE IF NOT EXISTS ongs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(15),
    endereco TEXT,
    cidade VARCHAR(50),
    uf CHAR(2),
    descricao TEXT,
    logo_url VARCHAR(255),
    status ENUM('ativo', 'inativo', 'pendente') DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_cidade (cidade),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Doadores
CREATE TABLE IF NOT EXISTS doadores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(15),
    cpf VARCHAR(14) UNIQUE,
    data_nascimento DATE,
    endereco TEXT,
    cidade VARCHAR(50),
    uf CHAR(2),
    status ENUM('ativo', 'inativo') DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Necessidades
CREATE TABLE IF NOT EXISTS necessidades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ong_id INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(50) NOT NULL,
    quantidade_necessaria INT NOT NULL,
    quantidade_recebida INT DEFAULT 0,
    urgencia ENUM('baixa', 'media', 'alta') DEFAULT 'media',
    data_limite DATE,
    status ENUM('aberta', 'encerrada') DEFAULT 'aberta',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id),
    INDEX idx_categoria (categoria),
    INDEX idx_status (status),
    INDEX idx_urgencia (urgencia)
) ENGINE=InnoDB;

-- Tabela de Doações
CREATE TABLE IF NOT EXISTS doacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    doador_id INT NOT NULL,
    necessidade_id INT NOT NULL,
    quantidade INT NOT NULL,
    mensagem TEXT,
    status ENUM('pendente', 'confirmada', 'cancelada') DEFAULT 'pendente',
    data_doacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP NULL,
    FOREIGN KEY (doador_id) REFERENCES doadores(id) ON DELETE CASCADE,
    FOREIGN KEY (necessidade_id) REFERENCES necessidades(id) ON DELETE CASCADE,
    INDEX idx_doador (doador_id),
    INDEX idx_necessidade (necessidade_id),
    INDEX idx_status (status),
    INDEX idx_data (data_doacao)
) ENGINE=InnoDB;

-- Tabela de Avaliações
CREATE TABLE IF NOT EXISTS avaliacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    doador_id INT NOT NULL,
    ong_id INT NOT NULL,
    nota INT CHECK (nota >= 1 AND nota <= 5),
    comentario TEXT,
    data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doador_id) REFERENCES doadores(id) ON DELETE CASCADE,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    UNIQUE KEY unique_avaliacao (doador_id, ong_id),
    INDEX idx_ong (ong_id)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE SEGURANÇA E AUDITORIA
-- =====================================================

-- Tabela de Logs de Segurança
CREATE TABLE IF NOT EXISTS logs_seguranca (
    id INT PRIMARY KEY AUTO_INCREMENT,
    evento VARCHAR(100) NOT NULL,
    usuario_id INT,
    usuario_tipo ENUM('ong', 'doador', 'admin') NULL,
    ip VARCHAR(45),
    user_agent TEXT,
    detalhes JSON,
    gravidade ENUM('info', 'alerta', 'critico') DEFAULT 'info',
    data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_evento (evento),
    INDEX idx_usuario (usuario_id),
    INDEX idx_gravidade (gravidade),
    INDEX idx_data (data_evento)
) ENGINE=InnoDB;

-- Tabela de Tentativas de Login
CREATE TABLE IF NOT EXISTS tentativas_login (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100),
    ip VARCHAR(45),
    sucesso BOOLEAN DEFAULT FALSE,
    motivo VARCHAR(255),
    data_tentativa TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ip (ip),
    INDEX idx_email (email),
    INDEX idx_data (data_tentativa)
) ENGINE=InnoDB;

-- Tabela de Tokens JWT (Blacklist)
CREATE TABLE IF NOT EXISTS tokens_revogados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    jti VARCHAR(100) NOT NULL,
    usuario_id INT,
    data_revogacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_jti (jti)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE NOTIFICAÇÕES
-- =====================================================

CREATE TABLE IF NOT EXISTS notificacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    usuario_tipo ENUM('ong', 'doador') NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    lida BOOLEAN DEFAULT FALSE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuario (usuario_id, usuario_tipo),
    INDEX idx_lida (lida)
) ENGINE=InnoDB;

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices compostos para buscas frequentes
CREATE INDEX idx_necessidades_busca ON necessidades(categoria, status, urgencia);
CREATE INDEX idx_doacoes_status_data ON doacoes(status, data_doacao);
CREATE INDEX idx_ongs_localizacao ON ongs(cidade, uf, status);

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger para atualizar quantidade_recebida ao confirmar doação
DELIMITER //
CREATE TRIGGER after_doacao_confirmada
AFTER UPDATE ON doacoes
FOR EACH ROW
BEGIN
    IF NEW.status = 'confirmada' AND OLD.status != 'confirmada' THEN
        UPDATE necessidades 
        SET quantidade_recebida = quantidade_recebida + NEW.quantidade
        WHERE id = NEW.necessidade_id;
        
        -- Verificar se necessidade foi totalmente atendida
        UPDATE necessidades n
        SET status = 'encerrada'
        WHERE n.id = NEW.necessidade_id 
        AND n.quantidade_recebida >= n.quantidade_necessaria;
    END IF;
END//
DELIMITER ;

-- =====================================================
-- DADOS INICIAIS (SEED)
-- =====================================================

-- Inserir algumas categorias padrão (opcional)
INSERT INTO necessidades (id, titulo, descricao, categoria, quantidade_necessaria) VALUES
(1, 'Cesta Básica', 'Alimentos não perecíveis para famílias em situação de vulnerabilidade', 'alimentos', 100),
(2, 'Agasalhos', 'Roupas de frio em bom estado para crianças e adultos', 'roupas', 50),
(3, 'Medicamentos', 'Medicamentos básicos para atendimento na comunidade', 'medicamentos', 30)
ON DUPLICATE KEY UPDATE id=id;

-- =====================================================
-- FIM DO SCHEMA
-- =====================================================