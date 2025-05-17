# limpar_dados.py
# Rota para limpar dados de teste da base

from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial, Item, Grupo, NaturezaDespesa, Fornecedor

limpar_bp = Blueprint('limpar_bp', __name__)

@limpar_bp.route('/limpar')
@login_required
def limpar_dados():
    try:
        # Deleta registros em ordem reversa de dependência
        db.session.query(EntradaItem).delete()
        db.session.query(EntradaMaterial).delete()
        db.session.query(SaidaItem).delete()
        db.session.query(SaidaMaterial).delete()
        db.session.query(Item).delete()
        db.session.query(Grupo).delete()
        db.session.query(NaturezaDespesa).delete()
        db.session.query(Fornecedor).delete()

        db.session.commit()
        flash('Base de dados limpa com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao limpar base de dados: {e}', 'danger')
    return redirect(url_for('dashboard_bp.dashboard'))