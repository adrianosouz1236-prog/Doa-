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
    status ENUM('ativo', 'inativo', 'pendente', 'bloqueado') DEFAULT 'ativo',
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
    status ENUM('ativo', 'inativo', 'bloqueado') DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Necessidades (Anúncios)
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
    INDEX idx_status (status)
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
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- =====================================================
-- NOVAS TABELAS PARA PERFIL DE ONG, EVENTOS E PARCERIAS
-- =====================================================

-- Tabela para fotos da ONG (galeria)
CREATE TABLE IF NOT EXISTS ong_fotos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ong_id INT NOT NULL,
    foto_url VARCHAR(255) NOT NULL,
    descricao VARCHAR(255),
    tipo ENUM('perfil', 'galeria') DEFAULT 'galeria',
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id)
) ENGINE=InnoDB;

-- Tabela para eventos das ONGs
CREATE TABLE IF NOT EXISTS ong_eventos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ong_id INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_evento DATETIME NOT NULL,
    local_evento VARCHAR(255),
    endereco TEXT,
    cidade VARCHAR(50),
    uf CHAR(2),
    imagem_url VARCHAR(255),
    status ENUM('ativo', 'concluido', 'cancelado') DEFAULT 'ativo',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id),
    INDEX idx_data (data_evento),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela para parcerias das ONGs
CREATE TABLE IF NOT EXISTS ong_parcerias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ong_id INT NOT NULL,
    parceiro_nome VARCHAR(100) NOT NULL,
    tipo_parceria VARCHAR(50),
    descricao TEXT,
    logo_url VARCHAR(255),
    website_url VARCHAR(255),
    data_inicio DATE,
    status ENUM('ativa', 'encerrada') DEFAULT 'ativa',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
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
    INDEX idx_gravidade (gravidade)
) ENGINE=InnoDB;

-- Tabela de Advertências
CREATE TABLE IF NOT EXISTS advertencias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    anuncio_id INT NOT NULL,
    ong_id INT NOT NULL,
    motivo VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_advertencia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id),
    INDEX idx_anuncio (anuncio_id)
) ENGINE=InnoDB;

-- =====================================================
-- DADOS INICIAIS (SEED)
-- =====================================================

-- Inserir ONG de exemplo
INSERT INTO ongs (id, nome, cnpj, email, senha, telefone, endereco, cidade, uf, descricao, logo_url, status) VALUES
(1, 'ONG Solidária Brasil', '12.345.678/0001-90', 'ong@solidaria.org', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '(11) 99999-9999', 'Rua da Solidariedade, 100', 'São Paulo', 'SP', 'ONG dedicada a ajudar pessoas em situação de vulnerabilidade social.', 'https://via.placeholder.com/150?text=Logo+ONG', 'ativo');

-- Inserir Doador de exemplo
INSERT INTO doadores (id, nome, email, senha, telefone, status) VALUES
(1, 'João Silva', 'joao@email.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '(11) 98888-7777', 'ativo');

-- Inserir Necessidade/Anúncio de exemplo
INSERT INTO necessidades (id, ong_id, titulo, descricao, categoria, quantidade_necessaria, quantidade_recebida, urgencia, status) VALUES
(1, 1, 'Arrecadação de Alimentos', 'Precisamos de alimentos não perecíveis para distribuir para 100 famílias carentes.', 'alimentos', 500, 150, 'alta', 'aberta');

-- Inserir Evento de exemplo
INSERT INTO ong_eventos (id, ong_id, titulo, descricao, data_evento, local_evento, endereco, cidade, uf, status) VALUES
(1, 1, 'Dia da Solidariedade', 'Venha participar do nosso evento de arrecadação de alimentos e roupas. Teremos música, comida e muito amor ao próximo!', '2024-12-15 10:00:00', 'Parque da Cidade', 'Av. Principal, 500', 'São Paulo', 'SP', 'ativo');

-- Inserir Parceria de exemplo
INSERT INTO ong_parcerias (id, ong_id, parceiro_nome, tipo_parceria, descricao, website_url, status) VALUES
(1, 1, 'Mercado Popular', 'empresa', 'Parceiro na arrecadação de alimentos mensalmente.', 'https://mercadopopular.com.br', 'ativa');

-- Inserir Foto de exemplo
INSERT INTO ong_fotos (id, ong_id, foto_url, descricao, tipo) VALUES
(1, 1, 'https://via.placeholder.com/400x300?text=Evento+ONG', 'Evento de arrecadação - 2023', 'galeria'),
(2, 1, 'https://via.placeholder.com/400x300?text=Equipe+ONG', 'Nossa equipe de voluntários', 'galeria');

-- =====================================================
-- FIM DO SCHEMA
-- =====================================================