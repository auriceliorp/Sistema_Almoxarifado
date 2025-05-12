from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import Grupo, NaturezaDespesa

grupo_bp = Blueprint('grupo_bp', __name__, url_prefix='/grupo')

@grupo_bp.route('/')
@login_required
def lista_grupos():
    grupos = Grupo.query.all()
    return render_template('lista_grupo.html', grupos=grupos)

@grupo_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_grupo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        natureza_id = request.form.get('natureza_despesa_id')

        if not nome or not natureza_id:
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('grupo_bp.novo_grupo'))

        novo = Grupo(nome=nome, natureza_despesa_id=natureza_id)
        db.session.add(novo)
        db.session.commit()
        flash('Grupo cadastrado com sucesso!')
        return redirect(url_for('grupo_bp.lista_grupos'))

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template('form_grupo.html', naturezas=naturezas)

@grupo_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_grupo(id):
    grupo = Grupo.query.get_or_404(id)
    if request.method == 'POST':
        grupo.nome = request.form.get('nome')
        grupo.natureza_despesa_id = request.form.get('natureza_despesa_id')

        if not grupo.nome or not grupo.natureza_despesa_id:
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('grupo_bp.editar_grupo', id=id))

        db.session.commit()
        flash('Grupo atualizado com sucesso!')
        return redirect(url_for('grupo_bp.lista_grupos'))

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template('form_grupo.html', grupo=grupo, naturezas=naturezas)

@grupo_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_grupo(id):
    grupo = Grupo.query.get_or_404(id)
    db.session.delete(grupo)
    db.session.commit()
    flash('Grupo excluído com sucesso!')
    return redirect(url_for('grupo_bp.lista_grupos'))
