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
    total_advertencias INT DEFAULT 0,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    endereco_completo VARCHAR(255),
    media_avaliacao DECIMAL(3, 2) DEFAULT 0,
    total_avaliacoes INT DEFAULT 0,
    conta_bancaria TEXT,
    email_confirmado BOOLEAN DEFAULT FALSE,
    consentimento_lgpd BOOLEAN DEFAULT FALSE,
    data_consentimento TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_cidade (cidade),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Doadores (ATUALIZADA)
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
    total_doacoes INT DEFAULT 0,
    pontuacao INT DEFAULT 0,
    conquistas JSON,
    email_confirmado BOOLEAN DEFAULT FALSE,
    consentimento_lgpd BOOLEAN DEFAULT FALSE,
    data_consentimento TIMESTAMP NULL,
    total_itens INT DEFAULT 0,
    twofa_secret VARCHAR(255),
    twofa_ativado BOOLEAN DEFAULT FALSE,
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
    status ENUM('aberta', 'encerrada', 'excluido') DEFAULT 'aberta',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id),
    INDEX idx_categoria (categoria),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Doações (Itens)
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

-- Tabela de Doações Financeiras
CREATE TABLE IF NOT EXISTS doacoes_financeiras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transacao_id VARCHAR(50) UNIQUE NOT NULL,
    doador_id INT NOT NULL,
    ong_id INT NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    valor_liquido DECIMAL(10, 2) NOT NULL,
    taxa_servico DECIMAL(10, 2) DEFAULT 0,
    mensagem TEXT,
    metodo_pagamento ENUM('cartao', 'pix', 'boleto') DEFAULT 'cartao',
    recorrente BOOLEAN DEFAULT FALSE,
    status ENUM('pendente', 'confirmado', 'cancelado') DEFAULT 'pendente',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP NULL,
    FOREIGN KEY (doador_id) REFERENCES doadores(id) ON DELETE CASCADE,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_transacao (transacao_id),
    INDEX idx_doador (doador_id),
    INDEX idx_ong (ong_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Carteiras
CREATE TABLE IF NOT EXISTS carteiras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ong_id INT NOT NULL UNIQUE,
    saldo DECIMAL(10, 2) DEFAULT 0,
    total_recebido DECIMAL(10, 2) DEFAULT 0,
    total_sacado DECIMAL(10, 2) DEFAULT 0,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id)
) ENGINE=InnoDB;

-- Tabela de Transações
CREATE TABLE IF NOT EXISTS transacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transacao_id VARCHAR(50) UNIQUE NOT NULL,
    doador_id INT NULL,
    ong_id INT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    tipo ENUM('doacao_financeira', 'saque', 'estorno') NOT NULL,
    status ENUM('pendente', 'confirmado', 'cancelado', 'processando') DEFAULT 'pendente',
    metodo VARCHAR(20),
    conta_bancaria TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_processamento TIMESTAMP NULL,
    FOREIGN KEY (doador_id) REFERENCES doadores(id) ON DELETE SET NULL,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE SET NULL,
    INDEX idx_transacao (transacao_id),
    INDEX idx_ong (ong_id),
    INDEX idx_doador (doador_id)
) ENGINE=InnoDB;

-- Tabela de Pagamentos
CREATE TABLE IF NOT EXISTS pagamentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transacao_id INT NOT NULL,
    doacao_financeira_id INT NOT NULL,
    status ENUM('aprovado', 'recusado', 'pendente') DEFAULT 'pendente',
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    codigo_autorizacao VARCHAR(50),
    FOREIGN KEY (transacao_id) REFERENCES transacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (doacao_financeira_id) REFERENCES doacoes_financeiras(id) ON DELETE CASCADE,
    INDEX idx_transacao (transacao_id)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE PERFIL E INTERAÇÕES
-- =====================================================

-- Tabela de Fotos da ONG
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

-- Tabela de Eventos
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

-- Tabela de Parcerias
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

-- Tabela de Avaliações
CREATE TABLE IF NOT EXISTS avaliacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ong_id INT NOT NULL,
    doador_id INT NOT NULL,
    doador_nome VARCHAR(100),
    nota INT NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    FOREIGN KEY (doador_id) REFERENCES doadores(id) ON DELETE CASCADE,
    UNIQUE KEY unique_avaliacao (ong_id, doador_id),
    INDEX idx_ong (ong_id),
    INDEX idx_doador (doador_id)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE VOLUNTARIADO
-- =====================================================

-- Tabela de Vagas de Voluntariado
CREATE TABLE IF NOT EXISTS voluntariado_vagas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ong_id INT NOT NULL,
    ong_nome VARCHAR(100),
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_evento DATETIME,
    local VARCHAR(255),
    vagas_disponiveis INT DEFAULT 1,
    vagas_preenchidas INT DEFAULT 0,
    habilidades TEXT,
    status ENUM('aberta', 'completa', 'cancelada') DEFAULT 'aberta',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Inscrições Voluntariado
