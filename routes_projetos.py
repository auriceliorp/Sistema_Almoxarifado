from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, Tarefa, Usuario
from datetime import datetime
from extensoes import csrf

bp = Blueprint('tarefas', __name__, url_prefix='/tarefas')

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
@bp.route('/api/tarefas', methods=['GET'])
@login_required
def listar_tarefas():
    """Lista todas as tarefas com filtros opcionais."""
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
    return jsonify([{
        'id': t.id,
        'titulo': t.titulo,
        'descricao': t.descricao,
        'area': t.area,
        'prioridade': t.prioridade,
        'status': t.status,
        'responsavel': t.responsavel
    } for t in tarefas])

@bp.route('/api/tarefas', methods=['POST'])
@login_required
@csrf.exempt
def criar_tarefa():
    """Cria uma nova tarefa."""
    data = request.get_json()
    
    if not data or not data.get('titulo') or not data.get('area') or not data.get('prioridade'):
        return jsonify({'error': 'Dados inválidos'}), 400
        
    tarefa = Tarefa(
        titulo=data['titulo'],
        descricao=data.get('descricao', ''),
        area=data['area'],
        prioridade=data['prioridade'],
        status=data.get('status', 'A Fazer'),
        responsavel=data.get('responsavel'),
        data_criacao=datetime.utcnow()
    )
    
    try:
        db.session.add(tarefa)
        db.session.commit()
        
        return jsonify({
            'id': tarefa.id,
            'titulo': tarefa.titulo,
            'descricao': tarefa.descricao,
            'area': tarefa.area,
            'prioridade': tarefa.prioridade,
            'status': tarefa.status,
            'responsavel': tarefa.responsavel
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/tarefas/<int:tarefa_id>', methods=['PUT'])
@login_required
@csrf.exempt
def atualizar_tarefa(tarefa_id):
    """Atualiza uma tarefa existente."""
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    data = request.get_json()
    
    if 'status' in data:
        tarefa.status = data['status']
        if data['status'] == 'Concluído' and not tarefa.data_conclusao:
            tarefa.data_conclusao = datetime.utcnow()
        elif data['status'] != 'Concluído':
            tarefa.data_conclusao = None
    
    try:
        db.session.commit()
        return jsonify({'message': 'Tarefa atualizada com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/tarefas/<int:tarefa_id>', methods=['DELETE'])
@login_required
@csrf.exempt
def deletar_tarefa(tarefa_id):
    """Deleta uma tarefa."""
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    try:
        db.session.delete(tarefa)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Rotas da API
api_bp = Blueprint('tarefas_api', __name__, url_prefix='/api/tarefas')

@api_bp.route('/', methods=['GET'])
@login_required
def get_tarefas():
    try:
        status = request.args.get('status', None)
        area = request.args.get('area', None)
        prioridade = request.args.get('prioridade', None)
        
        query = Tarefa.query
        
        if status:
            query = query.filter(Tarefa.status == status)
        if area:
            query = query.filter(Tarefa.area == area)
        if prioridade:
            query = query.filter(Tarefa.prioridade == prioridade)
            
        tarefas = query.all()
        return jsonify([tarefa.to_dict() for tarefa in tarefas])
    except Exception as e:
        print(f"Erro ao buscar tarefas: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/', methods=['POST'])
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
        
        return jsonify(tarefa.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar tarefa: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/<int:tarefa_id>', methods=['PUT'])
@login_required
def atualizar_tarefa_api(tarefa_id):
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        tarefa.titulo = data.get('titulo', tarefa.titulo)
        tarefa.descricao = data.get('descricao', tarefa.descricao)
        tarefa.area = data.get('area', tarefa.area)
        tarefa.prioridade = data.get('prioridade', tarefa.prioridade)
        tarefa.status = data.get('status', tarefa.status)
        tarefa.responsavel = data.get('responsavel', tarefa.responsavel)
        
        if data.get('status') == 'Concluído' and not tarefa.data_conclusao:
            tarefa.data_conclusao = datetime.utcnow()
        elif data.get('status') != 'Concluído':
            tarefa.data_conclusao = None
        
        db.session.commit()
        return jsonify(tarefa.to_dict())
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar tarefa: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/<int:tarefa_id>', methods=['DELETE'])
@login_required
def deletar_tarefa(tarefa_id):
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        db.session.delete(tarefa)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar tarefa: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500
