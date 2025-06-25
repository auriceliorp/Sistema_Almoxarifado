CREATE TABLE IF NOT EXISTS triagem_solicitacao_compra (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responsavel_id INTEGER NOT NULL REFERENCES usuarios(id),
    status VARCHAR(50) DEFAULT 'Processo Iniciado',
    CONSTRAINT fk_responsavel FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
);

ALTER TABLE solicitacao_compra
ADD COLUMN IF NOT EXISTS triagem_id INTEGER REFERENCES triagem_solicitacao_compra(id);
