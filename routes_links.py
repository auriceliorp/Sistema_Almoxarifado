# routes_links.py
# Rotas para a seção de Links Úteis

from flask import Blueprint, render_template
from flask_login import login_required, current_user

# Criação do blueprint
links_bp = Blueprint('links_bp', __name__, url_prefix='/links')

# -------------------------- ROTA: Página de Links Úteis -------------------------- #
@links_bp.route('/')
@login_required
def lista_links():
    return render_template('links_uteis.html', usuario=current_user)
