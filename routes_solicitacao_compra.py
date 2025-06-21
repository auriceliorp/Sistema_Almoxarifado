from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.solicitacao_compra_service import SolicitacaoCompraService
from models import db, Item, SolicitacaoCompra, ItemSolicitacaoCompra, Tarefa, CategoriaTarefa, Atividade, TriagemSolicitacaoCompra, PainelContratacao, NaturezaDespesa, Usuario, UnidadeLocal
import logging
import json
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

solicitacao_compra_bp = Blueprint('solicitacao_compra_bp', __name__, url_prefix='/solicitacao-compra')

@solicitacao_compra_bp.route('/nova')
@login_required
def nova_solicitacao():
    """Página para criar nova solicitação de compra"""
    try:
        itens = Item.query.order_by(Item.nome).all()
        atividades = Atividade.query.filter_by(status='ATIVA').order_by(Atividade.numero).all()
        return render_template('solicitacao_compra/nova_solicitacao.html', 
                             itens=itens,
                             atividades=atividades)
    except Exception as e:
        logger.error(f'Erro ao carregar página de nova solicitação: {str(e)}')
        # Retorna a página mesmo com erro, mas sem os dados
        return render_template('solicitacao_compra/nova_solicitacao.html', 
                             itens=[],
                             atividades=[],
                             error_message='Erro ao carregar os dados. Por favor, tente novamente.')

@solicitacao_compra_bp.route('/criar', methods=['POST'])
@login_required
def criar_solicitacao():
    """Cria uma nova solicitação de compra"""
    try:
        # Obter dados do formulário
        itens_ids = request.form.getlist('item_id[]')
        quantidades = request.form.getlist('quantidade[]')
        atividade_id = request.form.get('atividade_id')
        finalidade = request.form.get('finalidade')
        justificativa_marca = request.form.get('justificativa_marca')

        if not itens_ids:
            raise ValueError("É necessário incluir pelo menos um item")

        # Buscar a atividade
        atividade = Atividade.query.get(atividade_id)
        if not atividade:
            raise ValueError("Atividade não encontrada")

        # Preparar lista de itens
        itens = []
        for item_id, qtd in zip(itens_ids, quantidades):
            if item_id and qtd:
                quantidade = int(qtd)
                if quantidade <= 0:
                    raise ValueError("Quantidade deve ser maior que zero")

                itens.append({
                    'id': item_id,
                    'quantidade': quantidade
                })

        # Criar solicitação
        result = SolicitacaoCompraService.criar_solicitacao(
            solicitante_id=current_user.id,
            numero_atividade=atividade.numero,
            nome_atividade=atividade.nome,
            finalidade=finalidade,
            justificativa_marca=justificativa_marca,
            itens=itens
        )

        if result['success']:
            flash('Solicitação de compra criada com sucesso!', 'success')
            return redirect(url_for('solicitacao_compra_bp.minhas_solicitacoes'))
        else:
            flash(f'Erro ao criar solicitação: {result["error"]}', 'error')
            return redirect(url_for('solicitacao_compra_bp.nova_solicitacao'))

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('solicitacao_compra_bp.nova_solicitacao'))
    except Exception as e:
        flash(f'Erro ao criar solicitação: {str(e)}', 'error')
        return redirect(url_for('solicitacao_compra_bp.nova_solicitacao'))

@solicitacao_compra_bp.route('/minhas')
@login_required
def minhas_solicitacoes():
    """Lista as solicitações do usuário atual"""
    try:
        result = SolicitacaoCompraService.listar_minhas_solicitacoes(current_user.id)
        if result['success']:
            return render_template('solicitacao_compra/minhas_solicitacoes.html', 
                                solicitacoes=result['solicitacoes'])
        else:
            flash(f'Erro ao listar solicitações: {result["error"]}', 'error')
            return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Erro ao listar solicitações: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@solicitacao_compra_bp.route('/<int:solicitacao_id>')
@login_required
def detalhes_solicitacao(solicitacao_id):
    """Exibe os detalhes de uma solicitação de compra"""
    try:
        # Buscar a solicitação
        solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
        
        # Verificar se o usuário tem permissão para ver esta solicitação
        if not current_user.is_admin() and solicitacao.solicitante_id != current_user.id:
            flash('Você não tem permissão para ver esta solicitação.', 'error')
            return redirect(url_for('solicitacao_compra_bp.minhas_solicitacoes'))
        
        return render_template('solicitacao_compra/detalhes_solicitacao.html', 
                             solicitacao=solicitacao)
    except Exception as e:
        flash(f'Erro ao carregar detalhes da solicitação: {str(e)}', 'error')
        return redirect(url_for('solicitacao_compra_bp.minhas_solicitacoes'))

