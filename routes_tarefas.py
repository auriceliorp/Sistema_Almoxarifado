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

@bp.route('/editar/<int:tarefa_id>')
@login_required
def editar_tarefa(tarefa_id):
    """Renderiza o formulário de edição de tarefa."""
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    usuarios = Usuario.query.all()
    return render_template('tarefas/editar_tarefa.html', tarefa=tarefa, usuarios=usuarios)

# Rotas da API
@api_bp.route('/tarefas', methods=['GET'])
@login_required
def get_tarefas():
    try:
        area = request.args.get('area')
        prioridade = request.args.get('prioridade')
        status = request.args.get('status')
        responsavel = request.args.get('responsavel')
        
        query = Tarefa.query
        
        if area:
            query = query.filter_by(area=area)
        if prioridade:
            query = query.filter_by(prioridade=prioridade)
        if status:
            query = query.filter_by(status=status)
        if responsavel:
            query = query.filter_by(responsavel=responsavel)
            
        tarefas = query.all()
        return jsonify([tarefa.to_dict() for tarefa in tarefas])
    except Exception as e:
        print(f"Erro ao buscar tarefas: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas', methods=['POST'])
@login_required
def criar_tarefa():
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
def atualizar_tarefa(tarefa_id):
    """Atualiza uma tarefa existente."""
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        data = request.get_json()
        
        # Atualiza os campos básicos se fornecidos
        if 'titulo' in data:
            tarefa.titulo = data['titulo']
        if 'descricao' in data:
            tarefa.descricao = data['descricao']
        if 'area' in data:
            tarefa.area = data['area']
        if 'prioridade' in data:
            tarefa.prioridade = data['prioridade']
        if 'responsavel' in data:
            tarefa.responsavel = data['responsavel']
        
        # Atualiza o status e a data de conclusão
        if 'status' in data:
            old_status = tarefa.status
            tarefa.status = data['status']
            
            # Se a tarefa foi concluída agora, adiciona a data de conclusão
            if data['status'] == 'Concluído' and old_status != 'Concluído':
                tarefa.data_conclusao = datetime.utcnow()
            # Se a tarefa foi movida de Concluído para outro status, remove a data de conclusão
            elif data['status'] != 'Concluído' and old_status == 'Concluído':
                tarefa.data_conclusao = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa atualizada com sucesso',
            'data': tarefa.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar tarefa: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas/<int:tarefa_id>', methods=['DELETE'])
@login_required
def deletar_tarefa(tarefa_id):
    """Deleta uma tarefa."""
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        db.session.delete(tarefa)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/<int:tarefa_id>', methods=['DELETE'])
@login_required
def excluir_tarefa(tarefa_id):
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        db.session.delete(tarefa)
        db.session.commit()
        return jsonify({'message': 'Tarefa excluída com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir tarefa: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500
