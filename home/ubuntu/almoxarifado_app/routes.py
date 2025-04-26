# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from .models import NaturezaDespesa, Item, Usuario, Requisicao, RequisicaoItem, MovimentoEstoque, Perfil
from .database import db
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from sqlalchemy import func, extract
from datetime import datetime, timedelta

# Cria um Blueprint para organizar as rotas relacionadas ao almoxarifado
main_bp = Blueprint("main", __name__)

# --- Decorators para Controle de Acesso ---
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash("Acesso negado. Você precisa ser um administrador.", "danger")
            return redirect(url_for("main.home")) # Redireciona para home logada
        return f(*args, **kwargs)
    return decorated_function

def solicitante_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Permite Admin OU Solicitante acessar rotas de solicitante?
        # Se apenas solicitante: if not current_user.is_solicitante():
        # Se Admin também pode: if not (current_user.is_solicitante() or current_user.is_admin()):
        if not current_user.is_solicitante(): # Apenas solicitantes podem criar requisições, por exemplo
            flash("Acesso negado. Você precisa ser um solicitante.", "danger")
            return redirect(url_for("main.home")) # Redireciona para home logada
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Autenticação ---
@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember_me") == "on"

        user = Usuario.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Email ou senha inválidos.", "danger")
            return render_template("login.html")

        if not user.ativo:
            flash("Este usuário está inativo.", "warning")
            return render_template("login.html")

        login_user(user, remember=remember)
        flash(f"Login bem-sucedido! Bem-vindo, {user.nome}.", "success")

        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("main.home")
        return redirect(next_page)

    return render_template("login.html")

@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado.", "info")
    return redirect(url_for("main.login"))

# --- Rotas Principais ---
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    return redirect(url_for("main.login"))

@main_bp.route("/home")
@login_required
def home():
     # TODO: Criar template index_logged_in.html
     return render_template("index_logged_in.html")

# --- Rotas para Natureza de Despesa (ND) ---
@main_bp.route("/naturezas_despesa", methods=["GET"])
@login_required # Todos logados podem ver
def listar_naturezas_despesa():
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template("naturezas_despesa/list.html", naturezas=nds)

