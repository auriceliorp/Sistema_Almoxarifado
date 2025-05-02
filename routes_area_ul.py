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
            return redirect(url_for('area_ul.novo_local'))
        db.session.add(Local(descricao=descricao))
        db.session.commit()
        flash('Local cadastrado com sucesso!')
        return redirect(url_for('area_ul.lista_locais'))
    return render_template('novo_local.html')

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
            return redirect(url_for('area_ul.novo_ul'))

        ul = UnidadeLocal(codigo=codigo, descricao=descricao, local_id=local_id)
        db.session.add(ul)
        db.session.commit()
        flash('UL cadastrada com sucesso!')
        return redirect(url_for('area_ul.lista_uls'))

    return render_template('novo_ul.html', locais=locais)
