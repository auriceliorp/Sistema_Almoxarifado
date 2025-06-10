from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.requisicao_service import RequisicaoService
from models import Item, Grupo  # Adicionado import do Grupo
from functools import wraps

requisicao_bp = Blueprint('requisicao_bp', __name__, url_prefix='/requisicao')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.perfil or current_user.perfil.nome != 'Administrador':
            flash('Acesso negado. Você precisa ser administrador para acessar esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@requisicao_bp.route('/consulta-estoque')
@login_required
def consulta_estoque():
    """Página para consulta de estoque e criação de requisição"""
    try:
        itens = Item.query.filter(Item.estoque_atual > 0).order_by(Item.nome).all()
        grupos = Grupo.query.order_by(Grupo.nome).all()  # Busca todos os grupos
        return render_template('almoxarifado/requisicao/consulta_estoque.html', 
                             itens=itens,
                             grupos=grupos)  # Passa os grupos para o template
    except Exception as e:
        flash(f'Erro ao carregar itens: {str(e)}', 'error')
        return redirect(url_for('index'))

@requisicao_bp.route('/nova', methods=['POST'])
@login_required
def nova_requisicao():
    """Cria uma nova requisição de material"""
    try:
        # Obter dados do formulário
        itens_ids = request.form.getlist('item_id[]')
        quantidades = request.form.getlist('quantidade[]')
        observacao = request.form.get('observacao', '')

        if not itens_ids:
            raise ValueError("É necessário incluir pelo menos um item")

        # Preparar lista de itens
        itens = []
        for item_id, qtd in zip(itens_ids, quantidades):
            if item_id and qtd:
                # Buscar item
                item = Item.query.get(item_id)
                if not item:
                    raise ValueError(f"Item {item_id} não encontrado")

                quantidade = int(qtd)
                if quantidade <= 0:
                    raise ValueError("Quantidade deve ser maior que zero")

                if item.estoque_atual < quantidade:
                    raise ValueError(f"Estoque insuficiente para o item {item.nome}")

                itens.append({
                    'id': item_id,
                    'nome': item.nome,
                    'quantidade': quantidade
                })

        # Criar requisição usando o serviço
        result = RequisicaoService.criar_requisicao(
            solicitante_id=current_user.id,
            observacao=observacao,
            itens=itens
        )

        if result['success']:
            flash('Requisição criada com sucesso!', 'success')
            return redirect(url_for('requisicao_bp.minhas_requisicoes'))
        else:
            flash(f'Erro ao criar requisição: {result["error"]}', 'error')
            return redirect(url_for('requisicao_bp.consulta_estoque'))

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('requisicao_bp.consulta_estoque'))
    except Exception as e:
        flash(f'Erro ao criar requisição: {str(e)}', 'error')
        return redirect(url_for('requisicao_bp.consulta_estoque'))

@requisicao_bp.route('/minhas')
@login_required
def minhas_requisicoes():
    """Lista as requisições do usuário atual"""
    try:
        result = RequisicaoService.listar_minhas_requisicoes(current_user.id)
        if result['success']:
            return render_template('almoxarifado/requisicao/minhas_requisicoes.html', 
                                requisicoes=result['requisicoes'])
        else:
            flash(f'Erro ao listar requisições: {result["error"]}', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Erro ao listar requisições: {str(e)}', 'error')
        return redirect(url_for('index'))

@requisicao_bp.route('/pendentes')
@login_required
@admin_required
def requisicoes_pendentes():
    """Lista as requisições pendentes (para o almoxarifado)"""
    try:
        result = RequisicaoService.listar_requisicoes_pendentes()
        if result['success']:
            return render_template('almoxarifado/requisicao/requisicoes_pendentes.html',
                                requisicoes=result['requisicoes'])
        else:
            flash(f'Erro ao listar requisições pendentes: {result["error"]}', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Erro ao listar requisições pendentes: {str(e)}', 'error')
        return redirect(url_for('index'))

@requisicao_bp.route('/<int:requisicao_id>/atender', methods=['POST'])
@login_required
@admin_required
def atender_requisicao(requisicao_id):
    """Atende uma requisição gerando uma saída de material"""
    try:
        result = RequisicaoService.atender_requisicao(requisicao_id, current_user.id)
        if result['success']:
            flash('Requisição atendida com sucesso!', 'success')
        else:
            flash(result['error'], 'error')
        return redirect(url_for('requisicao_bp.requisicoes_pendentes'))
    except Exception as e:
        flash(f'Erro ao atender requisição: {str(e)}', 'error')
        return redirect(url_for('requisicao_bp.requisicoes_pendentes'))

@requisicao_bp.route('/<int:requisicao_id>/detalhes')
@login_required
def detalhes_requisicao(requisicao_id):
    """Exibe os detalhes de uma requisição"""
    try:
        result = RequisicaoService.obter_detalhes_requisicao(requisicao_id)
        if result['success']:
            if not current_user.perfil or (current_user.perfil.nome != 'Administrador' and result['requisicao'].solicitante_id != current_user.id):
                flash('Você não tem permissão para visualizar esta requisição.', 'error')
                return redirect(url_for('index'))
            return render_template('almoxarifado/requisicao/detalhes_requisicao.html',
                                requisicao=result['requisicao'])
        else:
            flash(f'Erro ao carregar detalhes da requisição: {result["error"]}', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Erro ao carregar detalhes da requisição: {str(e)}', 'error')
        return redirect(url_for('index'))

@requisicao_bp.route('/<int:requisicao_id>/cancelar', methods=['POST'])
@login_required
def cancelar_requisicao(requisicao_id):
    """Cancela uma requisição pendente"""
    try:
        result = RequisicaoService.cancelar_requisicao(requisicao_id, current_user.id)
        if result['success']:
            flash('Requisição cancelada com sucesso!', 'success')
        else:
            flash(result['error'], 'error')
        return redirect(url_for('requisicao_bp.minhas_requisicoes'))
    except Exception as e:
        flash(f'Erro ao cancelar requisição: {str(e)}', 'error')
        return redirect(url_for('requisicao_bp.minhas_requisicoes'))

@requisicao_bp.route('/api/requisicao/<int:requisicao_id>')
@login_required
def api_detalhes_requisicao(requisicao_id):
    """API para obter detalhes da requisição em formato JSON"""
    try:
        result = RequisicaoService.obter_detalhes_requisicao(requisicao_id)
        if result['success']:
            if not current_user.perfil or (current_user.perfil.nome != 'Administrador' and result['requisicao'].solicitante_id != current_user.id):
                return jsonify({'error': 'Acesso negado'}), 403
            return jsonify({
                'success': True,
                'requisicao': {
                    'id': result['requisicao'].id,
                    'data_requisicao': result['requisicao'].data_requisicao.isoformat(),
                    'status': result['requisicao'].status,
                    'observacao': result['requisicao'].observacao,
                    'solicitante': {
                        'id': result['requisicao'].solicitante.id,
                        'nome': result['requisicao'].solicitante.nome
                    },
                    'itens': [{
                        'id': item.id,
                        'item_id': item.item_id,
                        'nome': item.item.nome,
                        'quantidade': item.quantidade
                    } for item in result['requisicao'].itens]
                }
            })
        else:
            return jsonify({'error': result['error']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
