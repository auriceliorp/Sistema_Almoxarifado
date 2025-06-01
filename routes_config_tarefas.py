from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required
from models import db, CategoriaTarefa, OrigemTarefa
from datetime import datetime

bp = Blueprint('config_tarefas', __name__, url_prefix='/config/tarefas')

# Rotas para Categorias
@bp.route('/categorias')
@login_required
def lista_categorias():
    """Lista todas as categorias de tarefas."""
    categorias = CategoriaTarefa.query.all()
    return render_template('config_tarefas/lista_categorias.html', categorias=categorias)

@bp.route('/categorias/nova', methods=['GET', 'POST'])
@login_required
def nova_categoria():
    """Cria uma nova categoria de tarefa."""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            
            if not nome:
                flash('Nome é obrigatório.', 'error')
                return redirect(url_for('config_tarefas.nova_categoria'))
            
            categoria = CategoriaTarefa(
                nome=nome,
                descricao=descricao
            )
            
            db.session.add(categoria)
            db.session.commit()
            
            flash('Categoria criada com sucesso!', 'success')
            return redirect(url_for('config_tarefas.lista_categorias'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar categoria: {str(e)}', 'error')
            return redirect(url_for('config_tarefas.nova_categoria'))
            
    return render_template('config_tarefas/form_categoria.html')

@bp.route('/categorias/editar/<int:categoria_id>', methods=['GET', 'POST'])
@login_required
def editar_categoria(categoria_id):
    """Edita uma categoria existente."""
    categoria = CategoriaTarefa.query.get_or_404(categoria_id)
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            
            if not nome:
                flash('Nome é obrigatório.', 'error')
                return redirect(url_for('config_tarefas.editar_categoria', categoria_id=categoria_id))
            
            categoria.nome = nome
            categoria.descricao = descricao
            
            db.session.commit()
            
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('config_tarefas.lista_categorias'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar categoria: {str(e)}', 'error')
            return redirect(url_for('config_tarefas.editar_categoria', categoria_id=categoria_id))
            
    return render_template('config_tarefas/form_categoria.html', categoria=categoria)

# Rotas para Origens
@bp.route('/origens')
@login_required
def lista_origens():
    """Lista todas as origens de tarefas."""
    origens = OrigemTarefa.query.all()
    return render_template('config_tarefas/lista_origens.html', origens=origens)

@bp.route('/origens/nova', methods=['GET', 'POST'])
@login_required
def nova_origem():
    """Cria uma nova origem de tarefa."""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            
            if not nome:
                flash('Nome é obrigatório.', 'error')
                return redirect(url_for('config_tarefas.nova_origem'))
            
            origem = OrigemTarefa(
                nome=nome,
                descricao=descricao
            )
            
            db.session.add(origem)
            db.session.commit()
            
            flash('Origem criada com sucesso!', 'success')
            return redirect(url_for('config_tarefas.lista_origens'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar origem: {str(e)}', 'error')
            return redirect(url_for('config_tarefas.nova_origem'))
            
    return render_template('config_tarefas/form_origem.html')

@bp.route('/origens/editar/<int:origem_id>', methods=['GET', 'POST'])
@login_required
def editar_origem(origem_id):
    """Edita uma origem existente."""
    origem = OrigemTarefa.query.get_or_404(origem_id)
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            
            if not nome:
                flash('Nome é obrigatório.', 'error')
                return redirect(url_for('config_tarefas.editar_origem', origem_id=origem_id))
            
            origem.nome = nome
            origem.descricao = descricao
            
            db.session.commit()
            
            flash('Origem atualizada com sucesso!', 'success')
            return redirect(url_for('config_tarefas.lista_origens'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar origem: {str(e)}', 'error')
            return redirect(url_for('config_tarefas.editar_origem', origem_id=origem_id))
            
    return render_template('config_tarefas/form_origem.html', origem=origem)

# API Routes
@bp.route('/api/categorias')
@login_required
def get_categorias():
    """Retorna todas as categorias em formato JSON."""
    categorias = CategoriaTarefa.query.all()
    return jsonify([{
        'id': c.id,
        'nome': c.nome,
        'descricao': c.descricao
    } for c in categorias])

@bp.route('/api/origens')
@login_required
def get_origens():
    """Retorna todas as origens em formato JSON."""
    origens = OrigemTarefa.query.all()
    return jsonify([{
        'id': o.id,
        'nome': o.nome,
        'descricao': o.descricao
    } for o in origens]) 
