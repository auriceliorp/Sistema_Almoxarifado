from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models import db, Projeto
from datetime import datetime
from flask_login import login_required, current_user

bp = Blueprint('projetos', __name__)

@bp.route('/projetos')
@login_required
def index():
    return render_template('projetos/index.html')

@bp.route('/api/projetos', methods=['GET'])
@login_required
def get_projetos():
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

@bp.route('/api/projetos', methods=['POST'])
@login_required
def criar_projeto():
    data = request.json
    
    projeto = Projeto(
        titulo=data['titulo'],
        descricao=data.get('descricao', ''),
        area=data.get('area', ''),
        prioridade=data.get('prioridade', 'Média'),
        status='A Fazer',
        responsavel=data.get('responsavel', ''),
        data_criacao=datetime.utcnow()
    )
    
    db.session.add(projeto)
    db.session.commit()
    
    return jsonify(projeto.to_dict()), 201

@bp.route('/api/projetos/<int:projeto_id>', methods=['PUT'])
@login_required
def atualizar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    data = request.json
    
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

@bp.route('/api/projetos/<int:projeto_id>', methods=['DELETE'])
@login_required
def deletar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    db.session.delete(projeto)
    db.session.commit()
    return '', 204 
