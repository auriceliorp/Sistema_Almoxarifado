from flask import Blueprint, jsonify
from flask_login import login_required
from models import Tarefa, Item

# Primeiro, criar o blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Depois, definir as rotas
@api_bp.route('/itens')
def get_itens():
    itens = Item.query.all()
    return jsonify([{
        'id': item.id,
        'nome': f"{item.codigo_sap} - {item.nome}",
        'valor_unitario': float(item.valor_unitario)
    } for item in itens])

@api_bp.route('/tarefas/<int:tarefa_id>/detalhes')
@login_required
def get_detalhes_tarefa(tarefa_id):
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        
        return jsonify({
            'id': tarefa.id,
            'titulo': tarefa.titulo,
            'resumo': tarefa.resumo,
            'status': tarefa.status,
            'prioridade': tarefa.prioridade,
            'numero_sei': tarefa.numero_sei,
            'data_inicio': tarefa.data_inicio.isoformat() if tarefa.data_inicio else None,
            'data_termino': tarefa.data_termino.isoformat() if tarefa.data_termino else None,
            'data_conclusao': tarefa.data_conclusao.isoformat() if tarefa.data_conclusao else None,
            'categoria': {
                'id': tarefa.categoria.id,
                'nome': tarefa.categoria.nome
            } if tarefa.categoria else None,
            'origem': {
                'id': tarefa.origem.id,
                'nome': tarefa.origem.nome
            } if tarefa.origem else None,
            'unidade_local': {
                'id': tarefa.unidade_local.id,
                'descricao': tarefa.unidade_local.descricao
            } if tarefa.unidade_local else None,
            'responsavel': {
                'id': tarefa.responsavel.id,
                'nome': tarefa.responsavel.nome
            } if tarefa.responsavel else None,
            'solicitante': {
                'id': tarefa.solicitante.id,
                'nome': tarefa.solicitante.nome
            } if tarefa.solicitante else None,
            'observacoes': tarefa.observacoes
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas/contadores')
def get_contadores():
    try:
        total = Tarefa.query.count()
        nao_iniciadas = Tarefa.query.filter_by(status='Não iniciada').count()
        em_execucao = Tarefa.query.filter_by(status='Em execução').count()
        suspensas = Tarefa.query.filter_by(status='Suspensa').count()
        concluidas = Tarefa.query.filter_by(status='Concluída').count()
        em_atraso = Tarefa.query.filter_by(status='Em atraso').count()
        
        return jsonify({
            'total': total,
            'nao_iniciadas': nao_iniciadas,
            'em_execucao': em_execucao,
            'suspensas': suspensas,
            'concluidas': concluidas,
            'em_atraso': em_atraso
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
