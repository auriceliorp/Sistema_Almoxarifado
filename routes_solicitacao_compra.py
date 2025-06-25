from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from services.solicitacao_compra_service import SolicitacaoCompraService
from models import db, Item, SolicitacaoCompra, ItemSolicitacaoCompra, Tarefa, CategoriaTarefa, Atividade, TriagemSolicitacaoCompra, PainelContratacao, NaturezaDespesa, Usuario, UnidadeLocal, Local, Setor, Grupo
import logging
import json
from datetime import datetime
import csv
from io import StringIO
from sqlalchemy import func
from flask import current_app

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
        if solicitacao.status != 'Pendente':
            flash('Esta solicitação não pode ser cancelada.', 'error')
            return redirect(url_for('solicitacao_compra_bp.detalhes_solicitacao', solicitacao_id=solicitacao_id))
            
        # Cancelar a solicitação
        solicitacao.status = 'Cancelada'
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

@solicitacao_compra_bp.route('/triagem')
@login_required
def triagem_solicitacoes():
    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)

    # Carregar dados para os filtros
    solicitantes = Usuario.query.order_by(Usuario.nome).all()
    naturezas_despesa = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    # Usar os status do serviço
    status_list = SolicitacaoCompraService.STATUS_CHOICES

    # Carregar solicitações com paginação
    solicitacoes = SolicitacaoCompra.query\
        .order_by(SolicitacaoCompra.data_solicitacao.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # Carregar triagens
    triagens = TriagemSolicitacaoCompra.query\
        .order_by(TriagemSolicitacaoCompra.data_criacao.desc())\
        .all()

    return render_template(
        'solicitacao_compra/triagem_solicitacoes.html',
        solicitacoes=solicitacoes,
        triagens=triagens,
        solicitantes=solicitantes,
        naturezas_despesa=naturezas_despesa,
        status_list=status_list
    )

@solicitacao_compra_bp.route('/criar_triagem', methods=['POST'])
@login_required
def criar_triagem():
    try:
        dados = request.get_json()
        
        # Criar a triagem
        triagem = TriagemSolicitacaoCompra(
            titulo=dados['titulo'],
            descricao=dados['descricao'],
            responsavel_id=current_user.id,
            data_criacao=datetime.now()
        )
        db.session.add(triagem)
        
        # Associar solicitações e atualizar seus status
        for solicitacao_id in dados['solicitacoes']:
            solicitacao = SolicitacaoCompra.query.get(solicitacao_id)
            if solicitacao:
                triagem.solicitacoes.append(solicitacao)
                # Atualizar o status da solicitação
                solicitacao.status = 'Andamento'  # Usando o status padrão do sistema
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Triagem criada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao criar triagem: {str(e)}'
        }), 500

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
            solicitacao.status = 'Andamento'  # Mantendo consistência com o padrão
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Processo criado com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@solicitacao_compra_bp.route('/triagem/<int:triagem_id>/criar_processo', methods=['GET', 'POST'])
@login_required
def criar_processo_form(triagem_id):
    try:
        from datetime import datetime
        from models import NaturezaDespesa, Usuario, UnidadeLocal
        
        triagem = TriagemSolicitacaoCompra.query.get_or_404(triagem_id)
        
        if request.method == 'POST':
            dados_painel = {
                'numero_sei': request.form.get('numero_sei'),
                'modalidade': request.form.get('modalidade'),
                'objeto': request.form.get('objeto'),
                'fundamentacao_legal': request.form.get('fundamentacao_legal'),
                'orgaos_participantes': request.form.get('orgaos_participantes'),
                'natureza_despesa': request.form.get('natureza_despesa'),
                'valor_estimado': request.form.get('valor_estimado'),
                'valor_homologado': request.form.get('valor_homologado'),
                'setor_responsavel': request.form.get('setor_responsavel'),
                'responsavel_conducao': request.form.get('responsavel_conducao'),
                'impugnacao': request.form.get('impugnacao'),
                'recurso': request.form.get('recurso'),
                'itens_desertos': request.form.get('itens_desertos')
            }
            
            # Atualizar todas as solicitações da triagem
            for solicitacao in triagem.solicitacoes:
                result = SolicitacaoCompraService.atender_solicitacao(
                    solicitacao_id=solicitacao.id,
                    novo_status='Andamento',
                    dados_painel=dados_painel
                )
                
                if not result['success']:
                    raise Exception(result['error'])
            
            flash('Processo criado com sucesso!', 'success')
            return redirect(url_for('painel_bp.lista_painel'))
        
        # Carregar dados para os selects
        fundamentacoes_legais = [
            'Art. 24, Inc. I - Lei 8.666/93',
            'Art. 24, Inc. II - Lei 8.666/93',
            'Art. 25, Inc. I - Lei 8.666/93',
            'Art. 25, Inc. II - Lei 8.666/93',
            'Art. 25, Inc. III - Lei 8.666/93',
            'Lei 14.133/2021 - Nova Lei de Licitações',
            'Art. 75, Inc. I - Lei 14.133/2021',
            'Art. 75, Inc. II - Lei 14.133/2021',
            'Art. 74, Inc. I - Lei 14.133/2021',
            'Art. 74, Inc. II - Lei 14.133/2021',
            'Art. 74, Inc. III - Lei 14.133/2021'
        ]
        
        # Buscar naturezas de despesa
        naturezas_despesa = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
        
        # Buscar unidades locais
        unidades_locais = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all()
        
        # Buscar usuários ativos
        usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
            
        return render_template('solicitacao_compra/criar_processo.html', 
                             triagem=triagem,
                             now=datetime.now(),
                             fundamentacoes_legais=fundamentacoes_legais,
                             naturezas_despesa=naturezas_despesa,
                             setores=unidades_locais,
                             usuarios=usuarios)
        
    except Exception as e:
        flash(f'Erro ao criar processo: {str(e)}', 'error')
        return redirect(url_for('solicitacao_compra_bp.triagem_solicitacoes'))

