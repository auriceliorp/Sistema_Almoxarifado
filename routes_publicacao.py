from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Publicacao, Usuario, Fornecedor
from datetime import datetime

bp = Blueprint('publicacoes', __name__)

@bp.route('/publicacoes')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    filtro = request.args.get('filtro', '')
    busca = request.args.get('busca', '')

    query = Publicacao.query.filter_by(excluido=False)

    # Aplicar filtros de busca
    if busca and filtro:
        if filtro == 'especie':
            query = query.filter(Publicacao.especie.ilike(f'%{busca}%'))
        elif filtro == 'contrato':
            query = query.filter(Publicacao.contrato_saic.ilike(f'%{busca}%'))
        elif filtro == 'modalidade':
            query = query.filter(Publicacao.modalidade_licitacao.ilike(f'%{busca}%'))

    # Ordenação e paginação
    publicacoes = query.order_by(Publicacao.data_assinatura.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template('publicacao/listar.html', 
                         publicacoes=publicacoes,
                         filtro=filtro,
                         busca=busca)

@bp.route('/publicacoes/nova', methods=['GET', 'POST'])
@login_required
def nova():
    if request.method == 'POST':
        try:
            # Dados básicos
            publicacao = Publicacao(
                especie=request.form['especie'],
                contrato_saic=request.form.get('contrato_saic') or 'Não Aplicável',
                objeto=request.form['objeto'],
                modalidade_licitacao=request.form.get('modalidade_licitacao') or 'Não se Aplica',
                fonte_recursos=request.form.get('fonte_recursos') or 'Não se Aplica',
                valor_global=request.form.get('valor_global') or 'Não Aplicável',
                data_assinatura=datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d')
            )
            
            # Vigência
            if request.form.get('vigencia_inicio'):
                publicacao.vigencia_inicio = datetime.strptime(request.form['vigencia_inicio'], '%Y-%m-%d')
            if request.form.get('vigencia_fim'):
                publicacao.vigencia_fim = datetime.strptime(request.form['vigencia_fim'], '%Y-%m-%d')
            
            # Partes e Signatários
            partes_embrapa = request.form.getlist('partes_embrapa')
            partes_fornecedor = request.form.getlist('partes_fornecedor')
            signatarios_embrapa = request.form.getlist('signatarios_embrapa')
            signatarios_externos = request.form.getlist('signatarios_externos')
            
            # Adiciona as partes
            for parte_id in partes_embrapa:
                usuario = Usuario.query.get(parte_id)
                if usuario:
                    publicacao.partes_embrapa.append(usuario)
                    
            for parte_id in partes_fornecedor:
                fornecedor = Fornecedor.query.get(parte_id)
                if fornecedor:
                    publicacao.partes_fornecedor.append(fornecedor)
            
            # Adiciona os signatários
            for sig_id in signatarios_embrapa:
                usuario = Usuario.query.get(sig_id)
                if usuario:
                    publicacao.signatarios_embrapa.append(usuario)
                    
            for sig_id in signatarios_externos:
                fornecedor = Fornecedor.query.get(sig_id)
                if fornecedor:
                    publicacao.signatarios_externos.append(fornecedor)
            
            db.session.add(publicacao)
            db.session.commit()
            
            flash('Publicação cadastrada com sucesso!', 'success')
            return redirect(url_for('publicacoes.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar publicação: {str(e)}', 'error')
    
    usuarios = Usuario.query.all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html', 
                         usuarios=usuarios, 
                         fornecedores=fornecedores)

@bp.route('/publicacoes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    publicacao = Publicacao.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Atualiza dados básicos
            publicacao.especie = request.form['especie']
            publicacao.contrato_saic = request.form.get('contrato_saic') or 'Não Aplicável'
            publicacao.objeto = request.form['objeto']
            publicacao.modalidade_licitacao = request.form.get('modalidade_licitacao') or 'Não se Aplica'
            publicacao.fonte_recursos = request.form.get('fonte_recursos') or 'Não se Aplica'
            publicacao.valor_global = request.form.get('valor_global') or 'Não Aplicável'
            publicacao.data_assinatura = datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d')
            
            # Atualiza vigência
            publicacao.vigencia_inicio = None
            publicacao.vigencia_fim = None
            if request.form.get('vigencia_inicio'):
                publicacao.vigencia_inicio = datetime.strptime(request.form['vigencia_inicio'], '%Y-%m-%d')
            if request.form.get('vigencia_fim'):
                publicacao.vigencia_fim = datetime.strptime(request.form['vigencia_fim'], '%Y-%m-%d')
            
            # Limpa relacionamentos existentes
            publicacao.partes_embrapa.clear()
            publicacao.partes_fornecedor.clear()
            publicacao.signatarios_embrapa.clear()
            publicacao.signatarios_externos.clear()
            
            # Atualiza partes e signatários
            for parte_id in request.form.getlist('partes_embrapa'):
                usuario = Usuario.query.get(parte_id)
                if usuario:
                    publicacao.partes_embrapa.append(usuario)
                    
            for parte_id in request.form.getlist('partes_fornecedor'):
                fornecedor = Fornecedor.query.get(parte_id)
                if fornecedor:
                    publicacao.partes_fornecedor.append(fornecedor)
            
            for sig_id in request.form.getlist('signatarios_embrapa'):
                usuario = Usuario.query.get(sig_id)
                if usuario:
                    publicacao.signatarios_embrapa.append(usuario)
                    
            for sig_id in request.form.getlist('signatarios_externos'):
                fornecedor = Fornecedor.query.get(sig_id)
                if fornecedor:
                    publicacao.signatarios_externos.append(fornecedor)
            
            db.session.commit()
            flash('Publicação atualizada com sucesso!', 'success')
            return redirect(url_for('publicacoes.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar publicação: {str(e)}', 'error')
    
    usuarios = Usuario.query.all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html', 
                         publicacao=publicacao,
                         usuarios=usuarios, 
                         fornecedores=fornecedores)

@bp.route('/publicacoes/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    publicacao = Publicacao.query.get_or_404(id)
    try:
        publicacao.excluido = True
        db.session.commit()
        flash('Publicação excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir publicação: {str(e)}', 'error')
    
    return redirect(url_for('publicacoes.listar'))
