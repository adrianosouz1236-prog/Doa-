-- =====================================================
-- Banco de Dados: doacoes_db
-- Plataforma Doa+ - Conectando Doadores e ONGs
-- PostgreSQL Version
-- =====================================================

-- =====================================================
-- ENUMS
-- =====================================================

CREATE TYPE status_ong AS ENUM ('ativo', 'inativo', 'pendente', 'bloqueado');
CREATE TYPE status_doador AS ENUM ('ativo', 'inativo', 'bloqueado');
CREATE TYPE status_necessidade AS ENUM ('aberta', 'encerrada', 'excluido');
CREATE TYPE status_doacao AS ENUM ('pendente', 'confirmada', 'cancelada');
CREATE TYPE status_doacao_financeira AS ENUM ('pendente', 'confirmado', 'cancelado');
CREATE TYPE status_transacao AS ENUM ('pendente', 'confirmado', 'cancelado', 'processando');
CREATE TYPE status_pagamento AS ENUM ('aprovado', 'recusado', 'pendente');
CREATE TYPE urgencia_enum AS ENUM ('baixa', 'media', 'alta');
CREATE TYPE metodo_pagamento_enum AS ENUM ('cartao', 'pix', 'boleto');
CREATE TYPE tipo_transacao_enum AS ENUM ('doacao_financeira', 'saque', 'estorno');
CREATE TYPE tipo_parceria_enum AS ENUM ('empresa', 'instituicao', 'governo', 'outro');
CREATE TYPE status_voluntariado_enum AS ENUM ('aberta', 'completa', 'cancelada');
CREATE TYPE status_evento_enum AS ENUM ('ativo', 'concluido', 'cancelado');
CREATE TYPE status_suporte_enum AS ENUM ('aberto', 'em_andamento', 'resolvido', 'fechado');
CREATE TYPE status_feedback_enum AS ENUM ('pendente', 'respondido');
CREATE TYPE prioridade_comunicacao_enum AS ENUM ('normal', 'alta', 'urgente');
CREATE TYPE tipo_comunicacao_enum AS ENUM ('todos', 'doadores', 'ongs', 'especifico');
CREATE TYPE gravidade_log_enum AS ENUM ('info', 'alerta', 'media', 'critico');
CREATE TYPE status_exclusao_enum AS ENUM ('pendente', 'confirmado', 'cancelado');
CREATE TYPE tipo_usuario_enum AS ENUM ('ong', 'doador', 'admin');

-- =====================================================
-- TABELAS PRINCIPAIS
-- =====================================================

-- Tabela de ONGs
CREATE TABLE IF NOT EXISTS ongs (
    id SERIAL PRIMARY KEY,
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
    status status_ong DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_advertencias INT DEFAULT 0,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    endereco_completo VARCHAR(255),
    media_avaliacao DECIMAL(3, 2) DEFAULT 0,
    total_avaliacoes INT DEFAULT 0,
    conta_bancaria TEXT,
    email_confirmado BOOLEAN DEFAULT FALSE,
    consentimento_lgpd BOOLEAN DEFAULT FALSE,
    data_consentimento TIMESTAMP,
    ip_consentimento VARCHAR(45),
    user_agent_consentimento TEXT,
    versao_termos VARCHAR(20) DEFAULT 'v1.0'
);

CREATE INDEX idx_ongs_email ON ongs(email);
CREATE INDEX idx_ongs_cidade ON ongs(cidade);
CREATE INDEX idx_ongs_status ON ongs(status);

-- Tabela de Doadores
CREATE TABLE IF NOT EXISTS doadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(15),
    cpf VARCHAR(14) UNIQUE,
    data_nascimento DATE,
    endereco TEXT,
    cidade VARCHAR(50),
    uf CHAR(2),
    status status_doador DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_doacoes INT DEFAULT 0,
    pontuacao INT DEFAULT 0,
    conquistas JSONB,
    email_confirmado BOOLEAN DEFAULT FALSE,
    consentimento_lgpd BOOLEAN DEFAULT FALSE,
    data_consentimento TIMESTAMP,
    ip_consentimento VARCHAR(45),
    user_agent_consentimento TEXT,
    versao_termos VARCHAR(20) DEFAULT 'v1.0',
    total_itens INT DEFAULT 0,
    twofa_secret VARCHAR(255),
    twofa_ativado BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_doadores_email ON doadores(email);
CREATE INDEX idx_doadores_status ON doadores(status);

