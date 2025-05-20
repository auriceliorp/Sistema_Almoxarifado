routes_area_ul.py

Rotas para gerenciamento de Áreas e Unidades Locais

from flask import Blueprint, render_template, request, redirect, url_for, flash from flask_login import login_required from extensoes import db from models import UnidadeLocal, Local

area_ul_bp = Blueprint('area_ul_bp', name, url_prefix='/ul')

------------------------------ CRUD DE ÁREAS ------------------------------

@area_ul_bp.route('/areas') @login_required def lista_areas(): areas = Local.query.order_by(Local.descricao).all() return render_template('partials/area/lista_area.html', areas=areas)

@area_ul_bp.route('/areas/nova', methods=['GET', 'POST']) @login_required def nova_area(): if request.method == 'POST': descricao = request.form.get('descricao') if not descricao: flash('Descrição é obrigatória.', 'danger') return redirect(url_for('area_ul_bp.nova_area'))

nova = Local(descricao=descricao)
    db.session.add(nova)
    db.session.commit()
    flash('Área cadastrada com sucesso!', 'success')
    return redirect(url_for('main.dashboard_organizacao'))

return render_template('partials/area/form_area.html', area=None)

@area_ul_bp.route('/areas/editar/int:id', methods=['GET', 'POST']) @login_required def editar_area(id): area = Local.query.get_or_404(id) if request.method == 'POST': descricao = request.form.get('descricao') if not descricao: flash('Descrição é obrigatória.', 'danger') return redirect(url_for('area_ul_bp.editar_area', id=id))

area.descricao = descricao
    db.session.commit()
    flash('Área atualizada com sucesso!', 'success')
    return redirect(url_for('main.dashboard_organizacao'))

return render_template('partials/area/form_area.html', area=area)

@area_ul_bp.route('/areas/excluir/int:id', methods=['POST']) @login_required def excluir_area(id): area = Local.query.get_or_404(id) db.session.delete(area) db.session.commit() flash('Área excluída com sucesso!', 'success') return redirect(url_for('main.dashboard_organizacao'))

------------------------------ CRUD DE UNIDADES LOCAIS ------------------------------

@area_ul_bp.route('/') @login_required def lista_ul(): uls = UnidadeLocal.query.order_by(UnidadeLocal.codigo).all() return render_template('partials/ul/lista_ul.html', uls=uls)

@area_ul_bp.route('/novo', methods=['GET', 'POST']) @login_required def nova_ul(): areas = Local.query.order_by(Local.descricao).all()

if request.method == 'POST':
    codigo = request.form.get('codigo')
    descricao = request.form.get('descricao')
    local_id = request.form.get('local_id')

    if not codigo or not descricao or not local_id:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('area_ul_bp.nova_ul'))

    nova = UnidadeLocal(codigo=codigo, descricao=descricao, local_id=local_id)
    db.session.add(nova)
    db.session.commit()
    flash('Unidade Local cadastrada com sucesso!', 'success')
    return redirect(url_for('main.dashboard_organizacao'))

return render_template('partials/ul/form_ul.html', ul=None, locais=areas)

@area_ul_bp.route('/editar/int:id', methods=['GET', 'POST']) @login_required def editar_ul(id): ul = UnidadeLocal.query.get_or_404(id) areas = Local.query.order_by(Local.descricao).all()

if request.method == 'POST':
    codigo = request.form.get('codigo')
    descricao = request.form.get('descricao')
    local_id = request.form.get('local_id')

    if not codigo or not descricao or not local_id:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('area_ul_bp.editar_ul', id=id))

    ul.codigo = codigo
    ul.descricao = descricao
    ul.local_id = local_id
    db.session.commit()
    flash('Unidade Local atualizada com sucesso!', 'success')
    return redirect(url_for('main.dashboard_organizacao'))

return render_template('partials/ul/form_ul.html', ul=ul, locais=areas)

@area_ul_bp.route('/excluir/int:id', methods=['POST']) @login_required def excluir_ul(id): ul = UnidadeLocal.query.get_or_404(id) db.session.delete(ul) db.session.commit() flash('Unidade Local excluída com sucesso!', 'success') return redirect(url_for('main.dashboard_organizacao'))

