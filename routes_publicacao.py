from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Publicacao, Usuario, Fornecedor, Tarefa
from datetime import datetime

publicacao_bp = Blueprint('publicacao_bp', __name__)

def criar_tarefa_publicacao(publicacao):
    """Cria uma tarefa automaticamente a partir de uma publicação."""
    titulo = f"Publicação - {publicacao.especie}"
    resumo = f"""
    Objeto: {publicacao.objeto}
    Contrato SAIC: {publicacao.contrato_saic}
    Modalidade: {publicacao.modalidade_licitacao}
    Valor Global: {publicacao.valor_global}
    """
    
    tarefa = Tarefa(
        titulo=titulo,
        resumo=resumo,
        status='Não iniciada',
        prioridade='Alta',
        data_inicio=datetime.now().date(),
        data_termino=publicacao.vigencia_inicio if publicacao.vigencia_inicio else None,
        solicitante_id=current_user.id,
        responsavel_id=current_user.id,
        observacoes=f"Tarefa gerada automaticamente para acompanhamento da publicação ID: {publicacao.id}"
    )
    
    return tarefa

def atualizar_tarefa_publicacao(publicacao):
    """Atualiza ou cria uma tarefa relacionada à publicação."""
    # Procura por uma tarefa existente relacionada à publicação
    tarefa = Tarefa.query.filter(
        Tarefa.observacoes.like(f"%publicação ID: {publicacao.id}%")
    ).first()
    
    if not tarefa:
        # Se não existir, cria uma nova
        tarefa = criar_tarefa_publicacao(publicacao)
        db.session.add(tarefa)
    else:
        # Se existir, atualiza
        tarefa.titulo = f"Publicação - {publicacao.especie}"
        tarefa.resumo = f"""
        Objeto: {publicacao.objeto}
        Contrato SAIC: {publicacao.contrato_saic}
        Modalidade: {publicacao.modalidade_licitacao}
        Valor Global: {publicacao.valor_global}
        """
        tarefa.data_termino = publicacao.vigencia_inicio if publicacao.vigencia_inicio else None
    
    return tarefa

@publicacao_bp.route('/publicacoes')
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

@publicacao_bp.route('/publicacao/<int:id>/visualizar')
@login_required
def visualizar_publicacao(id):
    publicacao = Publicacao.query.get_or_404(id)
    
    # Formata o texto da vigência para exibição
    texto_vigencia = "A partir da Assinatura"
    if publicacao.vigencia_inicio and publicacao.vigencia_fim:
        texto_vigencia = f"De {publicacao.vigencia_inicio.strftime('%d/%m/%Y')} até {publicacao.vigencia_fim.strftime('%d/%m/%Y')}"
    elif publicacao.vigencia_inicio:
        texto_vigencia = f"A partir de {publicacao.vigencia_inicio.strftime('%d/%m/%Y')}"
    
    return render_template('publicacao/visualizar.html',
                         publicacao=publicacao,
                         texto_vigencia=texto_vigencia)

@publicacao_bp.route('/publicacao/nova', methods=['GET', 'POST'])
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
                vigencia_fim=vigencia_fim,
                excluido=False
            )

            # Atribui os relacionamentos
            publicacao.partes_embrapa = partes_embrapa
            publicacao.partes_fornecedor = partes_fornecedor
            publicacao.signatarios_embrapa = signatarios_embrapa
            publicacao.signatarios_externos = signatarios_externos

            db.session.add(publicacao)
            db.session.commit()

            # Cria e salva a tarefa automaticamente
            tarefa = criar_tarefa_publicacao(publicacao)
            db.session.add(tarefa)
            db.session.commit()

            flash('Publicação cadastrada com sucesso! Uma tarefa foi criada automaticamente.', 'success')
            return redirect(url_for('publicacao_bp.listar'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar publicação. Por favor, tente novamente.', 'danger')
            print(f"Erro: {str(e)}")
            return redirect(url_for('publicacao_bp.nova_publicacao'))

    # GET: Renderiza o formulário
    usuarios = Usuario.query.all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html',
                         usuarios=usuarios,
                         fornecedores=fornecedores)

@publicacao_bp.route('/publicacao/<int:id>/editar', methods=['GET', 'POST'])
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

            # Atualiza a tarefa relacionada
            atualizar_tarefa_publicacao(publicacao)
            
            db.session.commit()
            flash('Publicação e tarefa relacionada atualizadas com sucesso!', 'success')
            return redirect(url_for('publicacao_bp.listar'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar publicação. Por favor, tente novamente.', 'danger')
            print(f"Erro: {str(e)}")
            return redirect(url_for('publicacao_bp.editar_publicacao', id=id))

    # GET: Renderiza o formulário com os dados atuais
    usuarios = Usuario.query.all()
    fornecedores = Fornecedor.query.all()
    return render_template('publicacao/form.html',
                         publicacao=publicacao,
                         usuarios=usuarios,
                         fornecedores=fornecedores)

@publicacao_bp.route('/publicacao/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_publicacao(id):
    publicacao = Publicacao.query.get_or_404(id)
    try:
        # Exclusão lógica da publicação
        publicacao.excluido = True
        
        # Atualiza o status da tarefa relacionada
        tarefa = Tarefa.query.filter(
            Tarefa.observacoes.like(f"%publicação ID: {publicacao.id}%")
        ).first()
        
        if tarefa:
            tarefa.status = 'Concluída'
            tarefa.observacoes += "\nPublicação excluída em " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        db.session.commit()
        flash('Publicação excluída com sucesso! A tarefa relacionada foi marcada como concluída.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir publicação. Por favor, tente novamente.', 'danger')
        print(f"Erro: {str(e)}")
    
    return redirect(url_for('publicacao_bp.listar')) 