-- Tabela de Necessidades
CREATE TABLE IF NOT EXISTS necessidades (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(50) NOT NULL,
    quantidade_necessaria INT NOT NULL,
    quantidade_recebida INT DEFAULT 0,
    urgencia urgencia_enum DEFAULT 'media',
    data_limite DATE,
    status status_necessidade DEFAULT 'aberta',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_necessidades_ong ON necessidades(ong_id);
CREATE INDEX idx_necessidades_categoria ON necessidades(categoria);
CREATE INDEX idx_necessidades_status ON necessidades(status);

-- Tabela de Doações (Itens)
CREATE TABLE IF NOT EXISTS doacoes (
    id SERIAL PRIMARY KEY,
    doador_id INTEGER NOT NULL REFERENCES doadores(id) ON DELETE CASCADE,
    necessidade_id INTEGER NOT NULL REFERENCES necessidades(id) ON DELETE CASCADE,
    quantidade INT NOT NULL,
    mensagem TEXT,
    status status_doacao DEFAULT 'pendente',
    data_doacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP
);

CREATE INDEX idx_doacoes_doador ON doacoes(doador_id);
CREATE INDEX idx_doacoes_necessidade ON doacoes(necessidade_id);
CREATE INDEX idx_doacoes_status ON doacoes(status);

-- Tabela de Doações Financeiras
CREATE TABLE IF NOT EXISTS doacoes_financeiras (
    id SERIAL PRIMARY KEY,
    transacao_id VARCHAR(50) UNIQUE NOT NULL,
    doador_id INTEGER NOT NULL REFERENCES doadores(id) ON DELETE CASCADE,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    valor DECIMAL(10, 2) NOT NULL,
    valor_liquido DECIMAL(10, 2) NOT NULL,
    taxa_servico DECIMAL(10, 2) DEFAULT 0,
    mensagem TEXT,
    metodo_pagamento metodo_pagamento_enum DEFAULT 'cartao',
    recorrente BOOLEAN DEFAULT FALSE,
    status status_doacao_financeira DEFAULT 'pendente',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP,
    mp_preference_id VARCHAR(100),
    mp_payment_id VARCHAR(50),
    mp_status VARCHAR(20)
);

CREATE INDEX idx_doacoes_financeiras_transacao ON doacoes_financeiras(transacao_id);
CREATE INDEX idx_doacoes_financeiras_doador ON doacoes_financeiras(doador_id);
CREATE INDEX idx_doacoes_financeiras_ong ON doacoes_financeiras(ong_id);
CREATE INDEX idx_doacoes_financeiras_status ON doacoes_financeiras(status);

-- Tabela de Carteiras
CREATE TABLE IF NOT EXISTS carteiras (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL UNIQUE REFERENCES ongs(id) ON DELETE CASCADE,
    saldo DECIMAL(10, 2) DEFAULT 0,
    total_recebido DECIMAL(10, 2) DEFAULT 0,
    total_sacado DECIMAL(10, 2) DEFAULT 0,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_carteiras_ong ON carteiras(ong_id);

-- Tabela de Transações
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    transacao_id VARCHAR(50) UNIQUE NOT NULL,
    doador_id INTEGER REFERENCES doadores(id) ON DELETE SET NULL,
    ong_id INTEGER REFERENCES ongs(id) ON DELETE SET NULL,
    valor DECIMAL(10, 2) NOT NULL,
    tipo tipo_transacao_enum NOT NULL,
    status status_transacao DEFAULT 'pendente',
    metodo VARCHAR(20),
    conta_bancaria TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_processamento TIMESTAMP,
    mp_preference_id VARCHAR(100)
);

CREATE INDEX idx_transacoes_transacao ON transacoes(transacao_id);
CREATE INDEX idx_transacoes_ong ON transacoes(ong_id);
CREATE INDEX idx_transacoes_doador ON transacoes(doador_id);

-- Tabela de Pagamentos
CREATE TABLE IF NOT EXISTS pagamentos (
    id SERIAL PRIMARY KEY,
    transacao_id INTEGER NOT NULL REFERENCES transacoes(id) ON DELETE CASCADE,
    doacao_financeira_id INTEGER NOT NULL REFERENCES doacoes_financeiras(id) ON DELETE CASCADE,
    status status_pagamento DEFAULT 'pendente',
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    codigo_autorizacao VARCHAR(50)
);

CREATE INDEX idx_pagamentos_transacao ON pagamentos(transacao_id);

-- =====================================================
-- TABELAS DE PERFIL E INTERAÇÕES
-- =====================================================

-- Tabela de Fotos da ONG
CREATE TABLE IF NOT EXISTS ong_fotos (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    foto_url VARCHAR(255) NOT NULL,
    descricao VARCHAR(255),
    tipo VARCHAR(20) DEFAULT 'galeria',
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ong_fotos_ong ON ong_fotos(ong_id);

-- Tabela de Eventos
CREATE TABLE IF NOT EXISTS ong_eventos (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_evento TIMESTAMP NOT NULL,
    local_evento VARCHAR(255),
    endereco TEXT,
    cidade VARCHAR(50),
    uf CHAR(2),
    imagem_url VARCHAR(255),
    status status_evento_enum DEFAULT 'ativo',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ong_eventos_ong ON ong_eventos(ong_id);
CREATE INDEX idx_ong_eventos_data ON ong_eventos(data_evento);
CREATE INDEX idx_ong_eventos_status ON ong_eventos(status);

-- Tabela de Parcerias
CREATE TABLE IF NOT EXISTS ong_parcerias (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    parceiro_nome VARCHAR(100) NOT NULL,
    tipo_parceria VARCHAR(50),
    descricao TEXT,
    logo_url VARCHAR(255),
    website_url VARCHAR(255),
    data_inicio DATE,
    status VARCHAR(20) DEFAULT 'ativa',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ong_parcerias_ong ON ong_parcerias(ong_id);

-- Tabela de Avaliações
CREATE TABLE IF NOT EXISTS avaliacoes (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    doador_id INTEGER NOT NULL REFERENCES doadores(id) ON DELETE CASCADE,
    doador_nome VARCHAR(100),
    nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ong_id, doador_id)
);

CREATE INDEX idx_avaliacoes_ong ON avaliacoes(ong_id);
CREATE INDEX idx_avaliacoes_doador ON avaliacoes(doador_id);

-- =====================================================
-- TABELAS DE VOLUNTARIADO
-- =====================================================

-- Tabela de Vagas de Voluntariado
CREATE TABLE IF NOT EXISTS voluntariado_vagas (
    id SERIAL PRIMARY KEY,
    ong_id INTEGER NOT NULL REFERENCES ongs(id) ON DELETE CASCADE,
    ong_nome VARCHAR(100),
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_evento TIMESTAMP,
    local VARCHAR(255),
    vagas_disponiveis INT DEFAULT 1,
    vagas_preenchidas INT DEFAULT 0,
    habilidades TEXT,
    status status_voluntariado_enum DEFAULT 'aberta',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_voluntariado_vagas_ong ON voluntariado_vagas(ong_id);
CREATE INDEX idx_voluntariado_vagas_status ON voluntariado_vagas(status);

-- Tabela de Inscrições Voluntariado
CREATE TABLE IF NOT EXISTS voluntariado_inscricoes (
    id SERIAL PRIMARY KEY,
    vaga_id INTEGER NOT NULL REFERENCES voluntariado_vagas(id) ON DELETE CASCADE,
    doador_id INTEGER NOT NULL REFERENCES doadores(id) ON DELETE CASCADE,
    doador_nome VARCHAR(100),
    data_inscricao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'confirmada',
    UNIQUE (vaga_id, doador_id)
);

CREATE INDEX idx_voluntariado_inscricoes_vaga ON voluntariado_inscricoes(vaga_id);
CREATE INDEX idx_voluntariado_inscricoes_doador ON voluntariado_inscricoes(doador_id);

-- =====================================================
-- TABELAS DE FEEDBACK E SUPORTE
-- =====================================================

-- Tabela de Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL,
    user_email VARCHAR(100),
    user_nome VARCHAR(100),
    mensagem TEXT NOT NULL,
    tipo VARCHAR(50) DEFAULT 'geral',
    anonimo BOOLEAN DEFAULT FALSE,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status status_feedback_enum DEFAULT 'pendente',
    resposta TEXT,
    data_resposta TIMESTAMP
);

CREATE INDEX idx_feedback_user ON feedback(user_id);
CREATE INDEX idx_feedback_status ON feedback(status);

-- Tabela de Suporte
CREATE TABLE IF NOT EXISTS suporte (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL,
    user_email VARCHAR(100),
    user_nome VARCHAR(100),
    assunto VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    categoria VARCHAR(50) DEFAULT 'duvida',
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status status_suporte_enum DEFAULT 'aberto',
    resposta TEXT,
    data_resposta TIMESTAMP,
    responsavel VARCHAR(100)
);

CREATE INDEX idx_suporte_user ON suporte(user_id);
CREATE INDEX idx_suporte_status ON suporte(status);

-- =====================================================
-- TABELAS DE COMUNICAÇÃO E NOTIFICAÇÕES
-- =====================================================

-- Tabela de Comunicações
CREATE TABLE IF NOT EXISTS comunicacoes (
    id SERIAL PRIMARY KEY,
    admin_email VARCHAR(100) NOT NULL,
    tipo tipo_comunicacao_enum NOT NULL,
    destinatario_id INT,
    destinatario_tipo VARCHAR(20),
    destinatario_nome VARCHAR(100),
    titulo VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    prioridade prioridade_comunicacao_enum DEFAULT 'normal',
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lida BOOLEAN DEFAULT FALSE,
    data_leitura TIMESTAMP
);

CREATE INDEX idx_comunicacoes_tipo ON comunicacoes(tipo);
CREATE INDEX idx_comunicacoes_destinatario ON comunicacoes(destinatario_id);

-- Tabela de Notificações
CREATE TABLE IF NOT EXISTS notificacoes (
    id SERIAL PRIMARY KEY,
    admin_email VARCHAR(100) NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'informativo',
    destino VARCHAR(20) DEFAULT 'todos',
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enviado BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_notificacoes_destino ON notificacoes(destino);

-- Tabela de Preferências de Notificação
CREATE TABLE IF NOT EXISTS notificacoes_preferencias (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL,
    email_doacoes BOOLEAN DEFAULT TRUE,
    email_novas_necessidades BOOLEAN DEFAULT TRUE,
    email_eventos BOOLEAN DEFAULT TRUE,
    email_newsletter BOOLEAN DEFAULT FALSE,
    push_doacoes BOOLEAN DEFAULT TRUE,
    push_novas_necessidades BOOLEAN DEFAULT TRUE,
    push_eventos BOOLEAN DEFAULT TRUE,
    push_mensagens BOOLEAN DEFAULT TRUE,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, user_type)
);

CREATE INDEX idx_notificacoes_preferencias_user ON notificacoes_preferencias(user_id);

-- =====================================================
-- TABELAS DE CHAT
-- =====================================================

-- Tabela de Mensagens do Chat
CREATE TABLE IF NOT EXISTS chat_mensagens (
    id SERIAL PRIMARY KEY,
    remetente_id INTEGER NOT NULL,
    remetente_tipo VARCHAR(20) NOT NULL,
    destinatario_id INTEGER NOT NULL,
    destinatario_tipo VARCHAR(20) NOT NULL,
    mensagem TEXT NOT NULL,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lida BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_chat_mensagens_remetente ON chat_mensagens(remetente_id);
CREATE INDEX idx_chat_mensagens_destinatario ON chat_mensagens(destinatario_id);

-- =====================================================
-- TABELAS DE SEGURANÇA
-- =====================================================

-- Tabela de Logs de Segurança
CREATE TABLE IF NOT EXISTS logs_seguranca (
    id SERIAL PRIMARY KEY,
    evento VARCHAR(100) NOT NULL,
    usuario_id INT,
    usuario_tipo tipo_usuario_enum,
    ip VARCHAR(45),
    user_agent TEXT,
    detalhes JSONB,
    gravidade gravidade_log_enum DEFAULT 'info',
    data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_seguranca_evento ON logs_seguranca(evento);
CREATE INDEX idx_logs_seguranca_usuario ON logs_seguranca(usuario_id);
CREATE INDEX idx_logs_seguranca_gravidade ON logs_seguranca(gravidade);

-- Tabela de Tentativas de Login
CREATE TABLE IF NOT EXISTS tentativas_login (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100),
    ip VARCHAR(45),
    sucesso BOOLEAN DEFAULT FALSE,
    data_tentativa TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tentativas_login_ip ON tentativas_login(ip);
CREATE INDEX idx_tentativas_login_email ON tentativas_login(email);

-- Tabela de Advertências
CREATE TABLE IF NOT EXISTS advertencias (
    id SERIAL PRIMARY KEY,
    anuncio_id INTEGER NOT NULL,
    ong_id INTEGER NOT NULL,
    motivo VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_advertencia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin VARCHAR(100)
);

CREATE INDEX idx_advertencias_ong ON advertencias(ong_id);
CREATE INDEX idx_advertencias_anuncio ON advertencias(anuncio_id);

-- Tabela de Solicitações de Exclusão
CREATE TABLE IF NOT EXISTS solicitacoes_exclusao (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    usuario_nome VARCHAR(100),
    usuario_email VARCHAR(100) NOT NULL,
    usuario_tipo VARCHAR(20) NOT NULL,
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status status_exclusao_enum DEFAULT 'pendente',
    data_confirmacao TIMESTAMP,
    data_cancelamento TIMESTAMP,
    admin VARCHAR(100)
);

CREATE INDEX idx_solicitacoes_exclusao_usuario ON solicitacoes_exclusao(usuario_id);
CREATE INDEX idx_solicitacoes_exclusao_status ON solicitacoes_exclusao(status);

-- =====================================================
-- TABELAS DE RELATÓRIOS
-- =====================================================

-- Tabela de Relatórios Anuais
CREATE TABLE IF NOT EXISTS relatorios_anuais (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    usuario_type VARCHAR(20) NOT NULL,
    usuario_email VARCHAR(100),
    ano INTEGER NOT NULL,
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    caminho VARCHAR(255),
    status VARCHAR(20) DEFAULT 'gerado'
);

CREATE INDEX idx_relatorios_anuais_usuario ON relatorios_anuais(usuario_id);
CREATE INDEX idx_relatorios_anuais_ano ON relatorios_anuais(ano);

-- =====================================================
-- DADOS INICIAIS (SEED)
-- =====================================================

-- Inserir ONG de exemplo
INSERT INTO ongs (nome, cnpj, email, senha, telefone, endereco, cidade, uf, descricao, logo_url, status, email_confirmado, consentimento_lgpd, data_consentimento) 
VALUES 
('ONG Solidária Brasil', '12.345.678/0001-90', 'ong@solidaria.org', '$2b$12$3zXkPfVHlhBxXlJ6bqTTmO4gBt9aFwR3zKQ8uE5vN2wP1yY7zL8zW', '(11) 99999-9999', 'Rua da Solidariedade, 100', 'São Paulo', 'SP', 'ONG dedicada a ajudar pessoas em situação de vulnerabilidade social.', 'https://via.placeholder.com/150?text=Logo+ONG', 'ativo', TRUE, TRUE, CURRENT_TIMESTAMP);

-- Inserir Doador de exemplo
INSERT INTO doadores (nome, email, senha, telefone, status, email_confirmado, consentimento_lgpd, data_consentimento) 
VALUES 
('João Silva', 'joao@email.com', '$2b$10$e0Q8Z9wR5tU7vN2wP1yY7zL8zW3zXkPfVHlhBxXlJ6bqTTmO4gBt9aF', '(11) 98888-7777', 'ativo', TRUE, TRUE, CURRENT_TIMESTAMP);

-- Inserir Necessidade
INSERT INTO necessidades (ong_id, titulo, descricao, categoria, quantidade_necessaria, quantidade_recebida, urgencia, status) 
VALUES 
(1, 'Arrecadação de Alimentos', 'Precisamos de alimentos não perecíveis para distribuir para 100 famílias carentes.', 'alimentos', 500, 150, 'alta', 'aberta');

-- Inserir Evento
INSERT INTO ong_eventos (ong_id, titulo, descricao, data_evento, local_evento, endereco, cidade, uf, status) 
VALUES 
(1, 'Dia da Solidariedade', 'Venha participar do nosso evento de arrecadação de alimentos e roupas. Teremos música, comida e muito amor ao próximo!', '2024-12-15 10:00:00', 'Parque da Cidade', 'Av. Principal, 500', 'São Paulo', 'SP', 'ativo');

-- Inserir Parceria
INSERT INTO ong_parcerias (ong_id, parceiro_nome, tipo_parceria, descricao, website_url, status) 
VALUES 
(1, 'Mercado Popular', 'empresa', 'Parceiro na arrecadação de alimentos mensalmente.', 'https://mercadopopular.com.br', 'ativa');

-- Inserir Fotos
INSERT INTO ong_fotos (ong_id, foto_url, descricao, tipo) 
VALUES 
(1, 'https://via.placeholder.com/400x300?text=Evento+ONG', 'Evento de arrecadação - 2023', 'galeria'),
(1, 'https://via.placeholder.com/400x300?text=Equipe+ONG', 'Nossa equipe de voluntários', 'galeria');

-- =====================================================
-- FIM DO SCHEMA
-- =====================================================