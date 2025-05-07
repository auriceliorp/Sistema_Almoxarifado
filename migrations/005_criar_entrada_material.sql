-- Criação da tabela entrada_material
CREATE TABLE IF NOT EXISTS entrada_material (
    id SERIAL PRIMARY KEY,
    data_movimento DATE NOT NULL,
    data_nota_fiscal DATE NOT NULL,
    numero_nota_fiscal VARCHAR(50) NOT NULL,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedor(id) ON DELETE RESTRICT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criação da tabela entrada_item
CREATE TABLE IF NOT EXISTS entrada_item (
    id SERIAL PRIMARY KEY,
    entrada_material_id INTEGER NOT NULL REFERENCES entrada_material(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES item(id) ON DELETE RESTRICT,
    quantidade INTEGER NOT NULL,
    valor_unitario NUMERIC(10, 2) NOT NULL,
    valor_total NUMERIC(10, 2)
);

-- Trigger Function para calcular automaticamente o valor_total
CREATE OR REPLACE FUNCTION calcular_valor_total_entrada_item()
RETURNS TRIGGER AS $$
BEGIN
    NEW.valor_total := NEW.quantidade * NEW.valor_unitario;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criação da trigger somente se não existir
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_calcular_valor_total_entrada_item'
  ) THEN
    CREATE TRIGGER trg_calcular_valor_total_entrada_item
    BEFORE INSERT OR UPDATE ON entrada_item
    FOR EACH ROW
    EXECUTE FUNCTION calcular_valor_total_entrada_item();
  END IF;
END $$;

-- Trigger Function para atualizar o valor da Natureza de Despesa
CREATE OR REPLACE FUNCTION atualizar_valor_nd_entrada()
RETURNS TRIGGER AS $$
DECLARE
    v_nd_id INTEGER;
BEGIN
    SELECT natureza_despesa_id INTO v_nd_id
    FROM item
    WHERE id = NEW.item_id;

    IF v_nd_id IS NOT NULL THEN
        UPDATE natureza_despesa
        SET valor = COALESCE(valor, 0) + NEW.valor_total
        WHERE id = v_nd_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criação da trigger somente se não existir
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_atualizar_valor_nd_entrada'
  ) THEN
    CREATE TRIGGER trg_atualizar_valor_nd_entrada
    AFTER INSERT ON entrada_item
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_valor_nd_entrada();
  END IF;
END $$;
