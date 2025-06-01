from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Projeto, Usuario
from datetime import datetime
from extensoes import csrf

bp = Blueprint('projetos', __name__, url_prefix='/projetos')

@bp.route('/conteudo')
@login_required
def conteudo():
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('projetos/conteudo.html', usuarios=usuarios)

# Rotas da API
api_bp = Blueprint('projetos_api', __name__, url_prefix='/api/projetos')

@api_bp.route('/', methods=['GET'])
@login_required
def get_projetos():
    try:
        status = request.args.get('status', None)
        area = request.args.get('area', None)
        prioridade = request.args.get('prioridade', None)
        
        query = Projeto.query
        
        if status:
            query = query.filter(Projeto.status == status)
        if area:
            query = query.filter(Projeto.area == area)
        if prioridade:
            query = query.filter(Projeto.prioridade == prioridade)
            
        projetos = query.all()
        return jsonify([projeto.to_dict() for projeto in projetos])
    except Exception as e:
        print(f"Erro ao buscar projetos: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/', methods=['POST'])
@login_required
def criar_projeto():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        print(f"Dados recebidos: {data}")  # Log dos dados recebidos
            
        if not data.get('titulo'):
            return jsonify({'error': 'Título é obrigatório'}), 400
            
        projeto = Projeto(
            titulo=data['titulo'],
            descricao=data.get('descricao', ''),
            area=data.get('area', ''),
            prioridade=data.get('prioridade', 'Média'),
            status=data.get('status', 'A Fazer'),
            responsavel=data.get('responsavel', ''),
            data_criacao=datetime.utcnow()
        )
        
        print(f"Projeto a ser criado: {projeto}")  # Log do objeto antes de salvar
        
        db.session.add(projeto)
        db.session.commit()
        
        print(f"Projeto criado com ID: {projeto.id}")  # Log após salvar
        
        return jsonify(projeto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar projeto: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/<int:projeto_id>', methods=['PUT'])
@login_required
def atualizar_projeto(projeto_id):
    try:
        projeto = Projeto.query.get_or_404(projeto_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        projeto.titulo = data.get('titulo', projeto.titulo)
        projeto.descricao = data.get('descricao', projeto.descricao)
        projeto.area = data.get('area', projeto.area)
        projeto.prioridade = data.get('prioridade', projeto.prioridade)
        projeto.status = data.get('status', projeto.status)
        projeto.responsavel = data.get('responsavel', projeto.responsavel)
        
        if data.get('status') == 'Concluído' and not projeto.data_conclusao:
            projeto.data_conclusao = datetime.utcnow()
        elif data.get('status') != 'Concluído':
            projeto.data_conclusao = None
        
        db.session.commit()
        return jsonify(projeto.to_dict())
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar projeto: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500

@api_bp.route('/<int:projeto_id>', methods=['DELETE'])
@login_required
def deletar_projeto(projeto_id):
    try:
        projeto = Projeto.query.get_or_404(projeto_id)
        db.session.delete(projeto)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar projeto: {str(e)}")  # Log do erro
        return jsonify({'error': str(e)}), 500
