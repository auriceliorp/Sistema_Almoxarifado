-- Adicionar coluna totais_itens à tabela triagem_solicitacao_compra
ALTER TABLE triagem_solicitacao_compra
ADD COLUMN totais_itens JSONB; 
