# routes_painel.py
# CRUD para o Painel de Contratações

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from extensoes import db
from models import PainelContratacao, Usuario

painel_bp = Blueprint('painel_bp', __name__, url_prefix='/painel')


# -------------------- LISTAGEM DE PROCESSOS COM FILTROS -------------------- #
@painel_bp.route('/lista')
@login_required
def lista_painel():
    ano = request.args.get('ano')
    modalidade = request.args.get('modalidade')
    status = request.args.get('status')
    solicitante_id = request.args.get('solicitante_id')
    numero_sei = request.args.get('numero_sei')
    objeto = request.args.get('objeto')

    query = PainelContratacao.query.filter_by(excluido=False)

    if ano:
        query = query.filter(PainelContratacao.ano == ano)
    if modalidade:
        query = query.filter(PainelContratacao.modalidade.ilike(f"%{modalidade}%"))
    if status:
        query = query.filter(PainelContratacao.status == status)
    if solicitante_id:
        query = query.filter(PainelContratacao.solicitante_id == solicitante_id)
    if numero_sei:
        query = query.filter(PainelContratacao.numero_sei.ilike(f"%{numero_sei}%"))
    if objeto:
        query = query.filter(PainelContratacao.objeto.ilike(f"%{objeto}%"))

    processos = (
        query
        .options(joinedload(PainelContratacao.solicitante))
        .order_by(PainelContratacao.ano.desc(), PainelContratacao.data_abertura.desc())
        .all()
    )
    usuarios = Usuario.query.order_by(Usuario.nome).all()

    return render_template('painel/lista_painel.html', processos=processos, usuarios=usuarios, usuario=current_user)


# -------------------- NOVO PROCESSO -------------------- #
@painel_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_painel():
    if request.method == 'POST':
        try:
            ano = int(request.form.get('ano'))
            data_abertura = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d') if request.form.get('data_abertura') else None
            data_homologacao = datetime.strptime(request.form.get('data_homologacao'), '%Y-%m-%d') if request.form.get('data_homologacao') else None
            periodo_dias = request.form.get('periodo_dias')
            numero_sei = request.form.get('numero_sei')
            modalidade = request.form.get('modalidade')
            registro_precos = request.form.get('registro_precos')
            orgaos_participantes = request.form.get('orgaos_participantes')
            numero_licitacao = request.form.get('numero_licitacao')
            parecer_juridico = request.form.get('parecer_juridico')
            fundamentacao_legal = request.form.get('fundamentacao_legal')
            objeto = request.form.get('objeto')
            natureza_despesa = request.form.get('natureza_despesa')

            valor_estimado = request.form.get('valor_estimado', '').replace('.', '').replace(',', '.')
            valor_homologado = request.form.get('valor_homologado', '').replace('.', '').replace(',', '.')

            percentual_economia = request.form.get('percentual_economia')
            impugnacao = request.form.get('impugnacao')
            recurso = request.form.get('recurso')
            itens_desertos = request.form.get('itens_desertos')
            responsavel_conducao = request.form.get('responsavel_conducao')
            solicitante_id = request.form.get('solicitante_id') or None
            setor_responsavel = request.form.get('setor_responsavel')
            status = request.form.get('status')

            processo = PainelContratacao(
                ano=ano,
                data_abertura=data_abertura,
                data_homologacao=data_homologacao,
                periodo_dias=int(periodo_dias) if periodo_dias else None,
                numero_sei=numero_sei,
                modalidade=modalidade,
                registro_precos=registro_precos,
                orgaos_participantes=orgaos_participantes,
                numero_licitacao=numero_licitacao,
                parecer_juridico=parecer_juridico,
                fundamentacao_legal=fundamentacao_legal,
                objeto=objeto,
                natureza_despesa=natureza_despesa,
                valor_estimado=float(valor_estimado) if valor_estimado else None,
                valor_homologado=float(valor_homologado) if valor_homologado else None,
                percentual_economia=percentual_economia,
                impugnacao=impugnacao,
                recurso=recurso,
                itens_desertos=itens_desertos,
                responsavel_conducao=responsavel_conducao,
                solicitante_id=int(solicitante_id) if solicitante_id else None,
                setor_responsavel=setor_responsavel,
                status=status,
                excluido=False
            )

            db.session.add(processo)
            db.session.commit()
            flash('Processo cadastrado com sucesso!', 'success')
            return redirect(url_for('painel_bp.lista_painel'))

        except Exception as e:
            print(f"Erro ao salvar processo: {e}")
            flash('Erro ao salvar processo. Verifique os dados e tente novamente.', 'danger')

    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('painel/novo_painel.html', usuarios=usuarios, usuario=current_user)


