-- Criar tabela de atividades
CREATE TABLE atividades (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    data_inicio DATE,
    data_fim DATE,
    status VARCHAR(20) DEFAULT 'ATIVA',
    responsavel_id INTEGER REFERENCES usuarios(id),
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices
CREATE INDEX idx_atividades_numero ON atividades(numero);
CREATE INDEX idx_atividades_status ON atividades(status);
CREATE INDEX idx_atividades_responsavel ON atividades(responsavel_id);

-- Alterar tabela solicitacao_compra para usar foreign key
ALTER TABLE solicitacao_compra 
    DROP COLUMN numero_atividade,
    DROP COLUMN nome_atividade,
    ADD COLUMN atividade_id INTEGER REFERENCES atividades(id);
