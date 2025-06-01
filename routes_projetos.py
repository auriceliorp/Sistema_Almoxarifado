te, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.item import Item
from app.models.fornecedor import Fornecedor
from app.models.movimento import EntradaMaterial, EntradaItem
from app.services.almoxarifado import AlmoxarifadoService
from app.utils.exceptions import ItemNaoEncontradoError
from app.utils.decorators import admin_required
from app.blueprints.almoxarifado.entrada import bp
from datetime import datetime

@bp.route('/')
@login_required
def lista_entradas():
    """Lista todas as entradas de material."""
    page = request.args.get('page', 1, type=int)
    filtro = request.args.get('filtro', 'nota')
    busca = request.args.get('busca', '').strip().lower()
    
    entradas = AlmoxarifadoService.buscar_entradas(
        page=page,
        filtro=filtro,
        busca=busca
    )
    
    return render_template(
        'entrada/list.html',
        entradas=entradas,
        filtro=filtro,
        busca=busca
    )

@bp.route('/nova', methods=['GET', 'POST'])
@login_required
@admin_required
def nova_entrada():
    """Cadastra uma nova entrada de material."""
    if request.method == 'POST':
        try:
            entrada = AlmoxarifadoService.registrar_entrada(
                data_entrada=datetime.strptime(request.form.get('data_entrada'), '%Y-%m-%d'),
                fornecedor_id=request.form.get('fornecedor'),
                numero_nota=request.form.get('numero_nota'),
                valor_total=float(request.form.get('valor_total')),
                observacao=request.form.get('observacao'),
                usuario_id=current_user.id
            )
            flash('Entrada registrada com sucesso!', 'success')
            return redirect(url_for('almoxarifado.entrada.lista_entradas'))
        except Exception as e:
            flash(f'Erro ao registrar entrada: {str(e)}', 'danger')
    
    fornecedores = Fornecedor.query.all()
    return render_template('entrada/form.html', fornecedores=fornecedores)

@bp.route('/<int:id>')
@login_required
def visualizar_entrada(id):
    """Visualiza os detalhes de uma entrada específica."""
    entrada = EntradaMaterial.query.get_or_404(id)
    return render_template('entrada/detail.html', entrada=entrada)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_entrada(id):
    """Edita uma entrada existente."""
    entrada = EntradaMaterial.query.get_or_404(id)
    
    if entrada.status == 'Finalizada':
        flash('Não é possível editar uma entrada finalizada.', 'warning')
        return redirect(url_for('almoxarifado.entrada.lista_entradas'))
    
    if request.method == 'POST':
        try:
            AlmoxarifadoService.atualizar_entrada(
                entrada_id=id,
                data_entrada=datetime.strptime(request.form.get('data_entrada'), '%Y-%m-%d'),
                fornecedor_id=request.form.get('fornecedor'),
                numero_nota=request.form.get('numero_nota'),
                valor_total=float(request.form.get('valor_total')),
                observacao=request.form.get('observacao')
            )
            flash('Entrada atualizada com sucesso!', 'success')
            return redirect(url_for('almoxarifado.entrada.lista_entradas'))
        except Exception as e:
            flash(f'Erro ao atualizar entrada: {str(e)}', 'danger')
    
    fornecedores = Fornecedor.query.all()
    return render_template('entrada/form.html', entrada=entrada, fornecedores=fornecedores)

@bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
@admin_required
def excluir_entrada(id):
    """Exclui uma entrada existente."""
    entrada = EntradaMaterial.query.get_or_404(id)
    
    if entrada.status == 'Finalizada':
        flash('Não é possível excluir uma entrada finalizada.', 'warning')
        return redirect(url_for('almoxarifado.entrada.lista_entradas'))
    
    try:
        AlmoxarifadoService.excluir_entrada(id)
        flash('Entrada excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir entrada: {str(e)}', 'danger')
    
    return redirect(url_for('almoxarifado.entrada.lista_entradas'))

@bp.route('/imprimir/<int:id>')
@login_required
def imprimir_entrada(id):
    """Gera uma versão para impressão da entrada."""
    entrada = EntradaMaterial.query.get_or_404(id)
    return render_template('entrada/print.html', entrada=entrada) 
