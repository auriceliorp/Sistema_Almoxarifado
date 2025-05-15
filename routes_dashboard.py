routes_dashboard.py

Rotas para exibição do Dashboard do sistema

from flask import Blueprint, render_template from flask_login import login_required, current_user

Blueprint para dashboard

dashboard_bp = Blueprint('dashboard_bp', name, url_prefix='/dashboard')

Rota principal do dashboard

@dashboard_bp.route('/') @login_required def painel_dashboard(): return render_template('dashboard.html', usuario=current_user)

