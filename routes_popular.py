# routes_popular.py
# Rota para popular o banco de dados com dados fictícios para teste, com verificação e opção de continuar

from flask import Blueprint, redirect, url_for, flash, request, render_template
from flask_login import login_required, current_user
from extensoes import db
from models import (
    NaturezaDespesa, Grupo, Item, Fornecedor, Usuario,
    UnidadeLocal, Local, EntradaMaterial, SaidaMaterial
)

# Cria o blueprint com prefixo de rota /popular
popular_bp = Blueprint('popular_bp', __name__, url_prefix='/popular')


# -------------------- ROTA: Verifica se há dados existentes -------------------- #
@popular_bp.route('/verificar')
@login_required
def verificar_dados_existentes():
    if current_user.email != 'admin@admin.com':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('main.home'))

    # Verifica se existe algum dado em cada tabela (exceto admin)
    tabelas = {
        'Naturezas de Despesa': NaturezaDespesa.query.first(),
        'Grupos': Grupo.query.first(),
        'Itens': Item.query.first(),
        'Fornecedores': Fornecedor.query.first(),
        'Usuários': Usuario.query.filter(Usuario.email != 'admin@admin.com').first(),
        'Unidades Locais': UnidadeLocal.query.first(),
        'Locais': Local.query.first(),
        'Entradas de Material': EntradaMaterial.query.first(),
        'Saídas de Material': SaidaMaterial.query.first()
    }

    tabelas_existentes = [nome for nome, valor in tabelas.items() if valor is not None]

    if tabelas_existentes:
        # Renderiza página de confirmação com as tabelas já preenchidas
        return render_template('verificar_dados.html', tabelas=tabelas_existentes)
    else:
        # Se nenhuma tabela tiver dados, popula direto
        return redirect(url_for('popular_bp.popular_dados'))


# -------------------- ROTA: Executa script de popular dados -------------------- #
@popular_bp.route('/')
@login_required
def popular_dados():
    if current_user.email != 'admin@admin.com':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('main.home'))

    try:
        exec(open('popular_dados.py').read())
        flash('Base de dados populada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao popular base de dados: {e}', 'danger')

    return redirect(url_for('main.home'))