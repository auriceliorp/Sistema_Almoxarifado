-- Criação da tabela Area
CREATE TABLE IF NOT EXISTS area (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

-- Criação da tabela Setor
CREATE TABLE IF NOT EXISTS setor (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);
