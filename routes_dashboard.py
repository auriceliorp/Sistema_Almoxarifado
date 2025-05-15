# routes_dashboard.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Dados simulados para exibição no dashboard
    total_itens = 100
    entradas_mes = 25
    saidas_mes = 18
    requisicoes_pendentes = 7

    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai']
    dados_entrada = [10, 15, 5, 20, 8]
    dados_saida = [5, 8, 3, 10, 7]

    itens_baixo_estoque_labels = ['Papel A4', 'Álcool', 'Luvas', 'Caneta']
    itens_baixo_estoque_dados = [2, 1, 3, 1]

    return render_template(
        'dashboard.html',
        usuario=current_user,
        total_itens=total_itens,
        entradas_mes=entradas_mes,
        saidas_mes=saidas_mes,
        requisicoes_pendentes=requisicoes_pendentes,
        meses=meses,
        dados_entrada=dados_entrada,
        dados_saida=dados_saida,
        itens_baixo_estoque_labels=itens_baixo_estoque_labels,
        itens_baixo_estoque_dados=itens_baixo_estoque_dados
    )