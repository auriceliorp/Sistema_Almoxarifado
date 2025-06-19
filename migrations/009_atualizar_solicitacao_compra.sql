-- Adicionar coluna de referência ao painel
ALTER TABLE solicitacao_compra 
ADD COLUMN painel_contratacao_id integer;

-- Adicionar a foreign key
ALTER TABLE solicitacao_compra 
ADD CONSTRAINT fk_painel_contratacao 
FOREIGN KEY (painel_contratacao_id) 
REFERENCES painel_contratacoes(id);

-- Atualizar os status existentes para o novo padrão
UPDATE solicitacao_compra 
SET status = CASE 
    WHEN status = 'PENDENTE' THEN 'Processo Iniciado'
    WHEN status = 'APROVADA' THEN 'Em andamento'
    WHEN status = 'CONCLUÍDA' THEN 'Concluído'
    WHEN status = 'REJEITADA' THEN 'Cancelada'
    ELSE status 
END;

-- Alterar o tipo da coluna status se necessário
ALTER TABLE solicitacao_compra 
ALTER COLUMN status TYPE varchar(50); 
