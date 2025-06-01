from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Tarefa, Usuario
from datetime import datetime
from extensoes import csrf

bp = Blueprint('tarefas', __name__, url_prefix='/tarefas')
api_bp = Blueprint('tarefas_api', __name__, url_prefix='/api')

@bp.route('/')
@login_required
def lista_tarefas():
    """Renderiza a página principal de tarefas."""
    # Busca estatísticas
    total_tarefas = Tarefa.query.count()
    tarefas_em_progresso = Tarefa.query.filter_by(status='Em Progresso').count()
    tarefas_concluidas = Tarefa.query.filter_by(status='Concluído').count()
    total_responsaveis = db.session.query(Tarefa.responsavel).distinct().count()

    # Busca usuários para o select de responsável
    usuarios = Usuario.query.all()

    return render_template('tarefas/lista_tarefas.html',
                         total_tarefas=total_tarefas,
                         tarefas_em_progresso=tarefas_em_progresso,
                         tarefas_concluidas=tarefas_concluidas,
                         total_responsaveis=total_responsaveis,
                         usuarios=usuarios)

@bp.route('/nova')
@login_required
def nova_tarefa():
    """Renderiza o formulário de nova tarefa."""
    usuarios = Usuario.query.all()
    return render_template('tarefas/nova_tarefa.html', usuarios=usuarios)

# Rotas da API
@api_bp.route('/tarefas', methods=['GET'])
@login_required
def get_tarefas():
    try:
        area = request.args.get('area')
        prioridade = request.args.get('prioridade')
        responsavel = request.args.get('responsavel')
        
        query = Tarefa.query
        
        if area:
            query = query.filter_by(area=area)
        if prioridade:
            query = query.filter_by(prioridade=prioridade)
        if responsavel:
            query = query.filter_by(responsavel=responsavel)
            
        tarefas = query.all()
        return jsonify([tarefa.to_dict() for tarefa in tarefas])
    except Exception as e:
        print(f"Erro ao buscar tarefas: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas', methods=['POST'])
@login_required
def criar_tarefa_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        print(f"Dados recebidos: {data}")  # Log dos dados recebidos
            
        if not data.get('titulo'):
            return jsonify({'error': 'Título é obrigatório'}), 400
            
        tarefa = Tarefa(
            titulo=data['titulo'],
            descricao=data.get('descricao', ''),
            area=data.get('area', ''),
            prioridade=data.get('prioridade', 'Média'),
            status=data.get('status', 'A Fazer'),
            responsavel=data.get('responsavel', ''),
            data_criacao=datetime.utcnow()
        )
        
        print(f"Tarefa a ser criada: {tarefa}")  # Log do objeto antes de salvar
        
        db.session.add(tarefa)
        db.session.commit()
        
        print(f"Tarefa criada com ID: {tarefa.id}")  # Log após salvar
        
        return jsonify({
            'message': 'Tarefa criada com sucesso',
            'data': tarefa.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar tarefa: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas/<int:tarefa_id>', methods=['PUT'])
@login_required
def atualizar_tarefa_api(tarefa_id):
    """Atualiza uma tarefa existente."""
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        data = request.get_json()
        
        if 'status' in data:
            tarefa.status = data['status']
            if data['status'] == 'Concluído' and not tarefa.data_conclusao:
                tarefa.data_conclusao = datetime.utcnow()
            elif data['status'] != 'Concluído':
                tarefa.data_conclusao = None
        
        db.session.commit()
        return jsonify(tarefa.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas/<int:tarefa_id>', methods=['DELETE'])
@login_required
def deletar_tarefa_api(tarefa_id):
    """Deleta uma tarefa."""
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        db.session.delete(tarefa)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 
