-- Criação da tabela de Locais
CREATE TABLE local (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(120) NOT NULL
);

-- Criação da tabela de Unidades Locais (ULs)
CREATE TABLE unidade_local (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    descricao VARCHAR(120) NOT NULL,
    local_id INTEGER NOT NULL REFERENCES local(id)
);
