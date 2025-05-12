# routes_main.py
# Rotas principais do sistema: login, home, dashboards por perfil, logout

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.security import check_password_hash
from models import Usuario
from functools import wraps

# --- Definição do blueprint principal com nome 'main' ---
main = Blueprint('main', __name__)

# --- Decorador para restringir acesso com base no perfil do usuário ---
def perfil_required(perfis_autorizados):
    def wrapper(view_func):
        @wraps(view_func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login'))
            if current_user.perfil and current_user.perfil.nome in perfis_autorizados:
                return view_func(*args, **kwargs)
            flash('Acesso não autorizado para seu perfil.', 'danger')
            return redirect(url_for('main.login'))
        return decorated_view
    return wrapper

# --- Tela de login e redirecionamento baseado no perfil ---
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            perfil = usuario.perfil.nome if usuario.perfil else ''

            if perfil == 'Administrador':
                return redirect(url_for('main.home'))
            elif perfil == 'Solicitante':
                return redirect(url_for('main.home_solicitante'))
            elif perfil == 'Consultor':
                return redirect(url_for('main.home_consultor'))
            else:
                flash('Perfil desconhecido. Contate o administrador.', 'danger')
                return redirect(url_for('main.login'))

        flash('E-mail ou senha inválidos.', 'danger')
        return redirect(url_for('main.login'))

    return render_template('login.html')

# --- Página principal para Administrador ---
@main.route('/home')
@login_required
@perfil_required(['Administrador'])
def home():
    return render_template('home.html', usuario=current_user)

# --- Página principal para Solicitante ---
@main.route('/home_solicitante')
@login_required
@perfil_required(['Solicitante'])
def home_solicitante():
    return render_template('home_solicitante.html', usuario=current_user)

# --- Página principal para Consultor ---
@main.route('/home_consultor')
@login_required
@perfil_required(['Consultor'])
def home_consultor():
    return render_template('home_consultor.html', usuario=current_user)

# --- Dashboard genérico (opcional) ---
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

# --- Logout do sistema ---
@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# --- Rota inicial '/' redireciona para login ---
@main.route('/')
def index():
    return redirect(url_for('main.login'))

# --- Página Almoxarifado (temporária ou principal) ---
@main.route('/almoxarifado')
@login_required
def almoxarifado():
    return render_template('almoxarifado.html', usuario=current_user)

# Rota para a página de instrução de troca de senha
@main.route('/esqueci_senha')
def esqueci_senha():
    return render_template('esqueci_senha.html')


# Rota para a página de nd_grupos_ul

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))

# ... outras rotas

@main.route('/nd_grupos_ul')
@login_required
def nd_grupos_ul():
    return render_template('nd_grupos_ul.html')


