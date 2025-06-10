# routes_area_ul.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import Area, Local, UnidadeLocal, NaturezaDespesa, Grupo

# Alterando o nome do blueprint para area_ul_bp
area_ul_bp = Blueprint('area_ul_bp', __name__, url_prefix='/organizacao')

# ------------------------- ROTA: DASHBOARD ORGANIZAÇÃO ------------------------- #
@area_ul_bp.route('/')
@login_required
def dashboard_organizacao():
    nds = NaturezaDespesa.query.all()
    grupos = Grupo.query.all()
    areas = Local.query.all()
    uls = UnidadeLocal.query.all()
    return render_template('organizacao/dashboard_organizacao.html',
                           nds=nds, grupos=grupos, areas=areas, uls=uls)

# ------------------------- LISTA DE LOCAIS ------------------------- #
@area_ul_bp.route('/locais')
@login_required
def lista_locais():  # Mantendo o nome da função como lista_locais
    locais = Local.query.all()
    return render_template('partials/area/lista_area.html', areas=locais)

# ------------------------- LISTA DE UNIDADES LOCAIS ------------------------- #
@area_ul_bp.route('/uls')
@login_required
def lista_uls():
    uls = Local.query.all()
    return render_template('partials/ul/lista_ul.html', uls=uls)

# ------------------------- NOVO LOCAL ------------------------- #
@area_ul_bp.route('/locais/novo', methods=['GET', 'POST'])
@login_required
def novo_local():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome do local é obrigatório.')
            return redirect(url_for('area_ul_bp.novo_local'))
        db.session.add(Local(descricao=nome))
        db.session.commit()
        flash('Local cadastrado com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('partials/area/form_area.html')

# ------------------------- EDITAR LOCAL ------------------------- #
@area_ul_bp.route('/locais/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_local(id):
    local = Local.query.get_or_404(id)
    if request.method == 'POST':
        local.descricao = request.form.get('nome')
        db.session.commit()
        flash('Local atualizado com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('partials/area/form_area.html', area=local)

# ------------------------- NOVA UNIDADE LOCAL ------------------------- #
@area_ul_bp.route('/uls/novo', methods=['GET', 'POST'])
@login_required
def nova_ul():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('O nome da UL é obrigatório.')
            return redirect(url_for('area_ul_bp.nova_ul'))
        db.session.add(Local(descricao=nome))
        db.session.commit()
        flash('Unidade Local cadastrada com sucesso!')
        return redirect(url_for('area_ul_bp.lista_uls'))
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
        return redirect(url_for('area_ul_bp.lista_uls'))
    return render_template('partials/ul/form_ul.html', ul=ul, locais=locais)

# ------------------------- EXCLUIR LOCAL ------------------------- #
@area_ul_bp.route('/locais/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_local(id):
    local = Local.query.get_or_404(id)
    try:
        db.session.delete(local)
        db.session.commit()
        flash('Local excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir Local: {e}', 'danger')
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

