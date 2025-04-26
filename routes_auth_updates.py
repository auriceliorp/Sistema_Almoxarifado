

# --- Rotas de Autenticação ---
from flask_login import login_user, logout_user, login_required, current_user

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index")) # Ou para um dashboard

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

        # Redireciona para a página que o usuário tentou acessar ou para a index
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("main.index") # Ou dashboard específico do perfil
        return redirect(next_page)

    return render_template("login.html")

@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado.", "info")
    return redirect(url_for("main.login"))

# --- Fim das Rotas de Autenticação ---

# --- Decorators para Controle de Acesso ---
from functools import wraps

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash("Acesso negado. Você precisa ser um administrador.", "danger")
            return redirect(url_for("main.index")) # Ou página de acesso negado
        return f(*args, **kwargs)
    return decorated_function

def solicitante_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_solicitante():
            flash("Acesso negado. Você precisa ser um solicitante.", "danger")
            return redirect(url_for("main.index")) # Ou página de acesso negado
        return f(*args, **kwargs)
    return decorated_function

# --- Atualizar rotas existentes com decorators ---

# Exemplo: Proteger a criação de ND para admins
@main_bp.route("/naturezas_despesa/nova", methods=["GET", "POST"])
@admin_required
def criar_natureza_despesa():
    # ... (código existente) ...
    pass # O código original já está no arquivo, esta linha é só um placeholder

# Exemplo: Proteger edição de ND para admins
@main_bp.route("/naturezas_despesa/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_natureza_despesa(id):
    # ... (código existente) ...
    pass

# Exemplo: Proteger exclusão de ND para admins
@main_bp.route("/naturezas_despesa/<int:id>/excluir", methods=["POST"])
@admin_required
def excluir_natureza_despesa(id):
    # ... (código existente) ...
    pass

# Exemplo: Proteger CRUD de Itens para admins
@main_bp.route("/itens/novo", methods=["GET", "POST"])
@admin_required
def criar_item():
    # ... (código existente) ...
    pass

@main_bp.route("/itens/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_item(id):
    # ... (código existente) ...
    pass

@main_bp.route("/itens/<int:id>/excluir", methods=["POST"])
@admin_required
def excluir_item(id):
    # ... (código existente) ...
    pass

# Exemplo: Proteger registro de movimento manual para admins
@main_bp.route("/movimentos/novo", methods=["GET", "POST"])
@admin_required
def registrar_movimento():
    # Precisa substituir o usuario_id_mock pelo current_user.id
    # ... (código existente) ...
    pass

# Exemplo: Proteger criação de requisição para solicitantes
@main_bp.route("/requisicoes/nova", methods=["GET", "POST"])
@solicitante_required
def criar_requisicao():
    # Precisa substituir o solicitante_id_mock pelo current_user.id
    # ... (código existente) ...
    pass

# Exemplo: Proteger adição/remoção de itens (Solicitante dono ou Admin)
@main_bp.route("/requisicoes/<int:id>/adicionar_item", methods=["POST"])
@login_required # Verificar permissão dentro da rota
def adicionar_item_requisicao(id):
    requisicao = Requisicao.query.get_or_404(id)
    if not (current_user.is_admin() or current_user.id == requisicao.solicitante_id):
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    if requisicao.status != "PENDENTE":
        flash("Não é possível adicionar itens a uma requisição que não está pendente.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=id))
    # ... (restante do código existente) ...
    pass

@main_bp.route("/requisicoes/<int:req_id>/remover_item/<int:item_req_id>", methods=["POST"])
@login_required # Verificar permissão dentro da rota
def remover_item_requisicao(req_id, item_req_id):
    requisicao = Requisicao.query.get_or_404(req_id)
    if not (current_user.is_admin() or current_user.id == requisicao.solicitante_id):
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.detalhes_requisicao", id=req_id))
    if requisicao.status != "PENDENTE":
        flash("Não é possível remover itens de uma requisição que não está pendente.", "warning")
        return redirect(url_for("main.detalhes_requisicao", id=req_id))
    # ... (restante do código existente) ...
    pass

# Exemplo: Proteger aprovação/rejeição/atendimento para admins
@main_bp.route("/requisicoes/<int:id>/aprovar", methods=["POST"])
@admin_required
def aprovar_requisicao(id):
    # Precisa substituir o aprovador_id_mock pelo current_user.id
    # ... (código existente) ...
    pass

@main_bp.route("/requisicoes/<int:id>/rejeitar", methods=["POST"])
@admin_required
def rejeitar_requisicao(id):
    # Precisa substituir o aprovador_id_mock pelo current_user.id
    # ... (código existente) ...
    pass

@main_bp.route("/requisicoes/<int:id>/atender", methods=["POST"])
@admin_required
def atender_requisicao(id):
    # Precisa substituir o atendente_id_mock pelo current_user.id
    # ... (código existente) ...
    pass

# Proteger listagens e detalhes (pode ser @login_required e filtrar internamente ou usar decorators específicos)
@main_bp.route("/naturezas_despesa", methods=["GET"])
@login_required
def listar_naturezas_despesa():
    # ... (código existente) ...
    pass

@main_bp.route("/itens", methods=["GET"])
@login_required
def listar_itens():
    # ... (código existente) ...
    pass

@main_bp.route("/movimentos", methods=["GET"])
@login_required
def listar_movimentos():
    # ... (código existente) ...
    pass

@main_bp.route("/requisicoes", methods=["GET"])
@login_required
def listar_requisicoes():
    # Precisa filtrar: Admin vê tudo, Solicitante vê só as suas
    # ... (código existente) ...
    pass

@main_bp.route("/requisicoes/<int:id>", methods=["GET"])
@login_required
def detalhes_requisicao(id):
    requisicao = Requisicao.query.options(...).get_or_404(id)
    if not (current_user.is_admin() or current_user.id == requisicao.solicitante_id):
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.listar_requisicoes"))
    # ... (restante do código existente) ...
    pass

@main_bp.route("/inventario", methods=["GET"])
@login_required # Ou @admin_required?
def relatorio_inventario():
    # ... (código existente) ...
    pass

@main_bp.route("/relatorios/mensal_nd", methods=["GET"])
@login_required # Ou @admin_required?
def relatorio_mensal_nd():
    # ... (código existente) ...
    pass

# Ajustar a rota index para redirecionar se logado
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        # TODO: Criar dashboards específicos?
        # if current_user.is_admin():
        #     return render_template("dashboard_admin.html")
        # else:
        #     return render_template("dashboard_solicitante.html")
        return render_template("index_logged_in.html") # Placeholder para página logada
    return redirect(url_for("main.login")) # Redireciona para login se não autenticado

# Placeholder para página inicial logada
@main_bp.route("/home")
@login_required
def home():
     return render_template("index_logged_in.html") # Precisa criar este template


