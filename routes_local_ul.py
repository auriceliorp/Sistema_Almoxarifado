# routes_local_ul.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Area, Setor

local_ul_bp = Blueprint('local_ul', __name__, url_prefix='/organizacao')

# --------- LOCAIS ---------
@local_ul_bp.route('/locais')
@login_required
def lista_locais():
    areas = Area.query.all()
    return render_template('lista_areas.html', areas=areas)

@local_ul_bp.route('/locais/novo', methods=['GET', 'POST'])
@login_required
def novo_local():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome do local é obrigatório.')
            return redirect(url_for('local_ul.novo_local'))
        db.session.add(Area(nome=nome))
        db.session.commit()
        flash('Local cadastrado com sucesso!')
        return redirect(url_for('local_ul.lista_locais'))
    return render_template('nova_area.html')

# --------- UNIDADES LOCAIS (UL) ---------
@local_ul_bp.route('/uls')
@login_required
def lista_uls():
    setores = Setor.query.all()
    return render_template('lista_setores.html', setores=setores)

@local_ul_bp.route('/uls/novo', methods=['GET', 'POST'])
@login_required
def nova_ul():
    if request.method == 'POST':
        nome = request.form.get('nome')
        codigo = request.form.get('codigo')
        if not nome or not codigo:
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('local_ul.nova_ul'))
        db.session.add(Setor(nome=nome, codigo=codigo))
        db.session.commit()
        flash('Unidade Local cadastrada com sucesso!')
        return redirect(url_for('local_ul.lista_uls'))
    return render_template('novo_setor.html')
