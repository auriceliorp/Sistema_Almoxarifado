from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Publicacao, Usuario, Fornecedor
from datetime import datetime

bp = Blueprint('publicacao_bp', __name__)

@bp.route('/publicacoes')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Obtém parâmetros de filtro
    filtro = request.args.get('filtro', '')
    busca = request.args.get('busca', '')

    # Query base
    query = Publicacao.query.filter_by(excluido=False)

    # Aplica filtros se fornecidos
    if busca:
        if filtro == 'especie':
            query = query.filter(Publicacao.especie.ilike(f'%{busca}%'))
        elif filtro == 'objeto':
            query = query.filter(Publicacao.objeto.ilike(f'%{busca}%'))
        elif filtro == 'contrato':
            query = query.filter(Publicacao.contrato_saic.ilike(f'%{busca}%'))

    # Executa a query paginada
    publicacoes = query.order_by(Publicacao.data_assinatura.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('publicacao/listar.html', 
                         publicacoes=publicacoes,
                         filtro=filtro,
                         busca=busca)

@bp.route('/publicacao/nova', methods=['GET', 'POST'])
@login_required
def nova_publicacao():
    if request.method == 'POST':
        try:
            # Processa os dados do formulário
            especie = request.form.get('especie')
            objeto = request.form.get('objeto')
            contrato_saic = request.form.get('contrato_saic') or "Não Aplicável"
            modalidade_licitacao = request.form.get('modalidade_licitacao') or "Não se Aplica"
            fonte_recursos = request.form.get('fonte_recursos') or "Não se Aplica"
            valor_global = request.form.get('valor_global') or "Não Aplicável"
            
            # Processa datas
            data_assinatura = request.form.get('data_assinatura')
            vigencia_inicio = request.form.get('vigencia_inicio')
            vigencia_fim = request.form.get('vigencia_fim')

            # Validações básicas
            if not especie or not objeto or not data_assinatura:
                flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
                return redirect(url_for('publicacao_bp.nova_publicacao'))

            # Converte as datas
            data_assinatura = datetime.strptime(data_assinatura, '%Y-%m-%d').date()
            vigencia_inicio = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date() if vigencia_inicio else None
            vigencia_fim = datetime.strptime(vigencia_fim, '%Y-%m-%d').date() if vigencia_fim else None

            # Busca os objetos relacionados
            partes_embrapa = Usuario.query.filter(Usuario.id.in_(request.form.getlist('partes_embrapa'))).all()
            partes_fornecedor = Fornecedor.query.filter(Fornecedor.id.in_(request.form.getlist('partes_fornecedor'))).all()
            signatarios_embrapa = Usuario.query.filter(Usuario.id.in_(request.form.getlist('signatarios_embrapa'))).all()
            signatarios_externos = Fornecedor.query.filter(Fornecedor.id.in_(request.form.getlist('signatarios_externos'))).all()

            # Cria nova publicação
            publicacao = Publicacao(
                especie=especie,
                objeto=objeto,
                contrato_saic=contrato_saic,
                modalidade_licitacao=modalidade_licitacao,
                fonte_recursos=fonte_recursos,
                valor_global=valor_global,
                data_assinatura=data_assinatura,
                vigencia_inicio=vigencia_inicio,
                vigencia_fim=vigencia_fim
            )

            # Atribui os relacionamentos
            publicacao.partes_embrapa = partes_embrapa
            publicacao.partes_fornecedor = partes_fornecedor
            publicacao.signatarios_embrapa = signatarios_embrapa
            publicacao.signatarios_externos = signatarios_externos

            db.session.add(publicacao)
            db.session.commit()
            flash('Publicação cadastrada com sucesso!', 'success')
            return redirect(url_for('publicacao_bp.listar'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar publicação. Por favor, tente novamente.', 'danger')
            print(f"Erro: {str(e)}")
            return redirect(url_for('publicacao_bp.nova_publicacao'))

    # GET: Renderiza o formulário
    usuarios = Usuario.query.filter_by(ativo=True).all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html',
                         usuarios=usuarios,
                         fornecedores=fornecedores)

@bp.route('/publicacao/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_publicacao(id):
    publicacao = Publicacao.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Atualiza os dados da publicação
            publicacao.especie = request.form.get('especie')
            publicacao.objeto = request.form.get('objeto')
            publicacao.contrato_saic = request.form.get('contrato_saic') or "Não Aplicável"
            publicacao.modalidade_licitacao = request.form.get('modalidade_licitacao') or "Não se Aplica"
            publicacao.fonte_recursos = request.form.get('fonte_recursos') or "Não se Aplica"
            publicacao.valor_global = request.form.get('valor_global') or "Não Aplicável"
            
            # Processa datas
            data_assinatura = request.form.get('data_assinatura')
            if not data_assinatura:
                flash('A data de assinatura é obrigatória.', 'danger')
                return redirect(url_for('publicacao_bp.editar_publicacao', id=id))

            publicacao.data_assinatura = datetime.strptime(data_assinatura, '%Y-%m-%d').date()
            
            vigencia_inicio = request.form.get('vigencia_inicio')
            vigencia_fim = request.form.get('vigencia_fim')
            
            publicacao.vigencia_inicio = datetime.strptime(vigencia_inicio, '%Y-%m-%d').date() if vigencia_inicio else None
            publicacao.vigencia_fim = datetime.strptime(vigencia_fim, '%Y-%m-%d').date() if vigencia_fim else None

            # Atualiza os relacionamentos
            partes_embrapa = Usuario.query.filter(Usuario.id.in_(request.form.getlist('partes_embrapa'))).all()
            partes_fornecedor = Fornecedor.query.filter(Fornecedor.id.in_(request.form.getlist('partes_fornecedor'))).all()
            signatarios_embrapa = Usuario.query.filter(Usuario.id.in_(request.form.getlist('signatarios_embrapa'))).all()
            signatarios_externos = Fornecedor.query.filter(Fornecedor.id.in_(request.form.getlist('signatarios_externos'))).all()

            publicacao.partes_embrapa = partes_embrapa
            publicacao.partes_fornecedor = partes_fornecedor
            publicacao.signatarios_embrapa = signatarios_embrapa
            publicacao.signatarios_externos = signatarios_externos

            db.session.commit()
            flash('Publicação atualizada com sucesso!', 'success')
            return redirect(url_for('publicacao_bp.listar'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar publicação. Por favor, tente novamente.', 'danger')
            print(f"Erro: {str(e)}")
            return redirect(url_for('publicacao_bp.editar_publicacao', id=id))

    # GET: Renderiza o formulário com os dados atuais
    usuarios = Usuario.query.filter_by(ativo=True).all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html',
                         publicacao=publicacao,
                         usuarios=usuarios,
                         fornecedores=fornecedores)

@bp.route('/publicacao/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_publicacao(id):
    publicacao = Publicacao.query.get_or_404(id)
    try:
        # Exclusão lógica
        publicacao.excluido = True
        db.session.commit()
        flash('Publicação excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir publicação. Por favor, tente novamente.', 'danger')
        print(f"Erro: {str(e)}")
    
    return redirect(url_for('publicacao_bp.listar'))