@solicitacao_compra_bp.route('/<int:solicitacao_id>/cancelar', methods=['POST'])
@login_required
def cancelar_solicitacao(solicitacao_id):
    """Cancela uma solicitação de compra"""
    try:
        solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
        
        # Verificar se o usuário tem permissão para cancelar
        if solicitacao.solicitante_id != current_user.id:
            flash('Você não tem permissão para cancelar esta solicitação.', 'error')
            return redirect(url_for('solicitacao_compra_bp.detalhes_solicitacao', solicitacao_id=solicitacao_id))
            
        # Verificar se a solicitação pode ser cancelada
        if solicitacao.status != 'PENDENTE':
            flash('Esta solicitação não pode ser cancelada.', 'error')
            return redirect(url_for('solicitacao_compra_bp.detalhes_solicitacao', solicitacao_id=solicitacao_id))
            
        # Cancelar a solicitação
        solicitacao.status = 'CANCELADA'
        db.session.commit()
        
        flash('Solicitação cancelada com sucesso.', 'success')
        return redirect(url_for('solicitacao_compra_bp.minhas_solicitacoes'))
        
    except Exception as e:
        flash(f'Erro ao cancelar solicitação: {str(e)}', 'error')
        return redirect(url_for('solicitacao_compra_bp.detalhes_solicitacao', solicitacao_id=solicitacao_id))

@solicitacao_compra_bp.route('/<int:solicitacao_id>/imprimir')
@login_required
def imprimir_solicitacao(solicitacao_id):
    """Gera o documento de impressão da solicitação de compra"""
    try:
        solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
        
        # Verificar permissão
        if not current_user.is_admin() and solicitacao.solicitante_id != current_user.id:
            flash('Você não tem permissão para imprimir esta solicitação.', 'error')
            return redirect(url_for('solicitacao_compra_bp.minhas_solicitacoes'))
            
        return render_template('solicitacao_compra/imprimir_solicitacao.html', 
                             solicitacao=solicitacao)
                             
    except Exception as e:
        flash(f'Erro ao gerar impressão: {str(e)}', 'error')
        return redirect(url_for('solicitacao_compra_bp.detalhes_solicitacao', 
                              solicitacao_id=solicitacao_id))

@solicitacao_compra_bp.route('/atender/<int:solicitacao_id>', methods=['GET', 'POST'])
@login_required
def atender_solicitacao(solicitacao_id):
    solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
    
    if request.method == 'POST':
        novo_status = request.form.get('status')
        criar_processo = request.form.get('criar_processo') == 'on'
        
        dados_painel = None
        if criar_processo:
            dados_painel = {
                'numero_sei': request.form.get('numero_sei'),
                'modalidade': request.form.get('modalidade'),
                # ... outros campos do painel ...
            }
        
        result = SolicitacaoCompraService.atender_solicitacao(
            solicitacao_id=solicitacao_id,
            novo_status=novo_status,
            dados_painel=dados_painel
        )
        
        if result['success']:
            flash('Solicitação atendida com sucesso!', 'success')
            return redirect(url_for('solicitacao_compra_bp.lista_solicitacoes_pendentes'))
        else:
            flash(f'Erro ao atender solicitação: {result["error"]}', 'error')
    
    return render_template(
        'solicitacao_compra/atender_solicitacao.html',
        solicitacao=solicitacao
    )

@solicitacao_compra_bp.route('/triagem_solicitacoes')
@login_required
def triagem_solicitacoes():
    # Buscar solicitações pendentes
    solicitacoes = SolicitacaoCompra.query.filter_by(status='Processo Iniciado').all()
    
    # Buscar triagens existentes
    triagens = TriagemSolicitacaoCompra.query.order_by(TriagemSolicitacaoCompra.data_criacao.desc()).all()
    
    return render_template('solicitacao_compra/triagem_solicitacoes.html', 
                         solicitacoes=solicitacoes,
                         triagens=triagens)

@solicitacao_compra_bp.route('/criar_triagem', methods=['POST'])
@login_required
def criar_triagem():
    try:
        dados = request.get_json()
        print("Dados recebidos:", dados)  # Debug
        
        # Criar nova triagem
        triagem = TriagemSolicitacaoCompra(
            titulo=dados['titulo'],
            descricao=dados['descricao'],
            responsavel_id=current_user.id
        )
        db.session.add(triagem)
        db.session.flush()  # Para obter o ID da triagem
        
        # Associar solicitações à triagem
        for solicitacao_id in dados['solicitacoes']:
            solicitacao = SolicitacaoCompra.query.get(solicitacao_id)
            if solicitacao:
                solicitacao.triagem_id = triagem.id
                print(f"Associando solicitação {solicitacao_id} à triagem {triagem.id}")  # Debug
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Triagem criada com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        print("Erro ao criar triagem:", str(e))  # Debug
        return jsonify({'success': False, 'message': str(e)}), 400

