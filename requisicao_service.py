@staticmethod
def listar_requisicoes_atendidas():
    """Lista todas as requisições que foram atendidas"""
    try:
        # Busca requisições com status ATENDIDA e ordena por data de atendimento decrescente
        requisicoes = Requisicao.query.filter_by(status='ATENDIDA')\
            .order_by(Requisicao.data_atendimento.desc())\
            .all()
        
        # Para cada requisição, verifica se tem estoque suficiente para todos os itens
        for req in requisicoes:
            req.tem_estoque_suficiente = all(
                item.item.estoque_atual >= item.quantidade 
                for item in req.itens
            )
        
        return {
            'success': True,
            'requisicoes': requisicoes
        }
    except Exception as e:
        logger.error(f"Erro ao listar requisições atendidas: {str(e)}")
        return {
            'success': False,
            'error': f"Erro ao listar requisições atendidas: {str(e)}"
        }
