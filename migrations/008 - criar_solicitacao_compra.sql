-- Criar tabela de solicitação de compra
CREATE TABLE solicitacao_compra (
    id SERIAL PRIMARY KEY,
    data_solicitacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    numero_atividade VARCHAR(50),
    nome_atividade VARCHAR(200),
    finalidade TEXT NOT NULL,
    justificativa_marca TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
    solicitante_id INTEGER NOT NULL REFERENCES usuarios(id),
    tarefa_id INTEGER REFERENCES tarefas(id)
);

-- Criar tabela de itens da solicitação
CREATE TABLE item_solicitacao_compra (
    id SERIAL PRIMARY KEY,
    solicitacao_id INTEGER NOT NULL REFERENCES solicitacao_compra(id),
    item_id INTEGER NOT NULL REFERENCES item(id),
    quantidade INTEGER NOT NULL,
    CONSTRAINT fk_solicitacao_compra FOREIGN KEY (solicitacao_id)
        REFERENCES solicitacao_compra(id) ON DELETE CASCADE,
    CONSTRAINT fk_item FOREIGN KEY (item_id)
        REFERENCES item(id)
);

-- Criar índices
CREATE INDEX idx_solicitacao_compra_solicitante ON solicitacao_compra(solicitante_id);
CREATE INDEX idx_solicitacao_compra_status ON solicitacao_compra(status);
CREATE INDEX idx_item_solicitacao_compra_solicitacao ON item_solicitacao_compra(solicitacao_id);
