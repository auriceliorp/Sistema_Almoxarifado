from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import UnidadeLocal, Local

area_ul_bp = Blueprint('area_ul_bp', __name__, url_prefix='/ul')

# Função auxiliar para identificar requisições AJAX
def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ------------------------------ LISTAGEM ------------------------------ #
@area_ul_bp.route('/')
@login_required
def lista_ul():
    uls = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all()
    if is_ajax():
        return render_template('partials/ul/lista_ul.html', uls=uls)
    return redirect(url_for('main.nd_grupos_ul'))


# ------------------------------ NOVA UL ------------------------------ #
@area_ul_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def nova_ul():
    locais = Local.query.order_by(Local.descricao).all()

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')
        local_id = request.form.get('local_id')

        if not codigo or not descricao or not local_id:
            flash('Preencha todos os campos obrigatórios.')
            if is_ajax():
                return render_template('partials/ul/form_ul.html', ul=None, locais=locais)
            return redirect(url_for('area_ul_bp.nova_ul'))

        nova = UnidadeLocal(codigo=codigo, descricao=descricao, local_id=local_id)
        db.session.add(nova)
        db.session.commit()
        flash('Unidade Local cadastrada com sucesso!')

        if is_ajax():
            uls = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all()
            return render_template('partials/ul/lista_ul.html', uls=uls)
        return redirect(url_for('area_ul_bp.lista_ul'))

    if is_ajax():
        return render_template('partials/ul/form_ul.html', ul=None, locais=locais)
    return redirect(url_for('area_ul_bp.lista_ul'))


# ------------------------------ EDITAR UL ------------------------------ #
@area_ul_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ul(id):
    ul = UnidadeLocal.query.get_or_404(id)
    locais = Local.query.order_by(Local.descricao).all()

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')
        local_id = request.form.get('local_id')

        if not codigo or not descricao or not local_id:
            flash('Preencha todos os campos obrigatórios.')
            if is_ajax():
                return render_template('partials/ul/form_ul.html', ul=ul, locais=locais)
            return redirect(url_for('area_ul_bp.editar_ul', id=id))

        ul.codigo = codigo
        ul.descricao = descricao
        ul.local_id = local_id
        db.session.commit()
        flash('Unidade Local atualizada com sucesso!')

        if is_ajax():
            uls = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all()
            return render_template('partials/ul/lista_ul.html', uls=uls)
        return redirect(url_for('area_ul_bp.lista_ul'))

    if is_ajax():
        return render_template('partials/ul/form_ul.html', ul=ul, locais=locais)
    return redirect(url_for('area_ul_bp.lista_ul'))


# ------------------------------ EXCLUIR UL ------------------------------ #
@area_ul_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_ul(id):
    ul = UnidadeLocal.query.get_or_404(id)
    db.session.delete(ul)
    db.session.commit()
    flash('Unidade Local excluída com sucesso!')

    if is_ajax():
        uls = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all()
        return render_template('partials/ul/lista_ul.html', uls=uls)
    return redirect(url_for('area_ul_bp.lista_ul'))
