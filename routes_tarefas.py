# Importações do Flask
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

# Importações locais
from models import db, Tarefa, CategoriaTarefa, OrigemTarefa, UnidadeLocal, Usuario, LogAuditoria
from extensoes import csrf

# Outras importações
from datetime import datetime, timedelta
from sqlalchemy import func

# Definição dos blueprints
tarefas_bp = Blueprint('tarefas', __name__, url_prefix='/tarefas')
api_bp = Blueprint('tarefas_api', __name__, url_prefix='/api')

@tarefas_bp.route('/')
@login_required
def lista_tarefas():
    """Lista todas as tarefas."""
    status_filter = request.args.get('status', None)
    
    # Query base
    query = Tarefa.query
    
    # Aplicar filtro de status se fornecido
    if status_filter:
        query = query.filter(Tarefa.status == status_filter)
    
    # Ordenar por data de criação (mais recentes primeiro)
    tarefas = query.order_by(Tarefa.data_criacao.desc()).all()
    
    # Buscar dados para os selects
    categorias = CategoriaTarefa.query.order_by(CategoriaTarefa.nome).all()
    origens = OrigemTarefa.query.order_by(OrigemTarefa.nome).all()
    unidades_locais = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    
    # Estatísticas
    total_tarefas = len(tarefas)
    tarefas_nao_iniciadas = sum(1 for t in tarefas if t.status == 'Não iniciada')
    tarefas_em_execucao = sum(1 for t in tarefas if t.status == 'Em execução')
    tarefas_suspensas = sum(1 for t in tarefas if t.status == 'Suspensa')
    tarefas_concluidas = sum(1 for t in tarefas if t.status == 'Concluída')
    tarefas_em_atraso = sum(1 for t in tarefas if t.status == 'Em atraso')
    
    return render_template('tarefas/lista_tarefas.html',
                         tarefas=tarefas,
                         categorias=categorias,
                         origens=origens,
                         unidades_locais=unidades_locais,
                         usuarios=usuarios,
                         total_tarefas=total_tarefas,
                         tarefas_nao_iniciadas=tarefas_nao_iniciadas,
                         tarefas_em_execucao=tarefas_em_execucao,
                         tarefas_suspensas=tarefas_suspensas,
                         tarefas_concluidas=tarefas_concluidas,
                         tarefas_em_atraso=tarefas_em_atraso)

