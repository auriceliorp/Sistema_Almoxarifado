from flask import Blueprint, request, render_template, flash, redirect, url_for
from .models import Item, MovimentoEstoque
from .database import db
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps

# Criar um Blueprint para as rotas de movimentações
movimentos_bp = Blueprint("movimentos", __name__, url_prefix="/movimentos")

# Decorator para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash("Acesso negado. Você precisa ser um administrador.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated_function

@movimentos_bp.route("/", methods=["GET"])
@login_required
def listar_movimentos():
    """Lista todos os movimentos de estoque."""
    # Adicionar filtros por item, tipo, data
    item_id = request.args.get("item_id", type=int)
    tipo = request.args.get("tipo")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    
    query = MovimentoEstoque.query.options(
        db.joinedload(MovimentoEstoque.item),
        db.joinedload(MovimentoEstoque.registrado_por)
    )
    
    # Aplicar filtros se fornecidos
    if item_id:
        query = query.filter(MovimentoEstoque.item_id == item_id)
    if tipo:
        query = query.filter(MovimentoEstoque.tipo == tipo)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(MovimentoEstoque.data_movimento >= data_inicio_dt)
        except ValueError:
            flash("Formato de data inválido para data inicial.", "warning")
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
            data_fim_dt = data_fim_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(MovimentoEstoque.data_movimento <= data_fim_dt)
        except ValueError:
            flash("Formato de data inválido para data final.", "warning")
    
    # Ordenar por data mais recente
    movimentos = query.order_by(MovimentoEstoque.data_movimento.desc()).all()
    
    # Obter lista de itens para o filtro
    itens = Item.query.filter_by(ativo=True).order_by(Item.nome).all()
    
    return render_template(
        "movimentos/list.html", 
        movimentos=movimentos,
        itens=itens,
        filtros={
            "item_id": item_id,
            "tipo": tipo,
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
    )

@movimentos_bp.route("/novo", methods=["GET", "POST"])
@admin_required
def registrar_movimento():
    """Registra um novo movimento de estoque (entrada ou saída)."""
    itens_ativos = Item.query.filter_by(ativo=True).order_by(Item.nome).all()
    
    if request.method == "POST":
        item_id = request.form.get("item_id", type=int)
        tipo = request.form.get("tipo")
        quantidade = request.form.get("quantidade", type=int)
        observacao = request.form.get("observacao")
        
        # Validações básicas
        if not item_id or not tipo or not quantidade or quantidade <= 0:
            flash("Item, Tipo de Movimento e Quantidade (positiva) são obrigatórios.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        
        # Validar tipo de movimento
        if tipo not in ["ENTRADA", "SAIDA_AJUSTE", "ENTRADA_AJUSTE", "INVENTARIO_INICIAL"]:
            flash("Tipo de movimento inválido.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        
        # Buscar o item
        item = Item.query.get(item_id)
        if not item:
            flash("Item não encontrado.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 404
        
        try:
            with db.session.begin_nested():
                saldo_anterior = item.saldo_atual
                saldo_posterior = saldo_anterior
                
                # Calcular novo saldo
                if tipo.startswith("ENTRADA") or tipo == "INVENTARIO_INICIAL":
                    saldo_posterior = saldo_anterior + quantidade
                elif tipo.startswith("SAIDA"):
                    if saldo_anterior < quantidade:
                        raise ValueError(f"Saldo insuficiente para o item {item.nome} (Atual: {saldo_anterior}, Saída: {quantidade})")
                    saldo_posterior = saldo_anterior - quantidade
                
                # Criar o movimento
                novo_movimento = MovimentoEstoque(
                    item_id=item_id,
                    tipo=tipo,
                    quantidade=quantidade,
                    usuario_id=current_user.id,
                    observacao=observacao,
                    saldo_anterior=saldo_anterior,
                    saldo_posterior=saldo_posterior
                )
                
                # Salvar o movimento e atualizar o saldo do item
                db.session.add(novo_movimento)
                item.saldo_atual = saldo_posterior
                db.session.add(item)
            
            # Commit da transação
            db.session.commit()
            flash(f"Movimento de {tipo} registrado com sucesso para o item {item.nome}. Novo saldo: {saldo_posterior}", "success")
            return redirect(url_for("movimentos.listar_movimentos"))
        
        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao registrar movimento: {e}", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 500
    
    return render_template("movimentos/form.html", itens=itens_ativos)

# Função para registrar o Blueprint na aplicação Flask
def init_app(app):
    app.register_blueprint(movimentos_bp)
