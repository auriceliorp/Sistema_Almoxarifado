from flask import Blueprint, request, render_template, flash, redirect, url_for
from .models import Requisicao, RequisicaoItem, Item, MovimentoEstoque
from .database import db
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps

# Criar um Blueprint para as rotas de requisições
requisicoes_bp = Blueprint("requisicoes", __name__, url_prefix="/requisicoes")

# Decorators para Controle de Acesso
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash("Acesso negado. Você precisa ser um administrador.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated_function

def solicitante_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_solicitante():
            flash("Acesso negado. Você precisa ser um solicitante.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated_function

@requisicoes_bp.route("/", methods=["GET"])
@login_required
def listar_requisicoes():
    """Lista todas as requisições do usuário ou todas as requisições para administradores."""
    query = Requisicao.query.options(db.joinedload(Requisicao.solicitante))
    
    # Filtrar por status se fornecido
    status = request.args.get("status")
    if status:
        query = query.filter(Requisicao.status == status)
    
    # Filtrar por solicitante para usuários não-admin
    if not current_user.is_admin():
        query = query.filter(Requisicao.solicitante_id == current_user.id)
    
    requisicoes = query.order_by(Requisicao.data_requisicao.desc()).all()
    return render_template("requisicoes/list.html", requisicoes=requisicoes)

@requisicoes_bp.route("/nova", methods=["GET", "POST"])
@login_required
def criar_requisicao():
    """Cria uma nova requisição de materiais."""
    if request.method == "POST":
        observacao = request.form.get("observacao_solicitante")
        
        # Criar a requisição
        nova_requisicao = Requisicao(
            solicitante_id=current_user.id,
            status="PENDENTE",
            observacao_solicitante=observacao
        )
        
        try:
            db.session.add(nova_requisicao)
            db.session.commit()
            flash("Requisição criada com sucesso. Adicione itens à requisição.", "success")
            return redirect(url_for("requisicoes.detalhes_requisicao", id=nova_requisicao.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar requisição: {e}", "error")
    
    return render_template("requisicoes/form.html")

@requisicoes_bp.route("/<int:id>", methods=["GET"])
@login_required
def detalhes_requisicao(id):
    """Exibe os detalhes de uma requisição específica."""
    requisicao = Requisicao.query.options(
        db.joinedload(Requisicao.solicitante),
        db.joinedload(Requisicao.aprovador),
        db.joinedload(Requisicao.itens_requisicao).joinedload(RequisicaoItem.item)
    ).get_or_404(id)
    
    # Verificar permissão (admin vê todas, solicitante vê apenas as próprias)
    if not current_user.is_admin() and requisicao.solicitante_id != current_user.id:
        flash("Você não tem permissão para visualizar esta requisição.", "danger")
        return redirect(url_for("requisicoes.listar_requisicoes"))
    
    # Obter itens disponíveis para adicionar à requisição
    itens_disponiveis = Item.query.filter_by(ativo=True).order_by(Item.nome).all()
    
    return render_template(
        "requisicoes/details.html", 
        requisicao=requisicao, 
        itens_disponiveis=itens_disponiveis
    )

@requisicoes_bp.route("/<int:id>/adicionar_item", methods=["POST"])
@login_required
def adicionar_item_requisicao(id):
    """Adiciona um item a uma requisição existente."""
    requisicao = Requisicao.query.get_or_404(id)
    
    # Verificar permissão e status
    if not current_user.is_admin() and requisicao.solicitante_id != current_user.id:
        flash("Você não tem permissão para modificar esta requisição.", "danger")
        return redirect(url_for("requisicoes.listar_requisicoes"))
    
    if requisicao.status != "PENDENTE":
        flash("Não é possível adicionar itens a uma requisição que não está pendente.", "warning")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=id))
    
    # Obter dados do formulário
    item_id = request.form.get("item_id", type=int)
    quantidade = request.form.get("quantidade", type=int)
    
    # Validações
    if not item_id or not quantidade or quantidade <= 0:
        flash("Item e quantidade (positiva) são obrigatórios.", "error")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=id))
    
    # Verificar se o item existe
    item = Item.query.get(item_id)
    if not item:
        flash("Item não encontrado.", "error")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=id))
    
    # Verificar se o item já está na requisição
    item_existente = RequisicaoItem.query.filter_by(
        requisicao_id=id, 
        item_id=item_id
    ).first()
    
    try:
        if item_existente:
            # Atualizar quantidade
            item_existente.quantidade_solicitada += quantidade
            db.session.add(item_existente)
            flash(f"Quantidade do item {item.nome} atualizada na requisição.", "success")
        else:
            # Adicionar novo item
            novo_item_req = RequisicaoItem(
                requisicao_id=id,
                item_id=item_id,
                quantidade_solicitada=quantidade,
                quantidade_atendida=0
            )
            db.session.add(novo_item_req)
            flash(f"Item {item.nome} adicionado à requisição.", "success")
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao adicionar item: {e}", "error")
    
    return redirect(url_for("requisicoes.detalhes_requisicao", id=id))

