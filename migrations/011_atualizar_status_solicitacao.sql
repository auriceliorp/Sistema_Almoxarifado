-- Atualizar status das solicitações existentes
UPDATE solicitacao_compra
SET status = 'Pendente'
WHERE status IN ('PENDENTE', 'PROCESSO_INICIADO', 'Processo Iniciado');

UPDATE solicitacao_compra
SET status = 'Andamento'
WHERE status IN ('EM_ANALISE', 'EM_ANDAMENTO', 'Em andamento');

UPDATE solicitacao_compra
SET status = 'Concluido'
WHERE status IN ('APROVADA', 'CONCLUIDO', 'Concluído');

UPDATE solicitacao_compra
SET status = 'Cancelada'
WHERE status IN ('REJEITADA', 'CANCELADA', 'Cancelada');

-- Atualizar outros status que possam existir
UPDATE solicitacao_compra
SET status = 'AGUARDANDO_DEFINICOES'
WHERE status IN ('Aguardando Definições'); 