@solicitacao_compra_bp.route('/detalhes/<int:solicitacao_id>')
@login_required
def detalhes_solicitacao_ajax(solicitacao_id):
    try:
        solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
        
        # Renderizar o template com os detalhes
        html = render_template(
            'solicitacao_compra/detalhes_solicitacao.html',
            solicitacao=solicitacao,
            _is_ajax=True
        )
        
        return jsonify({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@solicitacao_compra_bp.route('/api/detalhes/<int:solicitacao_id>')
@login_required
def api_detalhes_solicitacao(solicitacao_id):
    """Retorna os detalhes da solicitação em formato JSON para AJAX"""
    try:
        solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
        
        # Verificar permissão
        if not current_user.is_admin() and solicitacao.solicitante_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Você não tem permissão para ver esta solicitação.'
            }), 403
        
        # Renderizar o template parcial
        html = render_template('solicitacao_compra/detalhes_solicitacao_partial.html',
                             solicitacao=solicitacao)
        
        return jsonify({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@solicitacao_compra_bp.route('/lista_solicitacoes_pendentes')
@login_required
def lista_solicitacoes_pendentes():
    """Lista todas as solicitações pendentes para atendimento"""
    try:
        # Buscar solicitações pendentes
        solicitacoes = SolicitacaoCompra.query.filter(
            SolicitacaoCompra.status.in_(['Processo Iniciado', 'Em andamento'])
        ).order_by(SolicitacaoCompra.data_solicitacao.desc()).all()
        
        return render_template('solicitacao_compra/requisicoes_pendentes.html',
                             solicitacoes=solicitacoes)
    except Exception as e:
        flash(f'Erro ao listar solicitações pendentes: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@solicitacao_compra_bp.route('/lista_solicitacoes_atendidas')
@login_required
def lista_solicitacoes_atendidas():
    """Lista todas as solicitações já atendidas"""
    try:
        # Buscar solicitações atendidas
        solicitacoes = SolicitacaoCompra.query.filter(
            SolicitacaoCompra.status.in_(['Concluído', 'Cancelada'])
        ).order_by(SolicitacaoCompra.data_solicitacao.desc()).all()
        
        return render_template('solicitacao_compra/requisicoes_atendidas.html',
                             solicitacoes=solicitacoes)
    except Exception as e:
        flash(f'Erro ao listar solicitações atendidas: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@solicitacao_compra_bp.route('/buscar_solicitacoes')
@login_required
def buscar_solicitacoes():
    """Busca solicitações por critérios"""
    try:
        # Obter parâmetros de busca
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        solicitante_id = request.args.get('solicitante_id')
        
        # Construir query base
        query = SolicitacaoCompra.query
        
        # Aplicar filtros
        if status:
            query = query.filter(SolicitacaoCompra.status == status)
        if data_inicio:
            query = query.filter(SolicitacaoCompra.data_solicitacao >= data_inicio)
        if data_fim:
            query = query.filter(SolicitacaoCompra.data_solicitacao <= data_fim)
        if solicitante_id:
            query = query.filter(SolicitacaoCompra.solicitante_id == solicitante_id)
            
        # Ordenar e executar query
        solicitacoes = query.order_by(SolicitacaoCompra.data_solicitacao.desc()).all()
        
        return render_template('solicitacao_compra/lista_solicitacoes.html',
                             solicitacoes=solicitacoes)
    except Exception as e:
        flash(f'Erro ao buscar solicitações: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@solicitacao_compra_bp.route('/exportar_solicitacoes')
@login_required
def exportar_solicitacoes():
    """Exporta solicitações para CSV"""
    try:
        # Obter parâmetros de filtro
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Construir query base
        query = SolicitacaoCompra.query
        
        # Aplicar filtros
        if status:
            query = query.filter(SolicitacaoCompra.status == status)
        if data_inicio:
            query = query.filter(SolicitacaoCompra.data_solicitacao >= data_inicio)
        if data_fim:
            query = query.filter(SolicitacaoCompra.data_solicitacao <= data_fim)
            
        # Buscar solicitações
        solicitacoes = query.order_by(SolicitacaoCompra.data_solicitacao.desc()).all()
        
        # Criar CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow(['ID', 'Data', 'Solicitante', 'Status', 'Atividade', 'Finalidade'])
        
        # Escrever dados
        for s in solicitacoes:
            writer.writerow([
                s.id,
                s.data_solicitacao.strftime('%d/%m/%Y'),
                s.solicitante.nome,
                s.status,
                s.numero_atividade,
                s.finalidade
            ])
        
        # Preparar resposta
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=solicitacoes.csv'}
        )
        
    except Exception as e:
        flash(f'Erro ao exportar solicitações: {str(e)}', 'error')
        return redirect(url_for('solicitacao_compra_bp.lista_solicitacoes_pendentes'))

@solicitacao_compra_bp.route('/triagem/filtrar')
@login_required
def filtrar_triagem():
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 10)

        # Obter parâmetros dos filtros
        solicitante_id = request.args.get('solicitante')
        status = request.args.get('status')
        nd_id = request.args.get('nd')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        # Debug dos parâmetros recebidos
        print("Filtros recebidos:", {
            'solicitante_id': solicitante_id,
            'status': status,
            'nd_id': nd_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim
        })

        # Query base
        query = SolicitacaoCompra.query

        # Aplicar filtros (apenas se valores não forem vazios)
        if solicitante_id and solicitante_id != '':
            query = query.filter(SolicitacaoCompra.solicitante_id == int(solicitante_id))
        
        if status and status != '':
            # Verificar se o status é válido
            if status in SolicitacaoCompraService.STATUS_CHOICES:
                query = query.filter(SolicitacaoCompra.status == status)
        
        if nd_id and nd_id != '':
            query = query.join(ItemSolicitacaoCompra, SolicitacaoCompra.id == ItemSolicitacaoCompra.solicitacao_id)\
                        .join(Item, ItemSolicitacaoCompra.item_id == Item.id)\
                        .join(Grupo)\
                        .filter(Grupo.natureza_despesa_id == int(nd_id))\
                        .distinct()
        
        if data_inicio and data_inicio != '':
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(SolicitacaoCompra.data_solicitacao >= data_inicio)
        
        if data_fim and data_fim != '':
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(SolicitacaoCompra.data_solicitacao <= data_fim)

        # Contar total de registros
        total_registros = query.count()

        # Ordenar e paginar
        solicitacoes = query.order_by(SolicitacaoCompra.data_solicitacao.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)

        # Renderizar tabela e paginação
        html_tabela = render_template(
            'solicitacao_compra/partials/tabela_solicitacoes.html',
            solicitacoes=solicitacoes
        )

        html_paginacao = render_template(
            'solicitacao_compra/partials/paginacao.html',
            solicitacoes=solicitacoes
        )

        return jsonify({
            'success': True,
            'html_tabela': html_tabela,
            'html_paginacao': html_paginacao,
            'total_registros': total_registros,
            'pagina_atual': page,
            'total_paginas': solicitacoes.pages
        })

    except Exception as e:
        print("Erro ao filtrar:", str(e))  # Debug do erro
        return jsonify({
            'success': False,
            'message': str(e)
        }) 

@solicitacao_compra_bp.route('/triagem/<int:triagem_id>/cancelar', methods=['POST'])
@login_required
def cancelar_processo(triagem_id):
    try:
        # Buscar a triagem
        triagem = TriagemSolicitacaoCompra.query.get_or_404(triagem_id)
        
        # Verificar se todas as solicitações têm processo
        tem_processo = False
        for solicitacao in triagem.solicitacoes:
            if solicitacao.painel_contratacao_id:
                tem_processo = True
                # Atualizar status da solicitação
                solicitacao.status = 'Cancelada'
                # Remover referência ao painel
                solicitacao.painel_contratacao_id = None
        
        if not tem_processo:
            return jsonify({'success': False, 'message': 'Esta triagem não tem processo para cancelar'}), 400
        
        # Commit das alterações
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500 

@solicitacao_compra_bp.route('/triagem/<int:triagem_id>/atualizar_status', methods=['POST'])
@login_required
def atualizar_status_triagem(triagem_id):
    try:
        # Buscar a triagem
        triagem = TriagemSolicitacaoCompra.query.get_or_404(triagem_id)
        
        # Obter o novo status do JSON
        dados = request.get_json()
        novo_status = dados.get('status')
        
        if not novo_status:
            return jsonify({'success': False, 'message': 'Status não fornecido'}), 400
            
        # Verificar se o status é válido
        status_validos = ['Processo Iniciado', 'Em andamento', 'Concluído', 'Aguardando Definições', 'Cancelada']
        if novo_status not in status_validos:
            return jsonify({'success': False, 'message': 'Status inválido'}), 400
        
        # Atualizar o status
        triagem.status = novo_status
        
        # Se o status for "Cancelada", atualizar também as solicitações
        if novo_status == 'Cancelada':
            for solicitacao in triagem.solicitacoes:
                solicitacao.status = 'Cancelada'
        
        # Commit das alterações
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500 
