from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Atividade
from utils.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

atividade_bp = Blueprint('atividade_bp', __name__, url_prefix='/atividade')

@atividade_bp.route('/lista')
@login_required
def lista_atividades():
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'ATIVA')
        
        query = Atividade.query
        
        if status_filter != 'TODAS':
            query = query.filter_by(status=status_filter)
            
        atividades = query.order_by(Atividade.data_cadastro.desc()).paginate(page=page, per_page=10)
        
        return render_template('atividade/lista.html', 
                             atividades=atividades,
                             status_filter=status_filter)
    except Exception as e:
        flash(f'Erro ao listar atividades: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@atividade_bp.route('/nova', methods=['GET', 'POST'])
@login_required
@admin_required
def nova_atividade():
    if request.method == 'POST':
        try:
            atividade = Atividade(
                numero=request.form['numero'],
                nome=request.form['nome'],
                descricao=request.form.get('descricao'),
                data_inicio=request.form.get('data_inicio'),
                data_fim=request.form.get('data_fim'),
                responsavel_id=request.form.get('responsavel_id')
            )
            
            db.session.add(atividade)
            db.session.commit()
            
            flash('Atividade cadastrada com sucesso!', 'success')
            return redirect(url_for('atividade_bp.lista_atividades'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar atividade: {str(e)}', 'error')
            
    return render_template('atividade/form.html')

@atividade_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_atividade(id):
    atividade = Atividade.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            atividade.numero = request.form['numero']
            atividade.nome = request.form['nome']
            atividade.descricao = request.form.get('descricao')
            atividade.data_inicio = request.form.get('data_inicio')
            atividade.data_fim = request.form.get('data_fim')
            atividade.responsavel_id = request.form.get('responsavel_id')
            
            db.session.commit()
            flash('Atividade atualizada com sucesso!', 'success')
            return redirect(url_for('atividade_bp.lista_atividades'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar atividade: {str(e)}', 'error')
    
    return render_template('atividade/form.html', atividade=atividade)

@atividade_bp.route('/api/buscar/<string:numero>')
@login_required
def buscar_atividade(numero):
    try:
        atividade = Atividade.query.filter_by(numero=numero, status='ATIVA').first()
        if atividade:
            return jsonify({
                'success': True,
                'id': atividade.id,
                'nome': atividade.nome,
                'responsavel': atividade.responsavel.nome if atividade.responsavel else None
            })
        return jsonify({'success': False, 'message': 'Atividade não encontrada'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}) 
