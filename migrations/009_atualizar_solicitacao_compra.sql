-- Atualizar a coluna status
ALTER TABLE solicitacao_compra 
ALTER COLUMN status TYPE varchar(50);

-- Adicionar coluna de referência ao painel
ALTER TABLE solicitacao_compra 
ADD COLUMN painel_contratacao_id integer REFERENCES painel_contratacoes(id);

-- Atualizar os status existentes
UPDATE solicitacao_compra 
SET status = 'Processo Iniciado' 
WHERE status = 'PENDENTE';

UPDATE solicitacao_compra 
SET status = 'Concluído' 
WHERE status = 'CONCLUÍDA'; 
