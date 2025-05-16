# utils/auditoria.py

import json
from models import AuditLog
from flask_login import current_user
from app_render import db

def registrar_auditoria(acao, tabela, registro_id=None, dados_antes=None, dados_depois=None):
    log = AuditLog(
        usuario_id=current_user.id if current_user.is_authenticated else None,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        dados_anteriores=json.dumps(dados_antes) if dados_antes else None,
        dados_novos=json.dumps(dados_depois) if dados_depois else None
    )
    db.session.add(log)
