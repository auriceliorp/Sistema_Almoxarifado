from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Publicacao, Usuario, Fornecedor
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

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
    query = Publicacao.query

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
@csrf_protect()
def nova_publicacao():
    if request.method == 'POST':
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

        # Se ambas as datas de vigência estiverem vazias, usa "A partir da Assinatura"
        if not vigencia_inicio and not vigencia_fim:
            vigencia = "A partir da Assinatura"
        else:
            vigencia = f"{vigencia_inicio} a {vigencia_fim}"

        # Processa seleções múltiplas
        partes_embrapa = request.form.getlist('partes_embrapa')
        partes_fornecedor = request.form.getlist('partes_fornecedor')
        signatarios_embrapa = request.form.getlist('signatarios_embrapa')
        signatarios_externos = request.form.getlist('signatarios_externos')

        # Validações básicas
        if not especie or not objeto or not data_assinatura:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('publicacao_bp.nova_publicacao'))

        # Cria nova publicação
        publicacao = Publicacao(
            especie=especie,
            objeto=objeto,
            contrato_saic=contrato_saic,
            modalidade_licitacao=modalidade_licitacao,
            fonte_recursos=fonte_recursos,
            valor_global=valor_global,
            data_assinatura=datetime.strptime(data_assinatura, '%Y-%m-%d').date(),
            vigencia=vigencia,
            partes_embrapa=partes_embrapa,
            partes_fornecedor=partes_fornecedor,
            signatarios_embrapa=signatarios_embrapa,
            signatarios_externos=signatarios_externos
        )

        try:
            db.session.add(publicacao)
            db.session.commit()
            flash('Publicação cadastrada com sucesso!', 'success')
            return redirect(url_for('publicacao_bp.listar'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar publicação. Por favor, tente novamente.', 'danger')
            print(f"Erro: {str(e)}")

    # GET: Renderiza o formulário
    usuarios = Usuario.query.all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html',
                         usuarios=usuarios,
                         fornecedores=fornecedores)

@bp.route('/publicacao/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@csrf_protect()
def editar_publicacao(id):
    publicacao = Publicacao.query.get_or_404(id)
    
    if request.method == 'POST':
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

        if not vigencia_inicio and not vigencia_fim:
            publicacao.vigencia = "A partir da Assinatura"
        else:
            publicacao.vigencia = f"{vigencia_inicio} a {vigencia_fim}"

        # Atualiza seleções múltiplas
        publicacao.partes_embrapa = request.form.getlist('partes_embrapa')
        publicacao.partes_fornecedor = request.form.getlist('partes_fornecedor')
        publicacao.signatarios_embrapa = request.form.getlist('signatarios_embrapa')
        publicacao.signatarios_externos = request.form.getlist('signatarios_externos')

        try:
            db.session.commit()
            flash('Publicação atualizada com sucesso!', 'success')
            return redirect(url_for('publicacao_bp.listar'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar publicação. Por favor, tente novamente.', 'danger')
            print(f"Erro: {str(e)}")

    # GET: Renderiza o formulário com os dados atuais
    usuarios = Usuario.query.all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html',
                         publicacao=publicacao,
                         usuarios=usuarios,
                         fornecedores=fornecedores)

@bp.route('/publicacao/<int:id>/excluir', methods=['POST'])
@login_required
@csrf_protect()
def excluir_publicacao(id):
    publicacao = Publicacao.query.get_or_404(id)
    try:
        db.session.delete(publicacao)
        db.session.commit()
        flash('Publicação excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir publicação. Por favor, tente novamente.', 'danger')
        print(f"Erro: {str(e)}")
    
    return redirect(url_for('publicacao_bp.listar'))
