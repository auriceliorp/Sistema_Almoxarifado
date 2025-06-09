# routes_area_setor.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import Area, Setor

area_setor_bp = Blueprint('area_setor', __name__, url_prefix='/organizacao')

# --------- AREAS ---------
@area_setor_bp.route('/areas')
@login_required
def lista_areas():
    areas = Area.query.all()
    return render_template('lista_areas.html', areas=areas)

@area_setor_bp.route('/areas/novo', methods=['GET', 'POST'])
@login_required
def nova_area():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome da área é obrigatório.')
            return redirect(url_for('area_setor.nova_area'))
        db.session.add(Area(nome=nome))
        db.session.commit()
        flash('Área cadastrada com sucesso!')
        return redirect(url_for('area_setor.lista_areas'))
    return render_template('nova_area.html')

# --------- SETORES ---------
@area_setor_bp.route('/setores')
@login_required
def lista_setores():
    setores = Setor.query.all()
    return render_template('lista_setores.html', setores=setores)

@area_setor_bp.route('/setores/novo', methods=['GET', 'POST'])
@login_required
def novo_setor():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome do setor é obrigatório.')
            return redirect(url_for('area_setor.novo_setor'))
        db.session.add(Setor(nome=nome))
        db.session.commit()
        flash('Setor cadastrado com sucesso!')
        return redirect(url_for('area_setor.lista_setores'))
    return render_template('novo_setor.html')
