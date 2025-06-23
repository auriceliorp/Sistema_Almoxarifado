-- Criar tabela de itens do painel
CREATE TABLE itens_painel_contratacao (
    id SERIAL PRIMARY KEY,
    painel_id INTEGER NOT NULL REFERENCES painel_contratacoes(id),
    item_id INTEGER NOT NULL REFERENCES item(id),
    quantidade INTEGER NOT NULL,
    valor_unitario NUMERIC(14, 2),
    valor_total NUMERIC(14, 2),
    CONSTRAINT fk_painel FOREIGN KEY (painel_id)
        REFERENCES painel_contratacoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_item FOREIGN KEY (item_id)
        REFERENCES item(id)
);

-- Criar tabela de associação para solicitantes
CREATE TABLE painel_solicitantes (
    painel_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    PRIMARY KEY (painel_id, usuario_id),
    CONSTRAINT fk_painel FOREIGN KEY (painel_id)
        REFERENCES painel_contratacoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
);

-- Criar índices
CREATE INDEX idx_itens_painel_contratacao_painel ON itens_painel_contratacao(painel_id);
CREATE INDEX idx_itens_painel_contratacao_item ON itens_painel_contratacao(item_id);
CREATE INDEX idx_painel_solicitantes_painel ON painel_solicitantes(painel_id);
CREATE INDEX idx_painel_solicitantes_usuario ON painel_solicitantes(usuario_id); 
