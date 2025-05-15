# routes_dashboard.py

@main.route('/dashboard')
@login_required
def dashboard():
    # Exemplos de dados fictícios - substitua por consultas reais
    total_itens = 142
    entradas_mes = 28
    saidas_mes = 19
    requisicoes_pendentes = 5

    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai']
    dados_entrada = [10, 20, 15, 30, 25]
    dados_saida = [5, 12, 10, 20, 18]

    itens_baixo_estoque_labels = ['Item A', 'Item B', 'Item C']
    itens_baixo_estoque_dados = [3, 1, 5]

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