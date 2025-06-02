from flask import Blueprint, jsonify
from models import Tarefa

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/tarefas/<int:tarefa_id>/detalhes')
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
            'data_fim': tarefa.data_fim.isoformat() if tarefa.data_fim else None,
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
            'criado_por': {
                'id': tarefa.criado_por.id,
                'nome': tarefa.criado_por.nome
            } if tarefa.criado_por else None,
            'observacoes': tarefa.observacoes
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/tarefas/contadores')
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
