# routes_area_ul.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import Area, Local, UnidadeLocal, NaturezaDespesa, Grupo

# Criação do blueprint
area_ul_bp = Blueprint('area_ul', __name__, url_prefix='/organizacao')

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
@area_ul_bp.route('/areas')
@login_required
def lista_areas():
    areas = Area.query.all()
    return render_template('partials/area/lista_area.html', areas=areas)

# ------------------------- LISTA DE UNIDADES LOCAIS ------------------------- #
@area_ul_bp.route('/uls')
@login_required
def lista_uls():
    uls = Local.query.all()
    return render_template('partials/ul/lista_ul.html', uls=uls)

# ------------------------- NOVA ÁREA ------------------------- #
@area_ul_bp.route('/areas/novo', methods=['GET', 'POST'])
@login_required
def nova_area():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome da área é obrigatório.')
            return redirect(url_for('area_ul.nova_area'))
        db.session.add(Area(nome=nome))
        db.session.commit()
        flash('Área cadastrada com sucesso!')
        return redirect(url_for('area_ul.lista_areas'))
    return render_template('partials/area/form_area.html')

# ------------------------- EDITAR ÁREA ------------------------- #
@area_ul_bp.route('/areas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_area(id):
    area = Area.query.get_or_404(id)
    if request.method == 'POST':
        area.nome = request.form.get('nome')
        db.session.commit()
        flash('Área atualizada com sucesso!')
        return redirect(url_for('area_ul.lista_areas'))
    return render_template('partials/area/form_area.html', area=area)

# ------------------------- NOVA UNIDADE LOCAL ------------------------- #
@area_ul_bp.route('/uls/novo', methods=['GET', 'POST'])
@login_required
def nova_ul():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome da UL é obrigatório.')
            return redirect(url_for('area_ul.nova_ul'))
        db.session.add(Local(descricao=nome))
        db.session.commit()
        flash('Unidade Local cadastrada com sucesso!')
        return redirect(url_for('area_ul.lista_uls'))
    return render_template('partials/ul/form_ul.html')

# ------------------------- EDITAR UNIDADE LOCAL ------------------------- #
@area_ul_bp.route('/uls/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ul(id):
    ul = UnidadeLocal.query.get_or_404(id)
    locais = Local.query.all()
    if request.method == 'POST':
        ul.descricao = request.form.get('descricao')
        ul.local_id = request.form.get('local_id')
        db.session.commit()
        flash('Unidade Local atualizada com sucesso!')
        return redirect(url_for('area_ul.lista_uls'))
    return render_template('partials/ul/form_ul.html', ul=ul, locais=locais)

# ------------------------- EXCLUIR LOCAL (Área) ------------------------- #
@area_ul_bp.route('/areas/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_area(id):
    area = Area.query.get_or_404(id)
    try:
        db.session.delete(area)
        db.session.commit()
        flash('Área excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir Área: {e}', 'danger')
    return redirect(url_for('area_ul.lista_areas'))

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
    return redirect(url_for('area_ul.lista_uls'))


