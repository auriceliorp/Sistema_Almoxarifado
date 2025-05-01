-- Criação da tabela "local"
CREATE TABLE IF NOT EXISTS local (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL
);

-- Criação da tabela "ul"
CREATE TABLE IF NOT EXISTS ul (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    local_id INTEGER NOT NULL,
    CONSTRAINT fk_ul_local FOREIGN KEY (local_id) REFERENCES local(id)
);
