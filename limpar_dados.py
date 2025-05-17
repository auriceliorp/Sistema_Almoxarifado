# limpar_dados.py
# Rota dedicada para limpar registros de teste do banco de dados, mantendo os usuários e configurações

from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import (
    EntradaItem, EntradaMaterial,
    SaidaItem, SaidaMaterial,
    Item, Grupo, NaturezaDespesa,
    Fornecedor
)

# Criação do blueprint
limpar_bp = Blueprint('limpar_bp', __name__)

# ------------------------------ ROTA: Limpar Dados de Teste ------------------------------ #
@limpar_bp.route('/limpar')
@login_required
def limpar_dados():
    try:
        # Ordem de exclusão respeita as dependências entre tabelas (evita erros de integridade)
        db.session.query(EntradaItem).delete()       # Itens precisam sair antes da entrada
        db.session.query(EntradaMaterial).delete()   # Entradas referenciadas por itens
        db.session.query(SaidaItem).delete()
        db.session.query(SaidaMaterial).delete()
        db.session.query(Item).delete()              # Itens dependem de grupo e natureza
        db.session.query(Grupo).delete()
        db.session.query(NaturezaDespesa).delete()
        db.session.query(Fornecedor).delete()

        db.session.commit()
        flash('Base de dados limpa com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao limpar base de dados: {e}', 'danger')

    # Redireciona de volta ao dashboard após a limpeza
    return redirect(url_for('dashboard_bp.dashboard'))