CREATE TABLE IF NOT EXISTS voluntariado_inscricoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vaga_id INT NOT NULL,
    doador_id INT NOT NULL,
    doador_nome VARCHAR(100),
    data_inscricao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('confirmada', 'cancelada') DEFAULT 'confirmada',
    FOREIGN KEY (vaga_id) REFERENCES voluntariado_vagas(id) ON DELETE CASCADE,
    FOREIGN KEY (doador_id) REFERENCES doadores(id) ON DELETE CASCADE,
    UNIQUE KEY unique_inscricao (vaga_id, doador_id),
    INDEX idx_vaga (vaga_id),
    INDEX idx_doador (doador_id)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE FEEDBACK E SUPORTE
-- =====================================================

-- Tabela de Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    user_type ENUM('ong', 'doador') NOT NULL,
    user_email VARCHAR(100),
    user_nome VARCHAR(100),
    mensagem TEXT NOT NULL,
    tipo VARCHAR(50) DEFAULT 'geral',
    anonimo BOOLEAN DEFAULT FALSE,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pendente', 'respondido') DEFAULT 'pendente',
    resposta TEXT,
    data_resposta TIMESTAMP NULL,
    INDEX idx_user (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Tabela de Suporte
CREATE TABLE IF NOT EXISTS suporte (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    user_type ENUM('ong', 'doador') NOT NULL,
    user_email VARCHAR(100),
    user_nome VARCHAR(100),
    assunto VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    categoria VARCHAR(50) DEFAULT 'duvida',
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('aberto', 'em_andamento', 'resolvido', 'fechado') DEFAULT 'aberto',
    resposta TEXT,
    data_resposta TIMESTAMP NULL,
    responsavel VARCHAR(100),
    INDEX idx_user (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE COMUNICAÇÃO E NOTIFICAÇÕES
-- =====================================================

-- Tabela de Comunicações
CREATE TABLE IF NOT EXISTS comunicacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_email VARCHAR(100) NOT NULL,
    tipo ENUM('todos', 'doadores', 'ongs', 'especifico') NOT NULL,
    destinatario_id INT NULL,
    destinatario_tipo ENUM('doador', 'ong') NULL,
    destinatario_nome VARCHAR(100),
    titulo VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    prioridade ENUM('normal', 'alta', 'urgente') DEFAULT 'normal',
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lida BOOLEAN DEFAULT FALSE,
    data_leitura TIMESTAMP NULL,
    INDEX idx_tipo (tipo),
    INDEX idx_destinatario (destinatario_id)
) ENGINE=InnoDB;

-- Tabela de Notificações
CREATE TABLE IF NOT EXISTS notificacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_email VARCHAR(100) NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    tipo ENUM('informativo', 'alerta', 'promocional', 'urgente') DEFAULT 'informativo',
    destino ENUM('todos', 'doadores', 'ongs') DEFAULT 'todos',
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enviado BOOLEAN DEFAULT FALSE,
    INDEX idx_destino (destino)
) ENGINE=InnoDB;

-- Tabela de Preferências de Notificação
CREATE TABLE IF NOT EXISTS notificacoes_preferencias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    user_type ENUM('ong', 'doador') NOT NULL,
    email_doacoes BOOLEAN DEFAULT TRUE,
    email_novas_necessidades BOOLEAN DEFAULT TRUE,
    email_eventos BOOLEAN DEFAULT TRUE,
    email_newsletter BOOLEAN DEFAULT FALSE,
    push_doacoes BOOLEAN DEFAULT TRUE,
    push_novas_necessidades BOOLEAN DEFAULT TRUE,
    push_eventos BOOLEAN DEFAULT TRUE,
    push_mensagens BOOLEAN DEFAULT TRUE,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user (user_id, user_type),
    INDEX idx_user (user_id)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE CHAT
-- =====================================================

-- Tabela de Mensagens do Chat
CREATE TABLE IF NOT EXISTS chat_mensagens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    remetente_id INT NOT NULL,
    remetente_tipo ENUM('ong', 'doador') NOT NULL,
    destinatario_id INT NOT NULL,
    destinatario_tipo ENUM('ong', 'doador') NOT NULL,
    mensagem TEXT NOT NULL,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lida BOOLEAN DEFAULT FALSE,
    INDEX idx_remetente (remetente_id),
    INDEX idx_destinatario (destinatario_id)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE SEGURANÇA
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
    gravidade ENUM('info', 'alerta', 'media', 'critico') DEFAULT 'info',
    data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_evento (evento),
    INDEX idx_usuario (usuario_id),
    INDEX idx_gravidade (gravidade)
) ENGINE=InnoDB;

