from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Tarefa, CategoriaTarefa, OrigemTarefa, UnidadeLocal, Usuario  # Alterado Area para UnidadeLocal
from datetime import datetime
from extensoes import csrf

bp = Blueprint('tarefas', __name__, url_prefix='/tarefas')
api_bp = Blueprint('tarefas_api', __name__, url_prefix='/api')

@bp.route('/')
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
    unidades_locais = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()  # Alterado
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
                         unidades_locais=unidades_locais,  # Alterado
                         usuarios=usuarios,
                         total_tarefas=total_tarefas,
                         tarefas_nao_iniciadas=tarefas_nao_iniciadas,
                         tarefas_em_execucao=tarefas_em_execucao,
                         tarefas_suspensas=tarefas_suspensas,
                         tarefas_concluidas=tarefas_concluidas,
                         tarefas_em_atraso=tarefas_em_atraso)

@bp.route('/nova', methods=['GET', 'POST'])
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
            unidade_local_id = request.form.get('unidade_local_id')  # Alterado
            origem_id = request.form.get('origem_id')
            responsavel_id = request.form.get('responsavel_id')
            solicitante_id = request.form.get('solicitante_id')
            quantidade_acoes = request.form.get('quantidade_acoes', type=int)
            prioridade = request.form.get('prioridade')
            status = request.form.get('status')
            data_inicio = request.form.get('data_inicio')
            data_termino = request.form.get('data_termino')
            observacoes = request.form.get('observacoes')
            unidades_locais = UnidadeLocal.query.all()  # Adicione esta linha
            
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
                unidade_local_id=unidade_local_id,  # Alterado
                origem_id=origem_id,
                responsavel_id=responsavel_id,
                solicitante_id=solicitante_id or current_user.id,
                quantidade_acoes=quantidade_acoes,
                prioridade=prioridade,
                status=status,
                data_inicio=data_inicio,
                data_termino=data_termino,
                observacoes=observacoes
                unidades_locais=unidades_locais)  # Adicione esta variável
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
    unidades_locais = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()  # Alterado
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    
    return render_template('tarefas/nova_tarefa.html',
                         categorias=categorias,
                         origens=origens,
                         unidades_locais=unidades_locais,  # Alterado
                         usuarios=usuarios)

@bp.route('/editar/<int:tarefa_id>', methods=['GET', 'POST'])
@login_required
def editar_tarefa(tarefa_id):
    """Edita uma tarefa existente."""
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            tarefa.titulo = request.form.get('titulo')
            tarefa.numero_sei = request.form.get('numero_sei')
            tarefa.categoria_id = request.form.get('categoria_id')
            tarefa.resumo = request.form.get('resumo')
            tarefa.unidade_local_id = request.form.get('unidade_local_id')  # Alterado
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
            return redirect(url_for('tarefas.editar_tarefa', tarefa_id=tarefa_id))
    
    # GET: Renderizar formulário
    categorias = CategoriaTarefa.query.order_by(CategoriaTarefa.nome).all()
    origens = OrigemTarefa.query.order_by(OrigemTarefa.nome).all()
    unidades_locais = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()  # Alterado
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    
    return render_template('tarefas/nova_tarefa.html',
                         tarefa=tarefa,
                         categorias=categorias,
                         origens=origens,
                         unidades_locais=unidades_locais,  # Alterado
                         usuarios=usuarios)

@bp.route('/excluir/<int:tarefa_id>')
@login_required
def excluir_tarefa(tarefa_id):
    """Exclui uma tarefa."""
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        db.session.delete(tarefa)
        db.session.commit()
        flash('Tarefa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tarefa: {str(e)}', 'error')
    
    return redirect(url_for('tarefas.lista_tarefas'))

# API Routes
@bp.route('/api/tarefas')
@login_required
def get_tarefas():
    """Retorna todas as tarefas em formato JSON."""
    tarefas = Tarefa.query.all()
    return jsonify([t.to_dict() for t in tarefas])

@api_bp.route('/tarefas', methods=['GET'])
@login_required
def get_tarefas():
    try:
        unidade_local = request.args.get('unidade_local')  # Alterado
        prioridade = request.args.get('prioridade')
        status = request.args.get('status')
        responsavel = request.args.get('responsavel')
        
        query = Tarefa.query
        
        if unidade_local:  # Alterado
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
            unidade_local_id=data.get('unidade_local_id'),  # Alterado
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

@api_bp.route('/tarefas/<int:tarefa_id>', methods=['PUT'])
@login_required
def atualizar_tarefa(tarefa_id):
    """Atualiza uma tarefa existente."""
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
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
        if 'unidade_local_id' in data:  # Alterado
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

@api_bp.route('/tarefas/<int:tarefa_id>', methods=['DELETE'])
@login_required
def deletar_tarefa(tarefa_id):
    """Deleta uma tarefa."""
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        db.session.delete(tarefa)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/<int:tarefa_id>', methods=['DELETE'])
@login_required
def excluir_tarefa(tarefa_id):
    try:
        tarefa = Tarefa.query.get_or_404(tarefa_id)
        db.session.delete(tarefa)
        db.session.commit()
        return jsonify({'message': 'Tarefa excluída com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir tarefa: {str(e)}")
        return jsonify({'error': str(e)}), 500
