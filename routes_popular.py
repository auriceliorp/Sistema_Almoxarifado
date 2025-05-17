# routes_popular.py
# Rota para popular o banco de dados com dados fictícios para teste

from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user

# Cria o blueprint com prefixo de rota /popular
popular_bp = Blueprint('popular_bp', __name__, url_prefix='/popular')

# -------------------- ROTA: Executa script de popular dados -------------------- #
@popular_bp.route('/')
@login_required  # exige que o usuário esteja autenticado
def popular_dados():
    # Permite acesso apenas ao usuário administrador
    if current_user.email != 'admin@admin.com':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('main.home'))

    try:
        # Executa o script Python como se estivesse rodando manualmente
        exec(open('popular_dados.py').read())
        flash('Base de dados populada com sucesso!', 'success')
    except Exception as e:
        # Em caso de erro, desfaz a transação e mostra mensagem
        flash(f'Erro ao popular base de dados: {e}', 'danger')

    return redirect(url_for('main.home'))