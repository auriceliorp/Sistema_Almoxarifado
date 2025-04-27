from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Usuario, NaturezaDespesa, Item
from .database import db
from functools import wraps

# Criar um Blueprint para as rotas principais
main_bp = Blueprint("main", __name__)

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

@main_bp.route("/")

def index():
    if current_user.is_authenticated:
        # Redirecionar diretamente para a página de Naturezas de Despesa
        return redirect(url_for('main.listar_naturezas_despesa'))
    else:
        return render_template("index.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for("main.index"))
        else:
            flash("Email ou senha incorretos. Tente novamente.", "danger")
    
    return render_template("login.html")

@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

# Rotas para Naturezas de Despesa
@main_bp.route("/naturezas_despesa")
@login_required
def listar_naturezas_despesa():
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template("naturezas_despesa/list.html", naturezas=naturezas)

@main_bp.route("/naturezas_despesa/nova", methods=["GET", "POST"])
@admin_required
def cadastrar_natureza_despesa():
    if request.method == "POST":
        codigo = request.form.get("codigo")
        descricao = request.form.get("descricao")
        
        if not codigo or not descricao:
            flash("Código e descrição são obrigatórios.", "danger")
            return render_template("naturezas_despesa/form.html", form_data=request.form)
        
        # Verificar se já existe uma ND com o mesmo código
        nd_existente = NaturezaDespesa.query.filter_by(codigo=codigo).first()
        if nd_existente:
            flash(f"Já existe uma Natureza de Despesa com o código {codigo}.", "danger")
            return render_template("naturezas_despesa/form.html", form_data=request.form)
        
        nova_nd = NaturezaDespesa(codigo=codigo, descricao=descricao)
        
        try:
            db.session.add(nova_nd)
            db.session.commit()
            flash("Natureza de Despesa cadastrada com sucesso.", "success")
            return redirect(url_for("main.listar_naturezas_despesa"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar Natureza de Despesa: {e}", "danger")
    
    return render_template("naturezas_despesa/form.html")

@main_bp.route("/naturezas_despesa/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_natureza_despesa(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    
    if request.method == "POST":
        codigo = request.form.get("codigo")
        descricao = request.form.get("descricao")
        
        if not codigo or not descricao:
            flash("Código e descrição são obrigatórios.", "danger")
            return render_template("naturezas_despesa/form.html", form_data=request.form, nd=nd)
        
        # Verificar se já existe outra ND com o mesmo código
        nd_existente = NaturezaDespesa.query.filter_by(codigo=codigo).first()
        if nd_existente and nd_existente.id != id:
            flash(f"Já existe outra Natureza de Despesa com o código {codigo}.", "danger")
            return render_template("naturezas_despesa/form.html", form_data=request.form, nd=nd)
        
        try:
            nd.codigo = codigo
            nd.descricao = descricao
            db.session.commit()
            flash("Natureza de Despesa atualizada com sucesso.", "success")
            return redirect(url_for("main.listar_naturezas_despesa"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar Natureza de Despesa: {e}", "danger")
    
    return render_template("naturezas_despesa/form.html", nd=nd)

@main_bp.route("/naturezas_despesa/<int:id>/excluir", methods=["POST"])
@admin_required
def excluir_natureza_despesa(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    
    # Verificar se existem itens vinculados a esta ND
    itens_vinculados = Item.query.filter_by(natureza_despesa_id=id).count()
    if itens_vinculados > 0:
        flash(f"Não é possível excluir esta Natureza de Despesa pois existem {itens_vinculados} itens vinculados a ela.", "danger")
        return redirect(url_for("main.listar_naturezas_despesa"))
    
    try:
        db.session.delete(nd)
        db.session.commit()
        flash("Natureza de Despesa excluída com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir Natureza de Despesa: {e}", "danger")
    
    return redirect(url_for("main.listar_naturezas_despesa"))

# Rotas para Itens
@main_bp.route("/itens")
@login_required
def listar_itens():
    itens = Item.query.options(db.joinedload(Item.natureza_despesa)).order_by(Item.nome).all()
    return render_template("itens/list.html", itens=itens)

@main_bp.route("/itens/novo", methods=["GET", "POST"])
@admin_required
def cadastrar_item():
    naturezas_despesa = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    
    if request.method == "POST":
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        unidade_medida = request.form.get("unidade_medida")
        natureza_despesa_id = request.form.get("natureza_despesa_id", type=int)
        estoque_minimo = request.form.get("estoque_minimo", type=int, default=0)
        ponto_ressuprimento = request.form.get("ponto_ressuprimento", type=int, default=0)
        
        if not nome or not unidade_medida or not natureza_despesa_id:
            flash("Nome, unidade de medida e natureza de despesa são obrigatórios.", "danger")
            return render_template("itens/form.html", naturezas_despesa=naturezas_despesa, form_data=request.form)
        
        # Verificar se a ND existe
        nd = NaturezaDespesa.query.get(natureza_despesa_id)
        if not nd:
            flash("Natureza de Despesa não encontrada.", "danger")
            return render_template("itens/form.html", naturezas_despesa=naturezas_despesa, form_data=request.form)
        
        novo_item = Item(
            nome=nome,
            descricao=descricao,
            unidade_medida=unidade_medida,
            natureza_despesa_id=natureza_despesa_id,
            estoque_minimo=estoque_minimo,
            ponto_ressuprimento=ponto_ressuprimento,
            saldo_atual=0
        )
        
        try:
            db.session.add(novo_item)
            db.session.commit()
            flash("Item cadastrado com sucesso.", "success")
            return redirect(url_for("main.listar_itens"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar Item: {e}", "danger")
    
    return render_template("itens/form.html", naturezas_despesa=naturezas_despesa)

@main_bp.route("/itens/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_item(id):
    item = Item.query.get_or_404(id)
    naturezas_despesa = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    
    if request.method == "POST":
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        unidade_medida = request.form.get("unidade_medida")
        natureza_despesa_id = request.form.get("natureza_despesa_id", type=int)
        estoque_minimo = request.form.get("estoque_minimo", type=int, default=0)
        ponto_ressuprimento = request.form.get("ponto_ressuprimento", type=int, default=0)
        ativo = request.form.get("ativo") == "on"
        
        if not nome or not unidade_medida or not natureza_despesa_id:
            flash("Nome, unidade de medida e natureza de despesa são obrigatórios.", "danger")
            return render_template("itens/form.html", naturezas_despesa=naturezas_despesa, form_data=request.form, item=item)
        
        # Verificar se a ND existe
        nd = NaturezaDespesa.query.get(natureza_despesa_id)
        if not nd:
            flash("Natureza de Despesa não encontrada.", "danger")
            return render_template("itens/form.html", naturezas_despesa=naturezas_despesa, form_data=request.form, item=item)
        
        try:
            item.nome = nome
            item.descricao = descricao
            item.unidade_medida = unidade_medida
            item.natureza_despesa_id = natureza_despesa_id
            item.estoque_minimo = estoque_minimo
            item.ponto_ressuprimento = ponto_ressuprimento
            item.ativo = ativo
            
            db.session.commit()
            flash("Item atualizado com sucesso.", "success")
            return redirect(url_for("main.listar_itens"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar Item: {e}", "danger")
    
    return render_template("itens/form.html", naturezas_despesa=naturezas_despesa, item=item)

@main_bp.route("/itens/<int:id>/excluir", methods=["POST"])
@admin_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    
    # Verificar se o item possui movimentações
    # (Esta verificação seria implementada quando o módulo de movimentações estiver pronto)
    
    try:
        # Em vez de excluir, apenas marcar como inativo
        item.ativo = False
        db.session.commit()
        flash("Item desativado com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao desativar Item: {e}", "danger")
    
    return redirect(url_for("main.listar_itens"))

# Implementação simplificada das novas funcionalidades diretamente no routes.py

# Rotas para Movimentações
@main_bp.route("/movimentos")
@login_required
def listar_movimentos():
    # Implementação simplificada
    return render_template("movimentos/list.html", movimentos=[])

@main_bp.route("/movimentos/novo", methods=["GET", "POST"])
@admin_required
def registrar_movimento():
    # Implementação simplificada
    return render_template("movimentos/form.html", itens=[])

# Rotas para Requisições
@main_bp.route("/requisicoes")
@login_required
def listar_requisicoes():
    # Implementação simplificada
    return render_template("requisicoes/list.html", requisicoes=[])

@main_bp.route("/requisicoes/nova", methods=["GET", "POST"])
@login_required
def criar_requisicao():
    # Implementação simplificada
    return render_template("requisicoes/form.html")

@main_bp.route("/requisicoes/<int:id>")
@login_required
def detalhes_requisicao(id):
    # Implementação simplificada
    return render_template("requisicoes/details.html", requisicao=None, itens_disponiveis=[])

# Rotas para Relatórios
@main_bp.route("/relatorios/inventario")
@login_required
def relatorio_inventario():
    # Implementação simplificada
    return render_template("relatorios/inventario.html", itens=[], naturezas_despesa=[])

@main_bp.route("/relatorios/mensal_nd")
@login_required
def relatorio_mensal_nd():
    # Implementação simplificada
    return render_template("relatorios/mensal_nd.html", relatorio=[], mes_ano="")

# Rotas para Movimentações de Estoque
@main_bp.route("/movimentos")
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

@main_bp.route("/movimentos/novo", methods=["GET", "POST"])
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


# Função para registrar o Blueprint na aplicação Flask
def init_app(app):
    app.register_blueprint(main_bp)
