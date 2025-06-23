-- Criar tabela de itens do painel
CREATE TABLE IF NOT EXISTS itens_painel_contratacao (
    id SERIAL PRIMARY KEY,
    painel_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    valor_unitario NUMERIC(14, 2),
    valor_total NUMERIC(14, 2),
    CONSTRAINT fk_painel FOREIGN KEY (painel_id)
        REFERENCES painel_contratacoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_item FOREIGN KEY (item_id)
        REFERENCES item(id)
);

-- Criar tabela de associação para solicitantes
CREATE TABLE IF NOT EXISTS painel_solicitantes (
    painel_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    PRIMARY KEY (painel_id, usuario_id),
    CONSTRAINT fk_painel_solicitante FOREIGN KEY (painel_id)
        REFERENCES painel_contratacoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_usuario_solicitante FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
);

-- Criar índices para melhorar performance (se não existirem)
CREATE INDEX IF NOT EXISTS idx_itens_painel_contratacao_painel ON itens_painel_contratacao(painel_id);
CREATE INDEX IF NOT EXISTS idx_itens_painel_contratacao_item ON itens_painel_contratacao(item_id);
CREATE INDEX IF NOT EXISTS idx_painel_solicitantes_painel ON painel_solicitantes(painel_id);
CREATE INDEX IF NOT EXISTS idx_painel_solicitantes_usuario ON painel_solicitantes(usuario_id);

-- Migrar dados existentes de solicitações de compra para o painel
INSERT INTO itens_painel_contratacao (painel_id, item_id, quantidade, valor_unitario, valor_total)
SELECT DISTINCT
    sc.painel_contratacao_id,
    isc.item_id,
    isc.quantidade,
    i.valor_unitario,
    (isc.quantidade * i.valor_unitario) as valor_total
FROM solicitacao_compra sc
JOIN item_solicitacao_compra isc ON isc.solicitacao_id = sc.id
JOIN item i ON i.id = isc.item_id
WHERE sc.painel_contratacao_id IS NOT NULL
ON CONFLICT DO NOTHING;

-- Migrar solicitantes existentes
INSERT INTO painel_solicitantes (painel_id, usuario_id)
SELECT DISTINCT painel_contratacao_id, solicitante_id
FROM solicitacao_compra
WHERE painel_contratacao_id IS NOT NULL
ON CONFLICT DO NOTHING; 