@main_bp.route("/naturezas_despesa/nova", methods=["GET", "POST"])
@admin_required
def criar_natureza_despesa():
    if request.method == "POST":
        codigo = request.form.get("codigo")
        descricao = request.form.get("descricao")
        ativa = request.form.get("ativa") == "on"
        if not codigo or not descricao:
            flash("Código e Descrição são obrigatórios.", "error")
            return render_template("naturezas_despesa/form.html", form_data=request.form), 400
        if NaturezaDespesa.query.filter_by(codigo=codigo).first():
            flash(f"O código {codigo} já está cadastrado.", "error")
            return render_template("naturezas_despesa/form.html", form_data=request.form), 400
        nova_nd = NaturezaDespesa(codigo=codigo, descricao=descricao, ativa=ativa)
        try:
            db.session.add(nova_nd)
            db.session.commit()
            flash("Natureza de Despesa criada com sucesso!", "success")
            return redirect(url_for("main.listar_naturezas_despesa"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar Natureza de Despesa: {e}", "error")
            return render_template("naturezas_despesa/form.html", form_data=request.form), 500
    return render_template("naturezas_despesa/form.html")

@main_bp.route("/naturezas_despesa/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_natureza_despesa(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    if request.method == "POST":
        codigo = request.form.get("codigo")
        descricao = request.form.get("descricao")
        ativa = request.form.get("ativa") == "on"
        if not codigo or not descricao:
            flash("Código e Descrição são obrigatórios.", "error")
            return render_template("naturezas_despesa/form.html", natureza=nd, form_data=request.form), 400
        if nd.codigo != codigo and NaturezaDespesa.query.filter(NaturezaDespesa.id != id, NaturezaDespesa.codigo == codigo).first():
            flash(f"O código {codigo} já está cadastrado para outra Natureza de Despesa.", "error")
            return render_template("naturezas_despesa/form.html", natureza=nd, form_data=request.form), 400
        nd.codigo = codigo
        nd.descricao = descricao
        nd.ativa = ativa
        try:
            db.session.commit()
            flash("Natureza de Despesa atualizada com sucesso!", "success")
            return redirect(url_for("main.listar_naturezas_despesa"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar Natureza de Despesa: {e}", "error")
            return render_template("naturezas_despesa/form.html", natureza=nd, form_data=request.form), 500
    return render_template("naturezas_despesa/form.html", natureza=nd)

@main_bp.route("/naturezas_despesa/<int:id>/excluir", methods=["POST"])
@admin_required
def excluir_natureza_despesa(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    if Item.query.filter_by(natureza_despesa_id=id).first():
        flash("Não é possível excluir esta Natureza de Despesa, pois existem itens vinculados a ela.", "error")
        return redirect(url_for("main.listar_naturezas_despesa"))
    try:
        db.session.delete(nd)
        db.session.commit()
        flash("Natureza de Despesa excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir Natureza de Despesa: {e}", "error")
    return redirect(url_for("main.listar_naturezas_despesa"))

# --- Rotas para Itens ---
@main_bp.route("/itens", methods=["GET"])
@login_required # Todos logados podem ver
def listar_itens():
    itens = Item.query.options(db.joinedload(Item.natureza_despesa)).order_by(Item.nome).all()
    return render_template("itens/list.html", itens=itens)

@main_bp.route("/itens/novo", methods=["GET", "POST"])
@admin_required
def criar_item():
    nds_ativas = NaturezaDespesa.query.filter_by(ativa=True).order_by(NaturezaDespesa.codigo).all()
    if request.method == "POST":
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        unidade_medida = request.form.get("unidade_medida")
        natureza_despesa_id = request.form.get("natureza_despesa_id", type=int)
        estoque_minimo = request.form.get("estoque_minimo", default=0, type=int)
        ponto_ressuprimento = request.form.get("ponto_ressuprimento", default=0, type=int)
        saldo_atual = 0
        ativo = request.form.get("ativo") == "on"
        if not nome or not unidade_medida or not natureza_despesa_id:
            flash("Nome, Unidade de Medida e Natureza de Despesa são obrigatórios.", "error")
            return render_template("itens/form.html", naturezas=nds_ativas, form_data=request.form), 400
        nd = NaturezaDespesa.query.filter_by(id=natureza_despesa_id, ativa=True).first()
        if not nd:
            flash("Natureza de Despesa inválida ou inativa.", "error")
            return render_template("itens/form.html", naturezas=nds_ativas, form_data=request.form), 400
        novo_item = Item(nome=nome, descricao=descricao, unidade_medida=unidade_medida, natureza_despesa_id=natureza_despesa_id, estoque_minimo=estoque_minimo, ponto_ressuprimento=ponto_ressuprimento, saldo_atual=saldo_atual, ativo=ativo)
        try:
            db.session.add(novo_item)
            db.session.commit()
            flash("Item criado com sucesso! Saldo inicial é zero. Registre uma entrada ou inventário inicial.", "success")
            return redirect(url_for("main.listar_itens"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar Item: {e}", "error")
            return render_template("itens/form.html", naturezas=nds_ativas, form_data=request.form), 500
    return render_template("itens/form.html", naturezas=nds_ativas)

@main_bp.route("/itens/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_item(id):
    item = Item.query.get_or_404(id)
    nds_ativas = NaturezaDespesa.query.filter_by(ativa=True).order_by(NaturezaDespesa.codigo).all()
    if request.method == "POST":
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        unidade_medida = request.form.get("unidade_medida")
        natureza_despesa_id = request.form.get("natureza_despesa_id", type=int)
        estoque_minimo = request.form.get("estoque_minimo", default=0, type=int)
        ponto_ressuprimento = request.form.get("ponto_ressuprimento", default=0, type=int)
        ativo = request.form.get("ativo") == "on"
        if not nome or not unidade_medida or not natureza_despesa_id:
            flash("Nome, Unidade de Medida e Natureza de Despesa são obrigatórios.", "error")
            return render_template("itens/form.html", item=item, naturezas=nds_ativas, form_data=request.form), 400
        nd = NaturezaDespesa.query.filter_by(id=natureza_despesa_id, ativa=True).first()
        if not nd:
            flash("Natureza de Despesa inválida ou inativa.", "error")
            return render_template("itens/form.html", item=item, naturezas=nds_ativas, form_data=request.form), 400
        item.nome = nome
        item.descricao = descricao
        item.unidade_medida = unidade_medida
        item.natureza_despesa_id = natureza_despesa_id
        item.estoque_minimo = estoque_minimo
        item.ponto_ressuprimento = ponto_ressuprimento
        item.ativo = ativo
        try:
            db.session.commit()
            flash("Item atualizado com sucesso!", "success")
            return redirect(url_for("main.listar_itens"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar Item: {e}", "error")
            return render_template("itens/form.html", item=item, naturezas=nds_ativas, form_data=request.form), 500
    return render_template("itens/form.html", item=item, naturezas=nds_ativas)

@main_bp.route("/itens/<int:id>/excluir", methods=["POST"])
@admin_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    if MovimentoEstoque.query.filter_by(item_id=id).first() or RequisicaoItem.query.filter_by(item_id=id).first():
        flash("Não é possível excluir este Item, pois existem movimentos de estoque ou requisições vinculadas a ele. Considere inativá-lo.", "error")
        return redirect(url_for("main.listar_itens"))
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Item excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir Item: {e}", "error")
    return redirect(url_for("main.listar_itens"))

# --- Rotas para Movimentos de Estoque ---
@main_bp.route("/movimentos/novo", methods=["GET", "POST"])
@admin_required
def registrar_movimento():
    itens_ativos = Item.query.filter_by(ativo=True).order_by(Item.nome).all()
    if request.method == "POST":
        item_id = request.form.get("item_id", type=int)
        tipo = request.form.get("tipo")
        quantidade = request.form.get("quantidade", type=int)
        observacao = request.form.get("observacao")
        if not item_id or not tipo or not quantidade or quantidade <= 0:
            flash("Item, Tipo de Movimento e Quantidade (positiva) são obrigatórios.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        if tipo not in ["ENTRADA", "SAIDA_AJUSTE", "ENTRADA_AJUSTE", "INVENTARIO_INICIAL"]:
            flash("Tipo de movimento inválido.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        item = Item.query.get(item_id)
        if not item:
            flash("Item não encontrado.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 404
        try:
            with db.session.begin_nested():
                saldo_anterior = item.saldo_atual
                saldo_posterior = saldo_anterior
                if tipo.startswith("ENTRADA") or tipo == "INVENTARIO_INICIAL":
                    saldo_posterior = saldo_anterior + quantidade
                elif tipo.startswith("SAIDA"):
                    if saldo_anterior < quantidade:
                        raise ValueError(f"Saldo insuficiente para o item {item.nome} (Atual: {saldo_anterior}, Saída: {quantidade})")
                    saldo_posterior = saldo_anterior - quantidade
                novo_movimento = MovimentoEstoque(
                    item_id=item_id,
                    tipo=tipo,
                    quantidade=quantidade,
                    usuario_id=current_user.id, # Usa usuário logado
                    observacao=observacao,
                    saldo_anterior=saldo_anterior,
                    saldo_posterior=saldo_posterior
                )
                db.session.add(novo_movimento)
                item.saldo_atual = saldo_posterior
                db.session.add(item)
            db.session.commit()
            flash(f"Movimento de {tipo} registrado com sucesso para o item {item.nome}. Novo saldo: {saldo_posterior}", "success")
            return redirect(url_for("main.listar_movimentos"))
        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao registrar movimento: {e}", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 500
    return render_template("movimentos/form.html", itens=itens_ativos)

@main_bp.route("/movimentos", methods=["GET"])
@login_required # Todos logados podem ver
def listar_movimentos():
    movimentos = MovimentoEstoque.query.options(
        db.joinedload(MovimentoEstoque.item),
        db.joinedload(MovimentoEstoque.registrado_por)
    ).order_by(MovimentoEstoque.data_movimento.desc()).all()
    return render_template("movimentos/list.html", movimentos=movimentos)

# --- Rotas para Requisições Internas ---
@main_bp.route("/requisicoes", methods=["GET"])
@login_required
def listar_requisicoes():
    query = Requisicao.query.options(db.joinedload(Requisicao.solicitante))
    if not current_user.is_admin(): # Filtra para solicitante
        query = query.filter(Requisicao.solicitante_id == current_user.id)
    requisicoes = query.order_by(Requisicao.data_requisicao.desc()).all()
    return render_template("requisicoes/list.html", requisicoes=requisicoes)

@main_bp.route("/requisicoes/nova", methods=["GET", "POST"])
@solicitante_required # Apenas solicitantes criam
def criar_requisicao():
    if request.method == "POST":
        observacao_solicitante = request.form.get("observacao_solicitante")
        nova_requisicao = Requisicao(
            solicitante_id=current_user.id, # Usa usuário logado
            observacao_solicitante=observacao_solicitante,
            status="PENDENTE"
        )
        try:
            db.session.add(nova_requisicao)
            db.session.commit()
            flash("Requisição criada com sucesso! Adicione os itens necessários.", "success")
            return redirect(url_for("main.detalhes_requisicao", id=nova_requisicao.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar requisição: {e}", "error")
            return render_template("requisicoes/form.html", form_data=request.form), 500
    return render_template("requisicoes/form.html")

@main_bp.route("/requisicoes/<int:id>", methods=["GET"])
@login_required
def detalhes_requisicao(id):
    requisicao = Requisicao.query.options(
        db.joinedload(Requisicao.solicitante),
        db.joinedload(Requisicao.aprovador),
        db.joinedload(Requisicao.itens_requisicao).joinedload(RequisicaoItem.item)
    ).get_or_404(id)
    # Verifica permissão (Admin ou Solicitante dono)
    if not (current_user.is_admin() or current_user.id == requisicao.solicitante_id):
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.listar_requisicoes"))
    itens_ativos = Item.query.filter_by(ativo=True).order_by(Item.nome).all()
    return render_template("requisicoes/details.html", requisicao=requisicao, itens_ativos=itens_ativos)

@main_bp.route("/requisicoes/<int:id>/adicionar_item", methods=["POST"])
@login_required
def adicionar_item_requisicao(id):
    requisicao = Requisicao.query.get_or_404(id)
    # Verifica permissão (Admin ou Solicitante dono)
    if not (current_user.is_admin() or current_user.id == requisicao.solicitante_id):
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    if requisicao.status != "PENDENTE":
        flash("Não é possível adicionar itens a uma requisição que não está pendente.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    item_id = request.form.get("item_id", type=int)
    quantidade_solicitada = request.form.get("quantidade_solicitada", type=int)
    if not item_id or not quantidade_solicitada or quantidade_solicitada <= 0:
        flash("Item e Quantidade (positiva) são obrigatórios.", "error")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    item = Item.query.filter_by(id=item_id, ativo=True).first()
    if not item:
        flash("Item inválido ou inativo.", "error")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    item_existente = RequisicaoItem.query.filter_by(requisicao_id=id, item_id=item_id).first()
    if item_existente:
        flash(f"O item {item.nome} já está na requisição. Edite a quantidade se necessário.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    novo_item_req = RequisicaoItem(requisicao_id=id, item_id=item_id, quantidade_solicitada=quantidade_solicitada)
    try:
        db.session.add(novo_item_req)
        db.session.commit()
        flash(f"Item {item.nome} adicionado à requisição.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao adicionar item à requisição: {e}", "error")
    return redirect(url_for("main.detalhes_requisicao", id=id))

@main_bp.route("/requisicoes/<int:req_id>/remover_item/<int:item_req_id>", methods=["POST"])
@login_required
def remover_item_requisicao(req_id, item_req_id):
    requisicao = Requisicao.query.get_or_404(req_id)
    item_req = RequisicaoItem.query.get_or_404(item_req_id)
    # Verifica permissão (Admin ou Solicitante dono)
    if not (current_user.is_admin() or current_user.id == requisicao.solicitante_id):
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.detalhes_requisicao", id=req_id))
    if requisicao.status != "PENDENTE":
        flash("Não é possível remover itens de uma requisição que não está pendente.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=req_id))
    if item_req.requisicao_id != req_id:
        flash("Item não pertence a esta requisição.", "error")
        return redirect(url_for("main.detalhes_requisicao", id=req_id))
    try:
        db.session.delete(item_req)
        db.session.commit()
        flash("Item removido da requisição.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover item da requisição: {e}", "error")
    return redirect(url_for("main.detalhes_requisicao", id=req_id))

@main_bp.route("/requisicoes/<int:id>/aprovar", methods=["POST"])
@admin_required
def aprovar_requisicao(id):
    requisicao = Requisicao.query.get_or_404(id)
    if requisicao.status != "PENDENTE":
        flash("A requisição não está pendente para aprovação.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    observacao_aprovador = request.form.get("observacao_aprovador")
    requisicao.status = "APROVADA"
    requisicao.aprovador_id = current_user.id # Usa usuário logado
    requisicao.data_aprovacao = datetime.utcnow()
    requisicao.observacao_aprovador = observacao_aprovador
    try:
        db.session.commit()
        flash("Requisição aprovada com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao aprovar requisição: {e}", "error")
    return redirect(url_for("main.detalhes_requisicao", id=id))

@main_bp.route("/requisicoes/<int:id>/rejeitar", methods=["POST"])
@admin_required
def rejeitar_requisicao(id):
    requisicao = Requisicao.query.get_or_404(id)
    if requisicao.status != "PENDENTE":
        flash("A requisição não está pendente para rejeição.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    observacao_aprovador = request.form.get("observacao_aprovador")
    if not observacao_aprovador:
        flash("A observação é obrigatória ao rejeitar uma requisição.", "error")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    requisicao.status = "REJEITADA"
    requisicao.aprovador_id = current_user.id # Usa usuário logado
    requisicao.data_aprovacao = datetime.utcnow()
    requisicao.observacao_aprovador = observacao_aprovador
    try:
        db.session.commit()
        flash("Requisição rejeitada.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao rejeitar requisição: {e}", "error")
    return redirect(url_for("main.detalhes_requisicao", id=id))

@main_bp.route("/requisicoes/<int:id>/atender", methods=["POST"])
@admin_required
def atender_requisicao(id):
    requisicao = Requisicao.query.options(
        db.joinedload(Requisicao.itens_requisicao).joinedload(RequisicaoItem.item)
    ).get_or_404(id)
    if requisicao.status != "APROVADA" and requisicao.status != "ATENDIDA_PARCIAL":
        flash("Somente requisições aprovadas ou parcialmente atendidas podem ser atendidas.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    itens_atendidos_total = 0
    itens_atendidos_parcial = 0
    erros = []
    try:
        with db.session.begin_nested():
            for item_req in requisicao.itens_requisicao:
                item = item_req.item
                quantidade_a_atender = item_req.quantidade_solicitada - item_req.quantidade_atendida
                if quantidade_a_atender <= 0:
                    itens_atendidos_total += 1 # Conta como já atendido
                    continue
                saldo_atual_item = item.saldo_atual
                quantidade_real_atendida = min(quantidade_a_atender, saldo_atual_item)
                if quantidade_real_atendida > 0:
                    saldo_anterior = saldo_atual_item
                    saldo_posterior = saldo_atual_item - quantidade_real_atendida
                    movimento = MovimentoEstoque(
                        item_id=item.id,
                        tipo="SAIDA_REQUISICAO",
                        quantidade=quantidade_real_atendida,
                        usuario_id=current_user.id, # Usa usuário logado
                        requisicao_item_id=item_req.id,
                        observacao=f"Atendimento Req. {requisicao.id}",
                        saldo_anterior=saldo_anterior,
                        saldo_posterior=saldo_posterior
                    )
                    db.session.add(movimento)
                    item.saldo_atual = saldo_posterior
                    db.session.add(item)
                    item_req.quantidade_atendida += quantidade_real_atendida
                    db.session.add(item_req)
                    if item_req.quantidade_atendida == item_req.quantidade_solicitada:
                        itens_atendidos_total += 1
                    else:
                        itens_atendidos_parcial += 1
                else:
                    erros.append(f"Item {item.nome}: Saldo insuficiente (Solicitado: {quantidade_a_atender}, Disponível: {saldo_atual_item})")
            # Atualiza status da requisição principal
            total_itens = len(requisicao.itens_requisicao)
            if itens_atendidos_total == total_itens:
                requisicao.status = "ATENDIDA_TOTAL"
            elif itens_atendidos_total > 0 or itens_atendidos_parcial > 0:
                 # Se houve algum atendimento (total ou parcial de algum item), mas não todos os itens foram totalmente atendidos
                 if requisicao.status != "ATENDIDA_PARCIAL": # Evita mudar se já estava parcial
                     requisicao.status = "ATENDIDA_PARCIAL"
            db.session.add(requisicao)
        db.session.commit()
        if erros:
            flash("Requisição atendida parcialmente. Erros: " + "; ".join(erros), "warning")
        elif requisicao.status == "ATENDIDA_TOTAL":
            flash("Requisição atendida totalmente com sucesso!", "success")
        elif requisicao.status == "ATENDIDA_PARCIAL":
             flash("Requisição atendida parcialmente com sucesso!", "success")
        else:
             flash("Nenhum item pôde ser atendido por falta de estoque.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao atender requisição: {e}", "error")
    return redirect(url_for("main.detalhes_requisicao", id=id))

# --- Rotas para Inventário e Relatórios ---
@main_bp.route("/inventario", methods=["GET"])
@login_required # Admin ou Solicitante podem ver?
def relatorio_inventario():
    itens_estoque = Item.query.options(
        db.joinedload(Item.natureza_despesa)
    ).filter(Item.ativo == True).order_by(Item.nome).all()
    return render_template("relatorios/inventario.html", itens=itens_estoque)

@main_bp.route("/relatorios/mensal_nd", methods=["GET"])
@login_required # Admin ou Solicitante podem ver?
def relatorio_mensal_nd():
    mes_ano_str = request.args.get("mes_ano")
    if not mes_ano_str:
        hoje = datetime.utcnow()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        mes_ano_str = ultimo_dia_mes_anterior.strftime("%Y-%m")
    try:
        ano, mes = map(int, mes_ano_str.split("-"))
        data_inicio_mes = datetime(ano, mes, 1)
        if mes == 12:
            data_fim_mes = datetime(ano + 1, 1, 1)
        else:
            data_fim_mes = datetime(ano, mes + 1, 1)
    except ValueError:
        flash("Formato de Mês/Ano inválido. Use YYYY-MM.", "error")
        # TODO: Criar template mensal_nd_form.html ou incluir form no template principal
        return render_template("relatorios/mensal_nd.html", relatorio=[], mes_ano=mes_ano_str)
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    relatorio = []
    for nd in nds:
        itens_nd = Item.query.filter_by(natureza_despesa_id=nd.id).all()
        item_ids = [item.id for item in itens_nd]
        if not item_ids:
            relatorio.append({"nd": nd, "saldo_inicial": 0, "total_entradas": 0, "total_saidas": 0, "saldo_final": 0, "itens": []})
            continue
        subquery_saldo_inicial = db.session.query(MovimentoEstoque.item_id, func.max(MovimentoEstoque.id).label("max_id")).filter(MovimentoEstoque.item_id.in_(item_ids), MovimentoEstoque.data_movimento < data_inicio_mes).group_by(MovimentoEstoque.item_id).subquery()
        saldos_iniciais_itens = db.session.query(MovimentoEstoque.item_id, MovimentoEstoque.saldo_posterior).join(subquery_saldo_inicial, MovimentoEstoque.id == subquery_saldo_inicial.c.max_id).all()
        saldo_inicial_nd = sum(saldo for _, saldo in saldos_iniciais_itens)
        map_saldo_inicial_item = dict(saldos_iniciais_itens)
        movimentos_mes = db.session.query(MovimentoEstoque.item_id, MovimentoEstoque.tipo, func.sum(MovimentoEstoque.quantidade).label("total_quantidade")).filter(MovimentoEstoque.item_id.in_(item_ids), MovimentoEstoque.data_movimento >= data_inicio_mes, MovimentoEstoque.data_movimento < data_fim_mes).group_by(MovimentoEstoque.item_id, MovimentoEstoque.tipo).all()
        total_entradas_nd = 0
        total_saidas_nd = 0
        map_entradas_item = {item_id: 0 for item_id in item_ids}
        map_saidas_item = {item_id: 0 for item_id in item_ids}
        for item_id, tipo, total_quantidade in movimentos_mes:
            if tipo.startswith("ENTRADA") or tipo == "INVENTARIO_INICIAL":
                total_entradas_nd += total_quantidade
                map_entradas_item[item_id] = map_entradas_item.get(item_id, 0) + total_quantidade
            elif tipo.startswith("SAIDA"):
                total_saidas_nd += total_quantidade
                map_saidas_item[item_id] = map_saidas_item.get(item_id, 0) + total_quantidade
        saldo_final_nd = saldo_inicial_nd + total_entradas_nd - total_saidas_nd
        itens_detalhe = []
        for item in itens_nd:
            saldo_inicial_item = map_saldo_inicial_item.get(item.id, 0)
            entradas_item = map_entradas_item.get(item.id, 0)
            saidas_item = map_saidas_item.get(item.id, 0)
            saldo_final_item = saldo_inicial_item + entradas_item - saidas_item
            itens_detalhe.append({"item": item, "saldo_inicial": saldo_inicial_item, "entradas": entradas_item, "saidas": saidas_item, "saldo_final": saldo_final_item})
        relatorio.append({"nd": nd, "saldo_inicial": saldo_inicial_nd, "total_entradas": total_entradas_nd, "total_saidas": total_saidas_nd, "saldo_final": saldo_final_nd, "itens": itens_detalhe})
    return render_template("relatorios/mensal_nd.html", relatorio=relatorio, mes_ano=mes_ano_str)

# Função para registrar o Blueprint na aplicação Flask
def init_app(app):
    app.register_blueprint(main_bp)

