from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import Grupo, NaturezaDespesa

grupo_bp = Blueprint('grupo_bp', __name__, url_prefix='/grupo')

# Função auxiliar para checar se é uma requisição AJAX
def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ------------------------------ LISTAGEM ------------------------------ #
@grupo_bp.route('/')
@login_required
def lista_grupos():
    grupos = Grupo.query.order_by(Grupo.nome).all()
    if is_ajax():
        return render_template('partials/grupo/lista_grupo.html', grupos=grupos)
    return redirect(url_for('main.nd_grupos_ul'))  # fallback para a tela com abas


# ------------------------------ NOVO GRUPO ------------------------------ #
@grupo_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_grupo():
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        natureza_id = request.form.get('natureza_despesa_id')

        if not nome or not natureza_id:
            flash('Preencha todos os campos obrigatórios.')
            if is_ajax():
                return render_template('partials/grupo/form_grupo.html', grupo=None, naturezas=naturezas)
            return redirect(url_for('grupo_bp.novo_grupo'))

        novo = Grupo(nome=nome, natureza_despesa_id=natureza_id)
        db.session.add(novo)
        db.session.commit()
        flash('Grupo cadastrado com sucesso!')

        if is_ajax():
            grupos = Grupo.query.order_by(Grupo.nome).all()
            return render_template('partials/grupo/lista_grupo.html', grupos=grupos)
        return redirect(url_for('grupo_bp.lista_grupos'))

    # GET
    if is_ajax():
        return render_template('partials/grupo/form_grupo.html', grupo=None, naturezas=naturezas)
    return redirect(url_for('grupo_bp.lista_grupos'))


# ------------------------------ EDITAR GRUPO ------------------------------ #
@grupo_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_grupo(id):
    grupo = Grupo.query.get_or_404(id)
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        natureza_id = request.form.get('natureza_despesa_id')

        if not nome or not natureza_id:
            flash('Preencha todos os campos obrigatórios.')
            if is_ajax():
                return render_template('partials/grupo/form_grupo.html', grupo=grupo, naturezas=naturezas)
            return redirect(url_for('grupo_bp.editar_grupo', id=id))

        grupo.nome = nome
        grupo.natureza_despesa_id = natureza_id
        db.session.commit()
        flash('Grupo atualizado com sucesso!')

        if is_ajax():
            grupos = Grupo.query.order_by(Grupo.nome).all()
            return render_template('partials/grupo/lista_grupo.html', grupos=grupos)
        return redirect(url_for('grupo_bp.lista_grupos'))

    # GET
    if is_ajax():
        return render_template('partials/grupo/form_grupo.html', grupo=grupo, naturezas=naturezas)
    return redirect(url_for('grupo_bp.lista_grupos'))


# ------------------------------ EXCLUIR GRUPO ------------------------------ #
@grupo_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_grupo(id):
    grupo = Grupo.query.get_or_404(id)
    db.session.delete(grupo)
    db.session.commit()
    flash('Grupo excluído com sucesso!')

    if is_ajax():
        grupos = Grupo.query.order_by(Grupo.nome).all()
        return render_template('partials/grupo/lista_grupo.html', grupos=grupos)
    return redirect(url_for('grupo_bp.lista_grupos'))
