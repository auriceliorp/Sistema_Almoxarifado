# routes_dashboard.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Dados fictícios para teste
    total_itens = 120
    entradas_mes = 35
    saidas_mes = 22
    requisicoes_pendentes = 8
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai']
    dados_entrada = [10, 15, 5, 20, 8]
    dados_saida = [5, 8, 3, 10, 7]
    itens_baixo_estoque_labels = ['Álcool', 'Luvas', 'Papel A4']
    itens_baixo_estoque_dados = [5, 2, 3]

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