-- Tabela de Tentativas de Login
CREATE TABLE IF NOT EXISTS tentativas_login (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100),
    ip VARCHAR(45),
    sucesso BOOLEAN DEFAULT FALSE,
    data_tentativa TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ip (ip),
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- Tabela de Advertências
CREATE TABLE IF NOT EXISTS advertencias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    anuncio_id INT NOT NULL,
    ong_id INT NOT NULL,
    motivo VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_advertencia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin VARCHAR(100),
    FOREIGN KEY (ong_id) REFERENCES ongs(id) ON DELETE CASCADE,
    INDEX idx_ong (ong_id),
    INDEX idx_anuncio (anuncio_id)
) ENGINE=InnoDB;

-- Tabela de Solicitações de Exclusão
CREATE TABLE IF NOT EXISTS solicitacoes_exclusao (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    usuario_nome VARCHAR(100),
    usuario_email VARCHAR(100) NOT NULL,
    usuario_tipo ENUM('ong', 'doador') NOT NULL,
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pendente', 'confirmado', 'cancelado') DEFAULT 'pendente',
    data_confirmacao TIMESTAMP NULL,
    data_cancelamento TIMESTAMP NULL,
    admin VARCHAR(100),
    INDEX idx_usuario (usuario_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- =====================================================
-- TABELAS DE RELATÓRIOS
-- =====================================================

-- Tabela de Relatórios Anuais
CREATE TABLE IF NOT EXISTS relatorios_anuais (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    usuario_type ENUM('ong', 'doador') NOT NULL,
    usuario_email VARCHAR(100),
    ano INT NOT NULL,
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    caminho VARCHAR(255),
    status ENUM('gerado', 'pendente', 'erro') DEFAULT 'gerado',
    INDEX idx_usuario (usuario_id),
    INDEX idx_ano (ano)
) ENGINE=InnoDB;

-- =====================================================
-- DADOS INICIAIS (SEED)
-- =====================================================

-- Inserir ONG de exemplo
INSERT INTO ongs (id, nome, cnpj, email, senha, telefone, endereco, cidade, uf, descricao, logo_url, status, email_confirmado, consentimento_lgpd, data_consentimento) VALUES
(1, 'ONG Solidária Brasil', '12.345.678/0001-90', 'ong@solidaria.org', '$2b$12$3zXkPfVHlhBxXlJ6bqTTmO4gBt9aFwR3zKQ8uE5vN2wP1yY7zL8zW', '(11) 99999-9999', 'Rua da Solidariedade, 100', 'São Paulo', 'SP', 'ONG dedicada a ajudar pessoas em situação de vulnerabilidade social.', 'https://via.placeholder.com/150?text=Logo+ONG', 'ativo', TRUE, TRUE, NOW());

-- Inserir Doador de exemplo
INSERT INTO doadores (id, nome, email, senha, telefone, status, email_confirmado, consentimento_lgpd, data_consentimento) VALUES
(1, 'João Silva', 'joao@email.com', '$2b$10$e0Q8Z9wR5tU7vN2wP1yY7zL8zW3zXkPfVHlhBxXlJ6bqTTmO4gBt9aF', '(11) 98888-7777', 'ativo', TRUE, TRUE, NOW());

-- Inserir Necessidade
INSERT INTO necessidades (id, ong_id, titulo, descricao, categoria, quantidade_necessaria, quantidade_recebida, urgencia, status) VALUES
(1, 1, 'Arrecadação de Alimentos', 'Precisamos de alimentos não perecíveis para distribuir para 100 famílias carentes.', 'alimentos', 500, 150, 'alta', 'aberta');

-- Inserir Evento
INSERT INTO ong_eventos (id, ong_id, titulo, descricao, data_evento, local_evento, endereco, cidade, uf, status) VALUES
(1, 1, 'Dia da Solidariedade', 'Venha participar do nosso evento de arrecadação de alimentos e roupas. Teremos música, comida e muito amor ao próximo!', '2024-12-15 10:00:00', 'Parque da Cidade', 'Av. Principal, 500', 'São Paulo', 'SP', 'ativo');

-- Inserir Parceria
INSERT INTO ong_parcerias (id, ong_id, parceiro_nome, tipo_parceria, descricao, website_url, status) VALUES
(1, 1, 'Mercado Popular', 'empresa', 'Parceiro na arrecadação de alimentos mensalmente.', 'https://mercadopopular.com.br', 'ativa');

-- Inserir Fotos
INSERT INTO ong_fotos (id, ong_id, foto_url, descricao, tipo) VALUES
(1, 1, 'https://via.placeholder.com/400x300?text=Evento+ONG', 'Evento de arrecadação - 2023', 'galeria'),
(2, 1, 'https://via.placeholder.com/400x300?text=Equipe+ONG', 'Nossa equipe de voluntários', 'galeria');

-- Inserir Preferências de Notificação
INSERT INTO notificacoes_preferencias (user_id, user_type) VALUES
(1, 'doador');

-- =====================================================
-- FIM DO SCHEMA
-- =====================================================