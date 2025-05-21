# routes_area_ul.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import Local, UnidadeLocal, NaturezaDespesa, Grupo

# Criação do blueprint
area_ul_bp = Blueprint('area_ul_bp', __name__, url_prefix='/organizacao')

# ------------------------- ROTA: DASHBOARD ORGANIZAÇÃO (não está mais em uso) ------------------------- #
@area_ul_bp.route('/')
@login_required
def dashboard_organizacao():
    """
    (Obsoleta se não usar abas) Rota antiga de dashboard de organização administrativa.
    """
    nds = NaturezaDespesa.query.all()
    grupos = Grupo.query.all()
    areas = Local.query.all()
    uls = UnidadeLocal.query.all()
    return render_template('organizacao/dashboard_organizacao.html',
                           nds=nds, grupos=grupos, areas=areas, uls=uls)

# ------------------------- LISTA DE ÁREAS ------------------------- #
@area_ul_bp.route('/locais')
@login_required
def lista_locais():
    areas = Local.query.order_by(Local.descricao).all()
    return render_template('partials/area/lista_area.html', areas=areas)

# ------------------------- LISTA DE UNIDADES LOCAIS ------------------------- #
@area_ul_bp.route('/uls')
@login_required
def lista_uls():
    uls = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all()
    return render_template('partials/ul/lista_ul.html', uls=uls)

# ------------------------- NOVA ÁREA ------------------------- #
@area_ul_bp.route('/locais/novo', methods=['GET', 'POST'])
@login_required
def novo_local():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        if not descricao:
            flash('Descrição é obrigatória.')
            return redirect(url_for('area_ul_bp.novo_local'))
        db.session.add(Local(descricao=descricao))
        db.session.commit()
        flash('Área cadastrada com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('partials/area/form_area.html')

# ------------------------- EDITAR ÁREA ------------------------- #
@area_ul_bp.route('/locais/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_local(id):
    local = Local.query.get_or_404(id)
    if request.method == 'POST':
        local.descricao = request.form.get('descricao')
        db.session.commit()
        flash('Área atualizada com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('partials/area/form_area.html', local=local)

# ------------------------- NOVA UNIDADE LOCAL ------------------------- #
@area_ul_bp.route('/uls/novo', methods=['GET', 'POST'])
@login_required
def novo_ul():
    locais = Local.query.all()
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')
        local_id = request.form.get('local_id')
        if not codigo or not descricao or not local_id:
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('area_ul_bp.novo_ul'))
        ul = UnidadeLocal(codigo=codigo, descricao=descricao, local_id=local_id)
        db.session.add(ul)
        db.session.commit()
        flash('Unidade Local cadastrada com sucesso!')
        return redirect(url_for('area_ul_bp.lista_uls'))
    return render_template('partials/ul/form_ul.html', locais=locais)

# ------------------------- EDITAR UNIDADE LOCAL ------------------------- #
@area_ul_bp.route('/uls/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ul(id):
    ul = UnidadeLocal.query.get_or_404(id)
    locais = Local.query.all()
    if request.method == 'POST':
        ul.codigo = request.form.get('codigo')
        ul.descricao = request.form.get('descricao')
        ul.local_id = request.form.get('local_id')
        db.session.commit()
        flash('Unidade Local atualizada com sucesso!')
        return redirect(url_for('area_ul_bp.lista_uls'))
    return render_template('partials/ul/form_ul.html', ul=ul, locais=locais)

# ------------------------- EXCLUIR LOCAL (Área) ------------------------- #
@area_ul_bp.route('/locais/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_local(id):
    local = Local.query.get_or_404(id)
    try:
        db.session.delete(local)
        db.session.commit()
        flash('Área excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir Área: {e}', 'danger')
    return redirect(url_for('area_ul_bp.lista_locais'))

# ------------------------- EXCLUIR UNIDADE LOCAL ------------------------- #
@area_ul_bp.route('/uls/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_ul(id):
    ul = UnidadeLocal.query.get_or_404(id)
    try:
        db.session.delete(ul)
        db.session.commit()
        flash('Unidade Local excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir Unidade Local: {e}', 'danger')
    return redirect(url_for('area_ul_bp.lista_uls'))

