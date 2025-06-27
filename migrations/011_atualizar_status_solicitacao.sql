UPDATE solicitacao_compra
SET status = 'Pendente'
WHERE status IN ('PENDENTE');

UPDATE solicitacao_compra
SET status = 'Em Andamento'
WHERE status IN ('EM_ANALISE', 'EM_ANDAMENTO', 'Em andamento');

UPDATE solicitacao_compra
SET status = 'Processo Iniciado'
WHERE status IN ('PROCESSO_INICIADO', 'Processo Iniciado');

UPDATE solicitacao_compra
SET status = 'Concluido'
WHERE status IN ('APROVADA', 'CONCLUIDO', 'Concluído');

UPDATE solicitacao_compra
SET status = 'Cancelada'
WHERE status IN ('REJEITADA', 'CANCELADA', 'Cancelada');

-- Atualizar outros status que possam existir
UPDATE solicitacao_compra
SET status = 'Aguardando Definições'
WHERE status IN ('AGUARDANDO_DEFINICOES', 'Aguardando Definições');
