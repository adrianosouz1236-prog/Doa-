-- =====================================================================
-- DATABASE/full_schema.sql
-- Schema completo do banco de dados Doa+
-- ATENÇÃO: Este arquivo contém APENAS a estrutura (DDL).
-- Dados de teste são criados pelo script init_test_data() em Python,
-- que roda somente em ambiente de desenvolvimento.
-- =====================================================================

-- =====================================================================
-- TABELA: administradores
-- =====================================================================
CREATE TABLE IF NOT EXISTS administradores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) DEFAULT 'admin',
    status VARCHAR(50) DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_administradores_email ON administradores(email);

-- =====================================================================
-- TABELA: ongs
-- =====================================================================
CREATE TABLE IF NOT EXISTS ongs (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cnpj VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    endereco VARCHAR(500),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    descricao TEXT,
    logo_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pendente_verificacao',
    banco VARCHAR(100),
    agencia VARCHAR(20),
    conta VARCHAR(30),
    tipo_conta VARCHAR(20) DEFAULT 'corrente',
    conta_bancaria_criptografada TEXT,
    codigo_verificacao VARCHAR(20),
    motivo_rejeicao TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    endereco_completo VARCHAR(500),
    total_advertencias INTEGER DEFAULT 0,
    media_avaliacao DECIMAL(3, 2) DEFAULT 0,
    total_avaliacoes INTEGER DEFAULT 0,
    email_confirmado BOOLEAN DEFAULT FALSE,
    consentimento_lgpd BOOLEAN DEFAULT FALSE,
    ip_consentimento VARCHAR(50),
    user_agent_consentimento VARCHAR(500),
    data_consentimento TIMESTAMP,
    versao_termos VARCHAR(20) DEFAULT 'v1.0',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_verificacao TIMESTAMP,
    verificado_por INTEGER
);

CREATE INDEX IF NOT EXISTS idx_ongs_email ON ongs(email);
CREATE INDEX IF NOT EXISTS idx_ongs_cnpj ON ongs(cnpj);
CREATE INDEX IF NOT EXISTS idx_ongs_status ON ongs(status);
CREATE INDEX IF NOT EXISTS idx_ongs_cidade ON ongs(cidade);

-- =====================================================================
-- TABELA: doadores
-- =====================================================================
CREATE TABLE IF NOT EXISTS doadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    cpf VARCHAR(14),
    data_nascimento DATE,
    endereco VARCHAR(500),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    status VARCHAR(50) DEFAULT 'ativo',
    total_doacoes INTEGER DEFAULT 0,
    pontuacao INTEGER DEFAULT 0,
    conquistas TEXT[],
    total_itens INTEGER DEFAULT 0,
    twofa_secret VARCHAR(100),
    twofa_ativado BOOLEAN DEFAULT FALSE,
    email_confirmado BOOLEAN DEFAULT FALSE,
    consentimento_lgpd BOOLEAN DEFAULT FALSE,
    ip_consentimento VARCHAR(50),
    user_agent_consentimento VARCHAR(500),
    data_consentimento TIMESTAMP,
    versao_termos VARCHAR(20) DEFAULT 'v1.0',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_doadores_email ON doadores(email);
CREATE INDEX IF NOT EXISTS idx_doadores_status ON doadores(status);
CREATE INDEX IF NOT EXISTS idx_doadores_pontuacao ON doadores(pontuacao DESC);