@requisicoes_bp.route("/<int:req_id>/remover_item/<int:item_req_id>", methods=["POST"])
@login_required
def remover_item_requisicao(req_id, item_req_id):
    """Remove um item de uma requisição."""
    requisicao = Requisicao.query.get_or_404(req_id)
    
    # Verificar permissão e status
    if not current_user.is_admin() and requisicao.solicitante_id != current_user.id:
        flash("Você não tem permissão para modificar esta requisição.", "danger")
        return redirect(url_for("requisicoes.listar_requisicoes"))
    
    if requisicao.status != "PENDENTE":
        flash("Não é possível remover itens de uma requisição que não está pendente.", "warning")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=req_id))
    
    # Buscar o item da requisição
    item_req = RequisicaoItem.query.get_or_404(item_req_id)
    
    # Verificar se o item pertence à requisição
    if item_req.requisicao_id != req_id:
        flash("Item não pertence a esta requisição.", "error")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=req_id))
    
    try:
        item_nome = item_req.item.nome if item_req.item else "Item"
        db.session.delete(item_req)
        db.session.commit()
        flash(f"Item {item_nome} removido da requisição.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover item: {e}", "error")
    
    return redirect(url_for("requisicoes.detalhes_requisicao", id=req_id))

@requisicoes_bp.route("/<int:id>/aprovar", methods=["POST"])
@admin_required
def aprovar_requisicao(id):
    """Aprova uma requisição pendente."""
    requisicao = Requisicao.query.get_or_404(id)
    
    if requisicao.status != "PENDENTE":
        flash("A requisição não está pendente para aprovação.", "warning")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=id))
    
    observacao_aprovador = request.form.get("observacao_aprovador")
    
    try:
        requisicao.status = "APROVADA"
        requisicao.aprovador_id = current_user.id
        requisicao.data_aprovacao = datetime.utcnow()
        requisicao.observacao_aprovador = observacao_aprovador
        
        db.session.add(requisicao)
        db.session.commit()
        flash("Requisição aprovada com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao aprovar requisição: {e}", "error")
    
    return redirect(url_for("requisicoes.detalhes_requisicao", id=id))

@requisicoes_bp.route("/<int:id>/rejeitar", methods=["POST"])
@admin_required
def rejeitar_requisicao(id):
    """Rejeita uma requisição pendente."""
    requisicao = Requisicao.query.get_or_404(id)
    
    if requisicao.status != "PENDENTE":
        flash("A requisição não está pendente para rejeição.", "warning")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=id))
    
    observacao_aprovador = request.form.get("observacao_aprovador")
    
    if not observacao_aprovador:
        flash("A observação é obrigatória ao rejeitar uma requisição.", "error")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=id))
    
    try:
        requisicao.status = "REJEITADA"
        requisicao.aprovador_id = current_user.id
        requisicao.data_aprovacao = datetime.utcnow()
        requisicao.observacao_aprovador = observacao_aprovador
        
        db.session.add(requisicao)
        db.session.commit()
        flash("Requisição rejeitada com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao rejeitar requisição: {e}", "error")
    
    return redirect(url_for("requisicoes.detalhes_requisicao", id=id))