@tarefas_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_tarefa():
    """Cria uma nova tarefa."""
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            titulo = request.form.get('titulo')
            numero_sei = request.form.get('numero_sei')
            categoria_id = request.form.get('categoria_id')
            resumo = request.form.get('resumo')
            unidade_local_id = request.form.get('unidade_local_id')
            origem_id = request.form.get('origem_id')
            responsavel_id = request.form.get('responsavel_id')
            solicitante_id = request.form.get('solicitante_id')
            quantidade_acoes = request.form.get('quantidade_acoes', type=int)
            prioridade = request.form.get('prioridade')
            status = request.form.get('status')  # Agora pegamos o status do formulário
            data_inicio = request.form.get('data_inicio')
            data_termino = request.form.get('data_termino')
            observacoes = request.form.get('observacoes')
            
            # Validar campos obrigatórios
            if not titulo:
                flash('Título é obrigatório.', 'error')
                return redirect(url_for('tarefas.nova_tarefa'))
            
            # Converter datas
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d') if data_inicio else None
            data_termino = datetime.strptime(data_termino, '%Y-%m-%d') if data_termino else None
            
            # Criar nova tarefa
            tarefa = Tarefa(
                titulo=titulo,
                numero_sei=numero_sei,
                categoria_id=categoria_id,
                resumo=resumo,
                unidade_local_id=unidade_local_id,
                origem_id=origem_id,
                responsavel_id=responsavel_id,
                solicitante_id=solicitante_id or current_user.id,
                quantidade_acoes=quantidade_acoes,
                prioridade=prioridade,
                status=status,
                data_inicio=data_inicio,
                data_termino=data_termino,
                observacoes=observacoes
            )
            
            db.session.add(tarefa)
            db.session.commit()
            
            flash('Tarefa criada com sucesso!', 'success')
            return redirect(url_for('tarefas.lista_tarefas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar tarefa: {str(e)}', 'error')
            return redirect(url_for('tarefas.nova_tarefa'))
    
    # GET: Renderizar formulário
    categorias = CategoriaTarefa.query.order_by(CategoriaTarefa.nome).all()
    origens = OrigemTarefa.query.order_by(OrigemTarefa.nome).all()
    unidades_locais = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    
    return render_template('tarefas/form_tarefa.html',
                         categorias=categorias,
                         origens=origens,
                         unidades_locais=unidades_locais,
                         usuarios=usuarios)

@tarefas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_tarefa(id):
    """Edita uma tarefa existente."""
    tarefa = Tarefa.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            tarefa.titulo = request.form.get('titulo')
            tarefa.numero_sei = request.form.get('numero_sei')
            tarefa.categoria_id = request.form.get('categoria_id')
            tarefa.resumo = request.form.get('resumo')
            tarefa.unidade_local_id = request.form.get('unidade_local_id')
            tarefa.origem_id = request.form.get('origem_id')
            tarefa.responsavel_id = request.form.get('responsavel_id')
            tarefa.solicitante_id = request.form.get('solicitante_id')
            tarefa.quantidade_acoes = request.form.get('quantidade_acoes', type=int)
            tarefa.prioridade = request.form.get('prioridade')
            tarefa.status = request.form.get('status')
            
            # Converter datas
            data_inicio = request.form.get('data_inicio')
            data_termino = request.form.get('data_termino')
            tarefa.data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d') if data_inicio else None
            tarefa.data_termino = datetime.strptime(data_termino, '%Y-%m-%d') if data_termino else None
            
            tarefa.observacoes = request.form.get('observacoes')
            
            db.session.commit()
            
            flash('Tarefa atualizada com sucesso!', 'success')
            return redirect(url_for('tarefas.lista_tarefas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tarefa: {str(e)}', 'error')
            return redirect(url_for('tarefas.editar_tarefa', id=id))
    
    # GET: Renderizar formulário
    categorias = CategoriaTarefa.query.order_by(CategoriaTarefa.nome).all()
    origens = OrigemTarefa.query.order_by(OrigemTarefa.nome).all()
    unidades_locais = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    
    return render_template('tarefas/form_tarefa.html',
                         tarefa=tarefa,
                         categorias=categorias,
                         origens=origens,
                         unidades_locais=unidades_locais,
                         usuarios=usuarios,
                         modo='editar')

@tarefas_bp.route('/excluir/<int:id>')
@login_required
def excluir_tarefa(id):
    """Exclui uma tarefa."""
    try:
        tarefa = Tarefa.query.get_or_404(id)
        db.session.delete(tarefa)
        db.session.commit()
        flash('Tarefa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tarefa: {str(e)}', 'error')
    
    return redirect(url_for('tarefas.lista_tarefas'))

# API Routes
@api_bp.route('/tarefas', methods=['GET'])
@login_required
def get_tarefas():
    try:
        unidade_local = request.args.get('unidade_local')
        prioridade = request.args.get('prioridade')
        status = request.args.get('status')
        responsavel = request.args.get('responsavel')
        
        query = Tarefa.query
        
        if unidade_local:
            query = query.filter_by(unidade_local_id=unidade_local)
        if prioridade:
            query = query.filter_by(prioridade=prioridade)
        if status:
            query = query.filter_by(status=status)
        if responsavel:
            query = query.filter_by(responsavel_id=responsavel)
            
        tarefas = query.all()
        return jsonify([tarefa.to_dict() for tarefa in tarefas])
    except Exception as e:
        print(f"Erro ao buscar tarefas: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas', methods=['POST'])
@login_required
def criar_tarefa():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        print(f"Dados recebidos: {data}")
            
        if not data.get('titulo'):
            return jsonify({'error': 'Título é obrigatório'}), 400
            
        tarefa = Tarefa(
            titulo=data['titulo'],
            numero_sei=data.get('numero_sei'),
            categoria_id=data.get('categoria_id'),
            resumo=data.get('resumo'),
            unidade_local_id=data.get('unidade_local_id'),
            origem_id=data.get('origem_id'),
            responsavel_id=data.get('responsavel_id'),
            solicitante_id=data.get('solicitante_id', current_user.id),
            quantidade_acoes=data.get('quantidade_acoes', 0),
            prioridade=data.get('prioridade', 'Média'),
            status=data.get('status', 'Não iniciada'),
            data_inicio=data.get('data_inicio'),
            data_termino=data.get('data_termino'),
            observacoes=data.get('observacoes'),
            data_criacao=datetime.utcnow()
        )
        
        db.session.add(tarefa)
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa criada com sucesso',
            'data': tarefa.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar tarefa: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas/<int:id>', methods=['PUT'])
@login_required
def atualizar_tarefa(id):
    """Atualiza uma tarefa existente."""
    try:
        tarefa = Tarefa.query.get_or_404(id)
        data = request.get_json()
        
        # Atualiza os campos se fornecidos
        if 'titulo' in data:
            tarefa.titulo = data['titulo']
        if 'numero_sei' in data:
            tarefa.numero_sei = data['numero_sei']
        if 'categoria_id' in data:
            tarefa.categoria_id = data['categoria_id']
        if 'resumo' in data:
            tarefa.resumo = data['resumo']
        if 'unidade_local_id' in data:
            tarefa.unidade_local_id = data['unidade_local_id']
        if 'origem_id' in data:
            tarefa.origem_id = data['origem_id']
        if 'responsavel_id' in data:
            tarefa.responsavel_id = data['responsavel_id']
        if 'prioridade' in data:
            tarefa.prioridade = data['prioridade']
        if 'quantidade_acoes' in data:
            tarefa.quantidade_acoes = data['quantidade_acoes']
        
        # Atualiza o status e a data de conclusão
        if 'status' in data:
            old_status = tarefa.status
            tarefa.status = data['status']
            
            if data['status'] == 'Concluída' and old_status != 'Concluída':
                tarefa.data_conclusao = datetime.utcnow()
            elif data['status'] != 'Concluída' and old_status == 'Concluída':
                tarefa.data_conclusao = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa atualizada com sucesso',
            'data': tarefa.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar tarefa: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas/<int:id>/status', methods=['PUT'])
@login_required
@csrf.exempt
def atualizar_status_tarefa(id):
    try:
        tarefa = Tarefa.query.get_or_404(id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'Status não fornecido'}), 400
            
        old_status = tarefa.status
        novo_status = data['status']
        
        # Validar status permitidos
        status_permitidos = ['Não iniciada', 'Em execução', 'Suspensa', 'Concluída', 'Em atraso']
        if novo_status not in status_permitidos:
            return jsonify({'error': f'Status inválido. Status permitidos: {", ".join(status_permitidos)}'}), 400
        
        tarefa.status = novo_status
        
        # Atualizar data de conclusão se necessário
        if novo_status == 'Concluída' and old_status != 'Concluída':
            tarefa.data_conclusao = datetime.utcnow()
        elif novo_status != 'Concluída' and old_status == 'Concluída':
            tarefa.data_conclusao = None
        
        # Commit das alterações
        db.session.commit()
        
        # Retornar também os contadores atualizados
        contadores = {
            'nao_iniciadas': Tarefa.query.filter_by(status='Não iniciada').count(),
            'em_execucao': Tarefa.query.filter_by(status='Em execução').count(),
            'suspensas': Tarefa.query.filter_by(status='Suspensa').count(),
            'concluidas': Tarefa.query.filter_by(status='Concluída').count(),
            'em_atraso': Tarefa.query.filter_by(status='Em atraso').count()
        }
        
        return jsonify({
            'message': 'Status atualizado com sucesso',
            'data': tarefa.to_dict(),
            'contadores': contadores
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar status da tarefa: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tarefas/contadores')
@login_required
def get_contadores():
    """Retorna os contadores de tarefas por status."""
    try:
        # Query base
        query = Tarefa.query
        
        # Calcular contadores
        total = query.count()
        nao_iniciadas = query.filter_by(status='Não iniciada').count()
        em_execucao = query.filter_by(status='Em execução').count()
        suspensas = query.filter_by(status='Suspensa').count()
        concluidas = query.filter_by(status='Concluída').count()
        
        # Lógica para tarefas em atraso
        hoje = datetime.now().date()
        em_atraso = query.filter(
            Tarefa.data_termino < hoje,
            Tarefa.status.notin_(['Concluída', 'Suspensa'])
        ).count()
        
        return jsonify({
            'total': total,
            'nao_iniciadas': nao_iniciadas,
            'em_execucao': em_execucao,
            'suspensas': suspensas,
            'concluidas': concluidas,
            'em_atraso': em_atraso
        })
    except Exception as e:
        print(f"Erro ao buscar contadores: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tarefas_bp.route('/dashboard')
@login_required
def dashboard_tarefas():
    """Renderiza a página do dashboard de tarefas."""
    # Contagem total de tarefas
    total_tarefas = Tarefa.query.count()
    
    # Contagem por status
    tarefas_em_andamento = Tarefa.query.filter_by(status='Em execução').count()
    tarefas_concluidas = Tarefa.query.filter_by(status='Concluída').count()
    tarefas_atrasadas = Tarefa.query.filter_by(status='Em atraso').count()
    
    # Dados para os gráficos
    # Categorias
    categorias = db.session.query(
        CategoriaTarefa.nome,
        func.count(Tarefa.id)
    ).join(Tarefa).group_by(CategoriaTarefa.nome).all()
    categorias_labels = [cat[0] for cat in categorias]
    categorias_data = [cat[1] for cat in categorias]
    
    # Unidades
    unidades = db.session.query(
        UnidadeLocal.descricao,
        func.count(Tarefa.id)
    ).join(Tarefa).group_by(UnidadeLocal.descricao).all()
    unidades_labels = [uni[0] for uni in unidades]
    unidades_data = [uni[1] for uni in unidades]
    
    # Origens
    origens = db.session.query(
        OrigemTarefa.nome,
        func.count(Tarefa.id)
    ).join(Tarefa).group_by(OrigemTarefa.nome).all()
    origens_labels = [orig[0] for orig in origens]
    origens_data = [orig[1] for orig in origens]
    
    # Responsáveis
    responsaveis = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id)
    ).join(Tarefa, Tarefa.responsavel_id == Usuario.id)\
    .group_by(Usuario.nome).all()
    responsaveis_labels = [resp[0] for resp in responsaveis]
    responsaveis_data = [resp[1] for resp in responsaveis]
    
    # Solicitantes
    solicitantes = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id)
    ).join(Tarefa, Tarefa.solicitante_id == Usuario.id)\
    .group_by(Usuario.nome).all()
    solicitantes_labels = [solic[0] for solic in solicitantes]
    solicitantes_data = [solic[1] for solic in solicitantes]
    
    return render_template('tarefas/dashboard_tarefas.html',
        total_tarefas=total_tarefas,
        tarefas_em_andamento=tarefas_em_andamento,
        tarefas_concluidas=tarefas_concluidas,
        tarefas_atrasadas=tarefas_atrasadas,
        categorias_labels=categorias_labels,
        categorias_data=categorias_data,
        unidades_labels=unidades_labels,
        unidades_data=unidades_data,
        origens_labels=origens_labels,
        origens_data=origens_data,
        responsaveis_labels=responsaveis_labels,
        responsaveis_data=responsaveis_data,
        solicitantes_labels=solicitantes_labels,
        solicitantes_data=solicitantes_data
    )

@api_bp.route('/tarefas/dashboard-data')
@login_required
def get_dashboard_data():
    """Retorna dados do dashboard filtrados por período."""
    try:
        period = request.args.get('period', 'week')
        
        # Definir data inicial baseada no período
        hoje = datetime.now()
        if period == 'week':
            data_inicial = hoje - timedelta(days=7)
        elif period == 'month':
            data_inicial = hoje - timedelta(days=30)
        elif period == 'year':
            data_inicial = hoje - timedelta(days=365)
        else:
            return jsonify({'error': 'Período inválido'}), 400
            
        # Query base filtrada por período
        base_query = Tarefa.query.filter(Tarefa.data_criacao >= data_inicial)
        
        # Estatísticas
        stats = {
            'total': base_query.count(),
            'em_andamento': base_query.filter_by(status='Em execução').count(),
            'concluidas': base_query.filter_by(status='Concluída').count(),
            'atrasadas': base_query.filter_by(status='Em atraso').count()
        }
        
        # Dados dos gráficos
        # Categorias
        categorias = db.session.query(
            CategoriaTarefa.nome,
            func.count(Tarefa.id)
        ).join(Tarefa).filter(
            Tarefa.data_criacao >= data_inicial
        ).group_by(CategoriaTarefa.nome).all()
        
        # Unidades
        unidades = db.session.query(
            UnidadeLocal.descricao,
            func.count(Tarefa.id)
        ).join(Tarefa).filter(
            Tarefa.data_criacao >= data_inicial
        ).group_by(UnidadeLocal.descricao).all()
        
        # Origens
        origens = db.session.query(
            OrigemTarefa.nome,
            func.count(Tarefa.id)
        ).join(Tarefa).filter(
            Tarefa.data_criacao >= data_inicial
        ).group_by(OrigemTarefa.nome).all()
        
        # Responsáveis
        responsaveis = db.session.query(
            Usuario.nome,
            func.count(Tarefa.id)
        ).join(Tarefa, Tarefa.responsavel_id == Usuario.id).filter(
            Tarefa.data_criacao >= data_inicial
        ).group_by(Usuario.nome).all()
        
        # Solicitantes
        solicitantes = db.session.query(
            Usuario.nome,
            func.count(Tarefa.id)
        ).join(Tarefa, Tarefa.solicitante_id == Usuario.id).filter(
            Tarefa.data_criacao >= data_inicial
        ).group_by(Usuario.nome).all()
        
        charts = {
            'categoriasChart': {
                'labels': [cat[0] for cat in categorias],
                'data': [cat[1] for cat in categorias]
            },
            'unidadesChart': {
                'labels': [uni[0] for uni in unidades],
                'data': [uni[1] for uni in unidades]
            },
            'origensChart': {
                'labels': [orig[0] for orig in origens],
                'data': [orig[1] for orig in origens]
            },
            'responsaveisChart': {
                'labels': [resp[0] for resp in responsaveis],
                'data': [resp[1] for resp in responsaveis]
            },
            'solicitantesChart': {
                'labels': [solic[0] for solic in solicitantes],
                'data': [solic[1] for solic in solicitantes]
            }
        }
        
        return jsonify({
            'stats': stats,
            'charts': charts
        })
        
    except Exception as e:
        print(f"Erro ao buscar dados do dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Registrar os blueprints
def init_app(app):
    app.register_blueprint(tarefas_bp)
    app.register_blueprint(api_bp) 

