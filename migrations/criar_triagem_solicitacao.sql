-- migrations/010_criar_triagem_solicitacao.sql
CREATE TABLE triagem_solicitacao_compra (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responsavel_id INTEGER REFERENCES usuarios(id) NOT NULL
);

ALTER TABLE solicitacao_compra
ADD COLUMN triagem_id INTEGER REFERENCES triagem_solicitacao_compra(id);
