# routes_auditoria.py
# Rotas para exibição dos logs de auditoria do sistema

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import AuditLog
from utils.auditoria import json_pretty
from functools import wraps

# Criação do blueprint
auditoria_bp = Blueprint('auditoria_bp', __name__, url_prefix='/auditoria')

# ------------------------ Decorador de restrição para admin ------------------------ #
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.email != 'admin@admin.com':
            return render_template('acesso_negado.html')
        return f(*args, **kwargs)
    return decorated_function

# ------------------------ ROTA: Lista de Logs ------------------------ #
@auditoria_bp.route('/logs')
@login_required
@admin_required
def lista_logs():
    page = request.args.get('page', 1, type=int)
    filtro = request.args.get('filtro', 'tabela')
    busca = request.args.get('busca', '').strip().lower()

    query = AuditLog.query

    if busca:
        if filtro == 'tabela':
            query = query.filter(AuditLog.tabela.ilike(f'%{busca}%'))
        elif filtro == 'acao':
            query = query.filter(AuditLog.acao.ilike(f'%{busca}%'))

    logs = query.order_by(AuditLog.data_hora.desc()).paginate(page=page, per_page=10)

    return render_template('lista_auditoria.html', logs=logs, filtro=filtro, busca=busca)

# ------------------------ ROTA: Detalhes do Log ------------------------ #
@auditoria_bp.route('/log/<int:log_id>')
@login_required
@admin_required
def detalhes_log(log_id):
    log = AuditLog.query.get_or_404(log_id)

    dados_antes = json_pretty(log.dados_anteriores)
    dados_novos = json_pretty(log.dados_novos)

    return render_template('detalhes_log.html', log=log, dados_antes=dados_antes, dados_novos=dados_novos)