from flask import Blueprint, request, render_template, flash, redirect, url_for
# Alterar para importação absoluta, assumindo que os modelos e db estão acessíveis
# a partir do módulo principal (app_render.py)
# Se os modelos estiverem em models.py, use 'from models import ...'
# Se db estiver em database.py, use 'from database import db'
# Como eles estão definidos em app_render.py, vamos importá-los de lá:
from app_render import db, Item, MovimentoEstoque, Usuario # Importar o necessário de app_render

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
        # Assumindo que o modelo Usuario tem o método is_admin()
        if not current_user.is_admin():
            flash("Acesso negado. Você precisa ser um administrador.", "danger")
            # Corrigir endpoint do redirect se 'main.home' não existir
            # Talvez seja 'main.index'?
            return redirect(url_for("main.index")) 
        return f(*args, **kwargs)
    return decorated_function

@movimentos_bp.route("/", methods=["GET"])
@login_required
def listar_movimentos():
    """Lista todos os movimentos de estoque."""
    item_id = request.args.get("item_id", type=int)
    tipo = request.args.get("tipo")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    
    # Usar db.joinedload requer importar db do SQLAlchemy
    # e não necessariamente do app_render, mas vamos manter por enquanto
    # Idealmente, MovimentoEstoque teria a relação definida
    # query = MovimentoEstoque.query.options(
    #     db.joinedload(MovimentoEstoque.item),
    #     db.joinedload(MovimentoEstoque.registrado_por) # Assumindo relação 'registrado_por'
    # )
    # Simplificando a query por agora:
    query = MovimentoEstoque.query
    
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
    
    # Assumindo que MovimentoEstoque tem o campo data_movimento
    movimentos = query.order_by(MovimentoEstoque.data_movimento.desc()).all()
    
    # Assumindo que Item tem o campo ativo
    # itens = Item.query.filter_by(ativo=True).order_by(Item.nome).all()
    # Simplificando:
    itens = Item.query.order_by(Item.descricao).all()
    
    # Certifique-se que o template existe
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
    # itens_ativos = Item.query.filter_by(ativo=True).order_by(Item.nome).all()
    # Simplificando:
    itens_ativos = Item.query.order_by(Item.descricao).all()
    
    if request.method == "POST":
        item_id = request.form.get("item_id", type=int)
        tipo = request.form.get("tipo")
        quantidade = request.form.get("quantidade", type=int)
        observacao = request.form.get("observacao")
        
        if not item_id or not tipo or not quantidade or quantidade <= 0:
            flash("Item, Tipo de Movimento e Quantidade (positiva) são obrigatórios.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        
        # Assumindo que MovimentoEstoque tem os tipos definidos
        # if tipo not in ["ENTRADA", "SAIDA_AJUSTE", "ENTRADA_AJUSTE", "INVENTARIO_INICIAL"]:
        #    flash("Tipo de movimento inválido.", "error")
        #    return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        
        item = Item.query.get(item_id)
        if not item:
            flash("Item não encontrado.", "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 404
        
        try:
            # Usar db.session requer importar db
            with db.session.begin_nested(): 
                # Assumindo que Item tem saldo_atual
                saldo_anterior = item.estoque_atual 
                saldo_posterior = saldo_anterior
                
                if tipo.startswith("ENTRADA") or tipo == "INVENTARIO_INICIAL":
                    saldo_posterior = saldo_anterior + quantidade
                elif tipo.startswith("SAIDA"):
                    if saldo_anterior < quantidade:
                        raise ValueError(f"Saldo insuficiente para o item {item.descricao} (Atual: {saldo_anterior}, Saída: {quantidade})")
                    saldo_posterior = saldo_anterior - quantidade
                
                # Assumindo que MovimentoEstoque existe e tem estes campos
                novo_movimento = MovimentoEstoque(
                    item_id=item_id,
                    tipo=tipo,
                    quantidade=quantidade,
                    usuario_id=current_user.id,
                    observacao=observacao,
                    saldo_anterior=saldo_anterior,
                    saldo_posterior=saldo_posterior
                    # data_movimento é adicionado automaticamente?
                )
                
                db.session.add(novo_movimento)
                item.estoque_atual = saldo_posterior
                db.session.add(item)
            
            db.session.commit()
            flash(f"Movimento de {tipo} registrado com sucesso para o item {item.descricao}. Novo saldo: {saldo_posterior}", "success")
            return redirect(url_for("movimentos.listar_movimentos"))
        
        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), "error")
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 400
        
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao registrar movimento: {e}", "error")
            # Logar o erro real é importante aqui
            print(f"Erro Exception: {e}") 
            return render_template("movimentos/form.html", itens=itens_ativos, form_data=request.form), 500
    
    # Certifique-se que o template existe
    return render_template("movimentos/form.html", itens=itens_ativos)

# Função para registrar o Blueprint na aplicação Flask
# Esta função não é necessária se o blueprint for importado diretamente em app_render.py
# def init_app(app):
#     app.register_blueprint(movimentos_bp)

