-- Adiciona campos ausentes à tabela usuarios

ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS matricula VARCHAR(50);

ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS ramal VARCHAR(20);

ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS unidade_local_id INTEGER;

ALTER TABLE usuarios
ADD CONSTRAINT fk_usuarios_unidade_local
FOREIGN KEY (unidade_local_id) REFERENCES unidade_local(id);

ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS perfil_id INTEGER;

ALTER TABLE usuarios
ADD CONSTRAINT fk_usuarios_perfil
FOREIGN KEY (perfil_id) REFERENCES perfil(id);

ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS senha_temporaria BOOLEAN DEFAULT TRUE;