@requisicoes_bp.route("/<int:id>/atender", methods=["POST"])
@admin_required
def atender_requisicao(id):
    """Atende uma requisição aprovada, gerando movimentos de saída de estoque."""
    requisicao = Requisicao.query.options(
        db.joinedload(Requisicao.itens_requisicao).joinedload(RequisicaoItem.item)
    ).get_or_404(id)
    
    if requisicao.status != "APROVADA" and requisicao.status != "ATENDIDA_PARCIAL":
        flash("Somente requisições aprovadas ou parcialmente atendidas podem ser atendidas.", "warning")
        return redirect(url_for("requisicoes.detalhes_requisicao", id=id))
    
    itens_atendidos_total = 0
    itens_atendidos_parcial = 0
    erros = []
    
    try:
        with db.session.begin_nested():
            for item_req in requisicao.itens_requisicao:
                item = item_req.item
                quantidade_a_atender = item_req.quantidade_solicitada - item_req.quantidade_atendida
                
                if quantidade_a_atender <= 0:
                    itens_atendidos_total += 1  # Conta como já atendido
                    continue
                
                saldo_atual_item = item.saldo_atual
                quantidade_real_atendida = min(quantidade_a_atender, saldo_atual_item)
                
                if quantidade_real_atendida > 0:
                    saldo_anterior = saldo_atual_item
                    saldo_posterior = saldo_atual_item - quantidade_real_atendida
                    
                    # Criar movimento de saída
                    movimento = MovimentoEstoque(
                        item_id=item.id,
                        tipo="SAIDA_REQUISICAO",
                        quantidade=quantidade_real_atendida,
                        usuario_id=current_user.id,
                        requisicao_item_id=item_req.id,
                        observacao=f"Atendimento Req. {requisicao.id}",
                        saldo_anterior=saldo_anterior,
                        saldo_posterior=saldo_posterior
                    )
                    
                    db.session.add(movimento)
                    
                    # Atualizar saldo do item
                    item.saldo_atual = saldo_posterior
                    db.session.add(item)
                    
                    # Atualizar quantidade atendida
                    item_req.quantidade_atendida += quantidade_real_atendida
                    db.session.add(item_req)
                    
                    if item_req.quantidade_atendida == item_req.quantidade_solicitada:
                        itens_atendidos_total += 1
                    else:
                        itens_atendidos_parcial += 1
                else:
                    erros.append(f"Item {item.nome}: Saldo insuficiente (Solicitado: {quantidade_a_atender}, Disponível: {saldo_atual_item})")
            
            # Atualizar status da requisição
            total_itens = len(requisicao.itens_requisicao)
            
            if itens_atendidos_total == total_itens:
                requisicao.status = "ATENDIDA_TOTAL"
            elif itens_atendidos_total > 0 or itens_atendidos_parcial > 0:
                requisicao.status = "ATENDIDA_PARCIAL"
            
            db.session.add(requisicao)
        
        # Commit da transação
        db.session.commit()
        
        if erros:
            flash(f"Requisição atendida parcialmente. {len(erros)} itens não puderam ser atendidos completamente.", "warning")
            for erro in erros:
                flash(erro, "info")
        else:
            flash("Requisição atendida com sucesso.", "success")
    
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao atender requisição: {e}", "error")
    
    return redirect(url_for("requisicoes.detalhes_requisicao", id=id))

# Função para registrar o Blueprint na aplicação Flask
def init_app(app):
    app.register_blueprint(requisicoes_bp)
