from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Usuario, AutorizacaoOperacao
from extensoes import db
from datetime import datetime
from utils.decorators import autorizador_required

autorizacao_bp = Blueprint('autorizacao', __name__, url_prefix='/autorizacao')

@autorizacao_bp.route('/pendentes')
@login_required
def lista_pendentes():
    # Se for autorizador, vê todas as pendentes
    if current_user.is_autorizador():
        autorizacoes = AutorizacaoOperacao.query.filter_by(status='PENDENTE').all()
    else:
        # Se não, vê apenas as suas solicitações
        autorizacoes = AutorizacaoOperacao.query.filter_by(
            solicitante_id=current_user.id
        ).order_by(AutorizacaoOperacao.data_solicitacao.desc()).all()
    
    return render_template(
        'autorizacao/lista_pendentes.html',
        autorizacoes=autorizacoes,
        is_autorizador=current_user.is_autorizador()
    )

@autorizacao_bp.route('/historico')
@login_required
def historico():
    # Se for autorizador ou admin, vê todo o histórico
    if current_user.is_autorizador() or current_user.is_admin():
        autorizacoes = AutorizacaoOperacao.query.filter(
            AutorizacaoOperacao.status != 'PENDENTE'
        ).order_by(AutorizacaoOperacao.data_autorizacao.desc()).all()
    else:
        # Se não, vê apenas seu histórico
        autorizacoes = AutorizacaoOperacao.query.filter(
            AutorizacaoOperacao.solicitante_id == current_user.id,
            AutorizacaoOperacao.status != 'PENDENTE'
        ).order_by(AutorizacaoOperacao.data_autorizacao.desc()).all()
    
    return render_template(
        'autorizacao/historico.html',
        autorizacoes=autorizacoes
    )

@autorizacao_bp.route('/autorizar/<int:id>', methods=['POST'])
@login_required
@autorizador_required
def autorizar(id):
    autorizacao = AutorizacaoOperacao.query.get_or_404(id)
    
    if autorizacao.status != 'PENDENTE':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('autorizacao.lista_pendentes'))
    
    acao = request.form.get('acao')
    justificativa = request.form.get('justificativa')
    
    if not justificativa:
        flash('É necessário fornecer uma justificativa.', 'warning')
        return redirect(url_for('autorizacao.lista_pendentes'))
    
    autorizacao.autorizador_id = current_user.id
    autorizacao.data_autorizacao = datetime.utcnow()
    autorizacao.justificativa = justificativa
    
    if acao == 'aprovar':
        autorizacao.status = 'APROVADA'
        flash('Solicitação aprovada com sucesso.', 'success')
    else:
        autorizacao.status = 'REJEITADA'
        flash('Solicitação rejeitada.', 'info')
    
    db.session.commit()
    return redirect(url_for('autorizacao.lista_pendentes'))

@autorizacao_bp.route('/detalhes/<int:id>')
@login_required
def detalhes(id):
    autorizacao = AutorizacaoOperacao.query.get_or_404(id)
    
    # Verifica se o usuário tem permissão para ver os detalhes
    if not (current_user.is_autorizador() or 
            current_user.id == autorizacao.solicitante_id or 
            current_user.is_admin()):
        flash('Você não tem permissão para ver estes detalhes.', 'danger')
        return redirect(url_for('main.home'))
    
    return render_template(
        'autorizacao/detalhes.html',
        autorizacao=autorizacao
    ) 
