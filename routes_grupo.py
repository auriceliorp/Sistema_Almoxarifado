# routes_grupo.py
# Rotas para gerenciamento de Grupos de Itens

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import Grupo, NaturezaDespesa

grupo_bp = Blueprint('grupo_bp', __name__, url_prefix='/grupo')


# ------------------------------ LISTAGEM ------------------------------ #
@grupo_bp.route('/')
@login_required
def lista_grupos():
    """
    Lista todos os grupos de itens cadastrados.
    """
    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template('partials/grupo/lista_grupo.html', grupos=grupos)


# ------------------------------ NOVO GRUPO ------------------------------ #
@grupo_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_grupo():
    """
    Exibe o formulário e cadastra um novo grupo de itens.
    """
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        natureza_id = request.form.get('natureza_despesa_id')

        if not nome or not natureza_id:
            flash('Preencha todos os campos obrigatórios.')
            return render_template('partials/grupo/form_grupo.html', grupo=None, naturezas=naturezas)

        # Verifica duplicidade dentro da mesma ND
        existente = Grupo.query.filter_by(nome=nome, natureza_despesa_id=natureza_id).first()
        if existente:
            flash('Já existe um grupo com esse nome vinculado a essa Natureza de Despesa.')
            return render_template('partials/grupo/form_grupo.html', grupo=None, naturezas=naturezas)

        try:
            novo = Grupo(nome=nome, natureza_despesa_id=natureza_id)
            db.session.add(novo)
            db.session.commit()
            flash('Grupo cadastrado com sucesso!')
            return redirect(url_for('grupo_bp.lista_grupos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar grupo: {e}')
            return render_template('partials/grupo/form_grupo.html', grupo=None, naturezas=naturezas)

    return render_template('partials/grupo/form_grupo.html', grupo=None, naturezas=naturezas)


# ------------------------------ EDITAR GRUPO ------------------------------ #
@grupo_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_grupo(id):
    """
    Exibe o formulário e atualiza um grupo de itens existente.
    """
    grupo = Grupo.query.get_or_404(id)
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        natureza_id = request.form.get('natureza_despesa_id')

        if not nome or not natureza_id:
            flash('Preencha todos os campos obrigatórios.')
            return render_template('partials/grupo/form_grupo.html', grupo=grupo, naturezas=naturezas)

        # Verifica se está tentando renomear para um nome já existente na mesma ND
        duplicado = Grupo.query.filter(
            Grupo.id != grupo.id,
            Grupo.nome == nome,
            Grupo.natureza_despesa_id == natureza_id
        ).first()
        if duplicado:
            flash('Já existe outro grupo com esse nome para a mesma Natureza de Despesa.')
            return render_template('partials/grupo/form_grupo.html', grupo=grupo, naturezas=naturezas)

        try:
            grupo.nome = nome
            grupo.natureza_despesa_id = natureza_id
            db.session.commit()
            flash('Grupo atualizado com sucesso!')
            return redirect(url_for('grupo_bp.lista_grupos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar grupo: {e}')
            return render_template('partials/grupo/form_grupo.html', grupo=grupo, naturezas=naturezas)

    return render_template('partials/grupo/form_grupo.html', grupo=grupo, naturezas=naturezas)


# ------------------------------ EXCLUIR GRUPO ------------------------------ #
@grupo_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_grupo(id):
    grupo = Grupo.query.get_or_404(id)
    try:
        db.session.delete(grupo)
        db.session.commit()
        flash('Grupo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir grupo: {e}', 'danger')
    return redirect(url_for('grupo_bp.lista_grupos'))



