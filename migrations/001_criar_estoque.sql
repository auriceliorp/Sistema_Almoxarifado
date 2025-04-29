-- Criação da tabela estoque
CREATE TABLE IF NOT EXISTS estoque (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    fornecedor VARCHAR(255),
    nota_fiscal VARCHAR(100),
    valor_unitario NUMERIC(10, 2),
    quantidade INTEGER,
    local VARCHAR(255),
    valor_total NUMERIC(10, 2),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger Function para calcular o valor_total automaticamente
CREATE OR REPLACE FUNCTION atualizar_valor_total()
RETURNS TRIGGER AS $$
BEGIN
    NEW.valor_total := NEW.valor_unitario * NEW.quantidade;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criação da trigger na tabela estoque
CREATE TRIGGER trigger_atualizar_valor_total
BEFORE INSERT OR UPDATE ON estoque
FOR EACH ROW
EXECUTE FUNCTION atualizar_valor_total();

-- Trigger Function para atualizar saldo da Natureza de Despesa
CREATE OR REPLACE FUNCTION atualizar_saldo_nd()
RETURNS TRIGGER AS $$
DECLARE
    v_nd_id INTEGER;
BEGIN
    -- Pega a natureza de despesa associada ao item
    SELECT natureza_despesa_id INTO v_nd_id FROM item WHERE id = NEW.item_id;

    -- Atualiza o saldo da natureza de despesa
    IF v_nd_id IS NOT NULL THEN
        UPDATE natureza_despesa
        SET saldo = COALESCE(saldo, 0) + (NEW.valor_unitario * NEW.quantidade)
        WHERE id = v_nd_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criação da trigger para atualizar saldo da ND após inserção no estoque
CREATE TRIGGER trigger_atualizar_saldo_nd
AFTER INSERT ON estoque
FOR EACH ROW
EXECUTE FUNCTION atualizar_saldo_nd();