# -------------------- EDITAR PROCESSO -------------------- #
@painel_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_painel(id):
    processo = PainelContratacao.query.get_or_404(id)

    if request.method == 'POST':
        try:
            processo.ano = int(request.form.get('ano'))
            processo.data_abertura = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d') if request.form.get('data_abertura') else None
            processo.data_homologacao = datetime.strptime(request.form.get('data_homologacao'), '%Y-%m-%d') if request.form.get('data_homologacao') else None
            processo.periodo_dias = int(request.form.get('periodo_dias')) if request.form.get('periodo_dias') else None
            processo.numero_sei = request.form.get('numero_sei')
            processo.modalidade = request.form.get('modalidade')
            processo.registro_precos = request.form.get('registro_precos')
            processo.orgaos_participantes = request.form.get('orgaos_participantes')
            processo.numero_licitacao = request.form.get('numero_licitacao')
            processo.parecer_juridico = request.form.get('parecer_juridico')
            processo.fundamentacao_legal = request.form.get('fundamentacao_legal')
            processo.objeto = request.form.get('objeto')
            processo.natureza_despesa = request.form.get('natureza_despesa')

            valor_estimado = request.form.get('valor_estimado', '').replace('.', '').replace(',', '.')
            valor_homologado = request.form.get('valor_homologado', '').replace('.', '').replace(',', '.')

            processo.valor_estimado = float(valor_estimado) if valor_estimado else None
            processo.valor_homologado = float(valor_homologado) if valor_homologado else None
            processo.percentual_economia = request.form.get('percentual_economia')
            processo.impugnacao = request.form.get('impugnacao')
            processo.recurso = request.form.get('recurso')
            processo.itens_desertos = request.form.get('itens_desertos')
            processo.responsavel_conducao = request.form.get('responsavel_conducao')
            processo.solicitante_id = int(request.form.get('solicitante_id')) if request.form.get('solicitante_id') else None
            processo.setor_responsavel = request.form.get('setor_responsavel')
            processo.status = request.form.get('status')

            db.session.commit()
            flash('Processo atualizado com sucesso!', 'success')
            return redirect(url_for('painel_bp.lista_painel'))

        except Exception as e:
            print(f"Erro ao atualizar processo: {e}")
            flash('Erro ao atualizar processo. Verifique os dados e tente novamente.', 'danger')

    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('painel/editar_painel.html', processo=processo, usuarios=usuarios, usuario=current_user)


# -------------------- EXCLUSÃO LÓGICA -------------------- #
@painel_bp.route('/excluir/<int:id>')
@login_required
def excluir_painel(id):
    processo = PainelContratacao.query.get_or_404(id)
    processo.excluido = True
    db.session.commit()
    flash(f'O processo {processo.numero_sei} foi excluído logicamente.', 'success')
    return redirect(url_for('painel_bp.lista_painel'))


# -------------------- VISUALIZAR PROCESSO -------------------- #
@painel_bp.route('/visualizar/<int:id>')
@login_required
def visualizar_painel(id):
    processo = PainelContratacao.query.get_or_404(id)
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('painel/visualizar_painel.html', processo=processo, usuarios=usuarios, usuario=current_user)


# -------------------- DASHBOARD DE COMPRAS -------------------- #
from flask import Blueprint

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/compras')
@login_required
def dashboard_compras():
    total_processos = db.session.query(func.count()).select_from(PainelContratacao).filter_by(excluido=False).scalar()

    total_estimado = db.session.query(func.sum(PainelContratacao.valor_estimado))\
        .filter(PainelContratacao.excluido == False).scalar() or 0

    total_com_sei = db.session.query(func.count()).select_from(PainelContratacao)\
        .filter(PainelContratacao.numero_sei != None, PainelContratacao.numero_sei != '', PainelContratacao.excluido == False).scalar()

    total_concluidos = db.session.query(func.count()).select_from(PainelContratacao)\
        .filter(PainelContratacao.status == 'Concluido', PainelContratacao.excluido == False).scalar()

    modalidades = db.session.query(PainelContratacao.modalidade, func.count())\
        .filter(PainelContratacao.excluido == False)\
        .group_by(PainelContratacao.modalidade).all()

    labels_modalidades = [m[0] or 'Não Informada' for m in modalidades]
    valores_modalidades = [m[1] for m in modalidades]

    ultimos_processos = db.session.query(PainelContratacao)\
        .filter(PainelContratacao.excluido == False)\
        .order_by(PainelContratacao.data_abertura.desc())\
        .limit(5).all()

    return render_template('dashboard_compras.html',
        total_processos=total_processos,
        total_estimado=total_estimado,
        total_com_sei=total_com_sei,
        total_concluidos=total_concluidos,
        labels_modalidades=labels_modalidades,
        valores_modalidades=valores_modalidades,
        ultimos_processos=ultimos_processos,
        usuario=current_user
    )