-- =====================================================================
-- TABELA: necessidades
-- =====================================================================
CREATE TABLE IF NOT EXISTS necessidades (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(50) NOT NULL,
    quantidade_necessaria INTEGER NOT NULL,
    quantidade_recebida INTEGER DEFAULT 0,
    urgencia VARCHAR(20) DEFAULT 'media',
    status VARCHAR(50) DEFAULT 'aberta',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_necessidades_ong ON necessidades(ong_id);
CREATE INDEX IF NOT EXISTS idx_necessidades_status ON necessidades(status);
CREATE INDEX IF NOT EXISTS idx_necessidades_categoria ON necessidades(categoria);

-- =====================================================================
-- TABELA: doacoes
-- =====================================================================
CREATE TABLE IF NOT EXISTS doacoes (
    id SERIAL PRIMARY KEY,
    doador_id INTEGER NOT NULL REFERENCES doadores(id) ON DELETE CASCADE,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    necessidade_id INTEGER REFERENCES necessidades(id) ON DELETE SET NULL,
    quantidade INTEGER NOT NULL,
    mensagem TEXT,
    status VARCHAR(50) DEFAULT 'pendente',
    data_doacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_doacoes_doador ON doacoes(doador_id);
CREATE INDEX IF NOT EXISTS idx_doacoes_ong ON doacoes(ong_id);
CREATE INDEX IF NOT EXISTS idx_doacoes_status ON doacoes(status);

-- =====================================================================
-- TABELA: doacoes_financeiras
-- =====================================================================
CREATE TABLE IF NOT EXISTS doacoes_financeiras (
    id SERIAL PRIMARY KEY,
    doador_id INTEGER NOT NULL REFERENCES doadores(id) ON DELETE CASCADE,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    valor DECIMAL(10, 2) NOT NULL,
    taxa_servico DECIMAL(10, 2) DEFAULT 0,
    valor_liquido DECIMAL(10, 2) DEFAULT 0,
    mensagem TEXT,
    recorrente BOOLEAN DEFAULT FALSE,
    metodo_pagamento VARCHAR(50),
    external_reference VARCHAR(255) UNIQUE,
    mp_preference_id VARCHAR(255),
    mp_payment_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pendente',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_doacoes_fin_doador ON doacoes_financeiras(doador_id);
CREATE INDEX IF NOT EXISTS idx_doacoes_fin_ong ON doacoes_financeiras(ong_id);
CREATE INDEX IF NOT EXISTS idx_doacoes_fin_status ON doacoes_financeiras(status);
CREATE INDEX IF NOT EXISTS idx_doacoes_fin_external ON doacoes_financeiras(external_reference);

-- =====================================================================
-- TABELA: carteiras
-- =====================================================================
CREATE TABLE IF NOT EXISTS carteiras (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL UNIQUE REFERENCES ongs(id) ON DELETE CASCADE,
    saldo DECIMAL(10, 2) DEFAULT 0,
    total_recebido DECIMAL(10, 2) DEFAULT 0,
    total_sacado DECIMAL(10, 2) DEFAULT 0,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_carteiras_ong ON carteiras(ong_id);

-- =====================================================================
-- TABELA: logs_auditoria
-- =====================================================================
CREATE TABLE IF NOT EXISTS logs_auditoria (
    id SERIAL PRIMARY KEY,
    evento VARCHAR(100) NOT NULL,
    usuario_id INTEGER,
    usuario_tipo VARCHAR(50),
    ip VARCHAR(50),
    user_agent VARCHAR(500),
    detalhes JSONB,
    gravidade VARCHAR(20) DEFAULT 'info',
    data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_evento ON logs_auditoria(evento);
CREATE INDEX IF NOT EXISTS idx_logs_data ON logs_auditoria(data_evento DESC);
CREATE INDEX IF NOT EXISTS idx_logs_gravidade ON logs_auditoria(gravidade);

-- =====================================================================
-- TABELA: tentativas_login
-- =====================================================================
CREATE TABLE IF NOT EXISTS tentativas_login (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    ip VARCHAR(50),
    sucesso BOOLEAN DEFAULT FALSE,
    data_tentativa TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tentativas_ip ON tentativas_login(ip);
CREATE INDEX IF NOT EXISTS idx_tentativas_data ON tentativas_login(data_tentativa DESC);

-- =====================================================================
-- TABELA: ong_eventos
-- =====================================================================
CREATE TABLE IF NOT EXISTS ong_eventos (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    data_evento TIMESTAMP NOT NULL,
    local_evento VARCHAR(255),
    endereco VARCHAR(500),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    imagem_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'ativo',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eventos_ong ON ong_eventos(ong_id);
CREATE INDEX IF NOT EXISTS idx_eventos_data ON ong_eventos(data_evento);

-- =====================================================================
-- TABELA: ong_parcerias
-- =====================================================================
CREATE TABLE IF NOT EXISTS ong_parcerias (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    parceiro_nome VARCHAR(255) NOT NULL,
    tipo_parceria VARCHAR(50) DEFAULT 'empresa',
    descricao TEXT,
    logo_url VARCHAR(500),
    website_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'ativa',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parcerias_ong ON ong_parcerias(ong_id);

-- =====================================================================
-- TABELA: ong_fotos
-- =====================================================================
CREATE TABLE IF NOT EXISTS ong_fotos (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    foto_url VARCHAR(500) NOT NULL,
    descricao VARCHAR(255),
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fotos_ong ON ong_fotos(ong_id);

-- =====================================================================
-- TABELA: advertencias
-- =====================================================================
CREATE TABLE IF NOT EXISTS advertencias (
    id SERIAL PRIMARY KEY,
    anuncio_id INTEGER,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    motivo VARCHAR(255) NOT NULL,
    descricao TEXT,
    admin_id INTEGER,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_advertencias_ong ON advertencias(ong_id);
CREATE INDEX IF NOT EXISTS idx_advertencias_anuncio ON advertencias(anuncio_id);

-- =====================================================================
-- TABELA: feedback
-- =====================================================================
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    user_type VARCHAR(50),
    user_email VARCHAR(255),
    user_nome VARCHAR(255),
    mensagem TEXT NOT NULL,
    tipo VARCHAR(50) DEFAULT 'geral',
    anonimo BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'pendente',
    resposta TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_resposta TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);

-- =====================================================================
-- TABELA: suporte
-- =====================================================================
CREATE TABLE IF NOT EXISTS suporte (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    user_type VARCHAR(50),
    user_nome VARCHAR(255),
    user_email VARCHAR(255),
    assunto VARCHAR(255) NOT NULL,
    mensagem TEXT NOT NULL,
    categoria VARCHAR(50) DEFAULT 'duvida',
    status VARCHAR(50) DEFAULT 'aberto',
    resposta TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_resposta TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suporte_user ON suporte(user_id);
CREATE INDEX IF NOT EXISTS idx_suporte_status ON suporte(status);

-- =====================================================================
-- TABELA: comunicacoes
-- =====================================================================
CREATE TABLE IF NOT EXISTS comunicacoes (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    mensagem TEXT NOT NULL,
    prioridade VARCHAR(20) DEFAULT 'normal',
    destinatario_id INTEGER,
    destinatario_tipo VARCHAR(50),
    destinatario_nome VARCHAR(255),
    admin_id INTEGER,
    admin_email VARCHAR(255),
    lida BOOLEAN DEFAULT FALSE,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_leitura TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_comunicacoes_destinatario ON comunicacoes(destinatario_id);
CREATE INDEX IF NOT EXISTS idx_comunicacoes_tipo ON comunicacoes(tipo);

-- =====================================================================
-- TABELA: solicitacoes_exclusao
-- =====================================================================
CREATE TABLE IF NOT EXISTS solicitacoes_exclusao (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    usuario_tipo VARCHAR(50) NOT NULL,
    usuario_email VARCHAR(255),
    usuario_nome VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pendente',
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP,
    data_cancelamento TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes_exclusao(status);

-- =====================================================================
-- TABELA: voluntariado
-- =====================================================================
CREATE TABLE IF NOT EXISTS voluntariado (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    ong_nome VARCHAR(255),
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    data_evento TIMESTAMP,
    local VARCHAR(255),
    vagas_disponiveis INTEGER DEFAULT 1,
    vagas_preenchidas INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'aberta',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voluntariado_ong ON voluntariado(ong_id);
CREATE INDEX IF NOT EXISTS idx_voluntariado_status ON voluntariado(status);

-- =====================================================================
-- TABELA: avaliacoes
-- =====================================================================
CREATE TABLE IF NOT EXISTS avaliacoes (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    doador_id INTEGER NOT NULL REFERENCES doadores(id) ON DELETE CASCADE,
    nota INTEGER NOT NULL CHECK (nota >= 1 AND nota <= 5),
    comentario TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_avaliacoes_ong ON avaliacoes(ong_id);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_doador ON avaliacoes(doador_id);

-- =====================================================================
-- FIM DO SCHEMA
-- Dados de teste são criados pelo init_test_data() em Python.
-- =====================================================================