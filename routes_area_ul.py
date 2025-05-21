# routes_area_ul.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Local, UnidadeLocal, NaturezaDespesa, Grupo

# Criação do blueprint
area_ul_bp = Blueprint('area_ul_bp', __name__, url_prefix='/organizacao')

# ------------------------- ROTA: LISTAR LOCAIS ------------------------- #
@area_ul_bp.route('/locais')
@login_required
def lista_locais():
    locais = Local.query.all()
    return render_template('lista_locais.html', locais=locais)

# ------------------------- ROTA: NOVO LOCAL ------------------------- #
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
        flash('Local cadastrado com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('novo_local.html')

# ------------------------- ROTA: EDITAR LOCAL ------------------------- #
@area_ul_bp.route('/locais/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_local(id):
    local = Local.query.get_or_404(id)
    if request.method == 'POST':
        local.descricao = request.form.get('descricao')
        db.session.commit()
        flash('Local atualizado com sucesso!')
        return redirect(url_for('area_ul_bp.lista_locais'))
    return render_template('editar_local.html', local=local)

# ------------------------- ROTA: LISTAR UNIDADES LOCAIS ------------------------- #
@area_ul_bp.route('/uls')
@login_required
def lista_uls():
    uls = UnidadeLocal.query.all()
    return render_template('lista_uls.html', uls=uls)

# ------------------------- ROTA: NOVA UNIDADE LOCAL ------------------------- #
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
    return render_template('novo_ul.html', locais=locais)

# ------------------------- ROTA: EDITAR UNIDADE LOCAL ------------------------- #
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
    return render_template('editar_ul.html', ul=ul, locais=locais)

# ------------------------- ROTA: DASHBOARD ORGANIZAÇÃO ------------------------- #
@area_ul_bp.route('/')
@login_required
def dashboard_organizacao():
    """
    Rota principal para o dashboard de Organização Administrativa.
    Carrega os dados necessários para exibição das abas:
    - Naturezas de Despesa
    - Grupos de Itens
    - Unidades Locais
    - Áreas (Locais)
    """
    nds = NaturezaDespesa.query.all()
    grupos = Grupo.query.all()
    uls = UnidadeLocal.query.all()
    areas = Local.query.all()
    return render_template(
        'organizacao/dashboard_organizacao.html',
        nds=nds, grupos=grupos, uls=uls, areas=areas
    )