@solicitacao_compra_bp.route('/triagem/<int:triagem_id>/processo', methods=['POST'])
@login_required
def criar_processo_da_triagem(triagem_id):
    try:
        dados = request.get_json()
        triagem = TriagemSolicitacaoCompra.query.get_or_404(triagem_id)
        
        # Criar processo no painel de contratações
        processo = PainelContratacao(
            ano=dados.get('ano'),
            numero_sei=dados.get('numero_sei'),
            modalidade=dados.get('modalidade'),
            objeto=dados.get('objeto'),
            natureza_despesa=dados.get('natureza_despesa'),
            valor_estimado=dados.get('valor_estimado'),
            setor_responsavel=dados.get('setor_responsavel'),
            responsavel_conducao=dados.get('responsavel_conducao'),
            status='Processo Iniciado',
            solicitante_id=current_user.id
        )
        
        db.session.add(processo)
        db.session.flush()  # Para obter o ID do processo
        
        # Atualizar solicitações vinculadas à triagem
        for solicitacao in triagem.solicitacoes:
            solicitacao.painel_contratacao_id = processo.id
            solicitacao.status = 'Em andamento'
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Processo criado com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@solicitacao_compra_bp.route('/triagem/<int:triagem_id>/criar_processo', methods=['GET', 'POST'])
@login_required
def criar_processo_form(triagem_id):
    triagem = TriagemSolicitacaoCompra.query.get_or_404(triagem_id)
    
    # Buscar dados para os selects
    naturezas_despesa = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
    setores = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all()
    
    # Lista de fundamentações legais
    fundamentacoes_legais = [
        'Art. 17, I (RLCC) c/c Art. 6º, XVI (Lei 14.133/2021) - Pregão',
        'Art. 29, I (Lei 13.303/2016) c/c Art. 98, Art. 100 e Art. 103, §3º - Dispensa',
        'Art. 29, II - Dispensa',
        'Art. 29, X - Prestadoras de Serviço Público',
        'Art. 29, XV - Contratação Emergencial',
        'Art. 30, I - Inexigibilidade',
        'Art. 30, II - Inexigibilidade',
        'Art. 108, IV - Congressos, Feiras e Exposições',
        'Art. 75, IV, "c" - P&D',
        'Art. 17, II - Licitação Embrapa'
    ]

    if request.method == 'POST':
        try:
            # Criar processo no painel de contratações
            processo = PainelContratacao(
                ano=request.form.get('ano'),
                data_abertura=datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d') if request.form.get('data_abertura') else None,
                data_homologacao=datetime.strptime(request.form.get('data_homologacao'), '%Y-%m-%d') if request.form.get('data_homologacao') else None,
                periodo_dias=request.form.get('periodo_dias'),
                numero_sei=request.form.get('numero_sei'),
                modalidade=request.form.get('modalidade'),
                registro_precos=request.form.get('registro_precos'),
                orgaos_participantes=request.form.get('orgaos_participantes'),
                numero_licitacao=request.form.get('numero_licitacao'),
                parecer_juridico=request.form.get('parecer_juridico'),
                fundamentacao_legal=request.form.get('fundamentacao_legal'),
                objeto=request.form.get('objeto'),  # Campo obrigatório
                natureza_despesa=request.form.get('natureza_despesa'),
                valor_estimado=float(request.form.get('valor_estimado')) if request.form.get('valor_estimado') else None,
                valor_homologado=float(request.form.get('valor_homologado')) if request.form.get('valor_homologado') else None,
                percentual_economia=None,  # Será calculado depois
                impugnacao=request.form.get('impugnacao'),
                recurso=request.form.get('recurso'),
                itens_desertos=request.form.get('itens_desertos'),
                responsavel_conducao=request.form.get('responsavel_conducao'),
                setor_responsavel=request.form.get('setor_responsavel'),
                status='Processo Iniciado',
                excluido=False,
                solicitante_id=current_user.id
            )
            
            db.session.add(processo)
            db.session.flush()
            
            # Atualizar solicitações vinculadas à triagem
            for solicitacao in triagem.solicitacoes:
                solicitacao.painel_contratacao_id = processo.id
                solicitacao.status = 'Em andamento'
            
            db.session.commit()
            flash('Processo criado com sucesso!', 'success')
            return redirect(url_for('painel_bp.visualizar_painel', painel_id=processo.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar processo: {str(e)}', 'error')
            return render_template(
                'solicitacao_compra/criar_processo.html',
                triagem=triagem,
                now=datetime.now(),
                naturezas_despesa=naturezas_despesa,
                usuarios=usuarios,
                setores=setores,
                fundamentacoes_legais=fundamentacoes_legais
            )
    
    return render_template(
        'solicitacao_compra/criar_processo.html',
        triagem=triagem,
        now=datetime.now(),
        naturezas_despesa=naturezas_despesa,
        usuarios=usuarios,
        setores=setores,
        fundamentacoes_legais=fundamentacoes_legais
    ) 
