# routes_area_ul.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Local, UnidadeLocal, NaturezaDespesa, Grupo

# Criação do blueprint
area_ul_bp = Blueprint('area_ul_bp', __name__, url_prefix='/organizacao')

# ------------------------- ROTA: DASHBOARD ORGANIZAÇÃO ------------------------- #
@area_ul_bp.route('/')
@login_required
def dashboard_organizacao():
    """
    Rota principal do dashboard de organização administrativa.
    Carrega os dados para as abas:
    - Natureza de Despesa
    - Grupos
    - Áreas (Locais)
    - Unidades Locais
    """
    nds = NaturezaDespesa.query.all()
    grupos = Grupo.query.all()
    areas = Local.query.all()
    uls = UnidadeLocal.query.all()
    return render_template('organizacao/dashboard_organizacao.html',
                           nds=nds, grupos=grupos, areas=areas, uls=uls)