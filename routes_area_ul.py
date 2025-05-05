# routes_area_ul.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Local, UnidadeLocal

area_ul_bp = Blueprint('area_ul_bp', __name__, url_prefix='/organizacao')

# ROTAS DE LOCAL
@area_ul_bp.route('/locais')
@login_required
def lista_locais():
    locais = Local.query.all()
    return render_template('lista_locais.html', locais=locais)

@area_ul_bp.route('/locais/novo', methods=['GET', 'POST'])
@login_required
def novo_local():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        if not descricao:
            flash('Descrição é obrigatória.')
            return redirect(url_for('area_ul_bp.novo_local'))
        db.session.add(Local(descricao=descricao))
        db.session.commit()
        flash('Local cadastrado com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('novo_local.html')

@area_ul_bp.route('/locais/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_local(id):
    local = Local.query.get_or_404(id)
    if request.method == 'POST':
        local.descricao = request.form.get('descricao')
        db.session.commit()
        flash('Local atualizado com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('novo_local.html', local=local)

@area_ul_bp.route('/locais/excluir/<int:id>', methods=['GET'])
@login_required
def excluir_local(id):
    local = Local.query.get_or_404(id)
    db.session.delete(local)
    db.session.commit()
    flash('Local excluído com sucesso!')
    return redirect(url_for('area_ul_bp.lista_locais'))

# ROTAS DE UL
@area_ul_bp.route('/uls')
@login_required
def lista_uls():
    uls = UnidadeLocal.query.all()
    return render_template('lista_uls.html', uls=uls)

@area_ul_bp.route('/uls/novo', methods=['GET', 'POST'])
@login_required
def novo_ul():
    locais = Local.query.all()
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')
        local_id = request.form.get('local_id')

        if not (codigo and descricao and local_id):
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('area_ul_bp.novo_ul'))

        ul = UnidadeLocal(codigo=codigo, descricao=descricao, local_id=local_id)
        db.session.add(ul)
        db.session.commit()
        flash('UL cadastrada com sucesso!')
        return redirect(url_for('area_ul_bp.lista_uls'))

    return render_template('novo_ul.html', locais=locais)

@area_ul_bp.route('/uls/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ul(id):
    ul = UnidadeLocal.query.get_or_404(id)
    locais = Local.query.all()
    if request.method == 'POST':
        ul.codigo = request.form.get('codigo')
        ul.descricao = request.form.get('descricao')
        ul.local_id = request.form.get('local_id')
        db.session.commit()
        flash('UL atualizada com sucesso!')
        return redirect(url_for('area_ul_bp.lista_uls'))
    return render_template('novo_ul.html', ul=ul, locais=locais)

@area_ul_bp.route('/uls/excluir/<int:id>', methods=['GET'])
@login_required
def excluir_ul(id):
    ul = UnidadeLocal.query.get_or_404(id)
    db.session.delete(ul)
    db.session.commit()
    flash('UL excluída com sucesso!')
    return redirect(url_for('area_ul_bp.lista_uls'))
