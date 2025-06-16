# routes_main.py
# Rotas principais do sistema: login, home, dashboards por perfil, logout

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.security import check_password_hash
from models import Usuario, RequisicaoMaterial
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email
from datetime import timedelta

# --- Definição do formulário de login ---
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])

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
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        senha = form.senha.data

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario, remember=True)
            session.permanent = True
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                perfil = usuario.perfil.nome if usuario.perfil else ''
                if perfil == 'Super Administrador':
                    next_page = url_for('main.home')
                elif perfil == 'Administrador':
                    next_page = url_for('main.home')
                elif perfil == 'Operador':
                    next_page = url_for('main.home_operador')
                elif perfil == 'Autorizador':
                    next_page = url_for('main.home_autorizador')
                else:
                    flash('Perfil desconhecido. Contate o administrador.', 'danger')
                    return redirect(url_for('main.login'))
            
            response = make_response(redirect(next_page))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response

        flash('E-mail ou senha inválidos.', 'danger')
        return redirect(url_for('main.login'))

    return render_template('login.html', form=form)

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

# --- Nova rota para Operador
@main.route('/home_operador')
@login_required
@perfil_required(['Operador'])
def home_operador():
    return render_template('home_operador.html', usuario=current_user)

# --- Página principal para Autorizador ---
@main.route('/home_autorizador')
@login_required
@perfil_required(['Autorizador'])
def home_autorizador():
    return render_template('home_autorizador.html', usuario=current_user)

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

# --- Página Almoxarifado ---
@main.route('/almoxarifado')
@login_required
def almoxarifado():
    requisicoes_pendentes_count = RequisicaoMaterial.query.filter_by(status='PENDENTE').count()
    return render_template('almoxarifado.html', 
                         usuario=current_user,
                         requisicoes_pendentes_count=requisicoes_pendentes_count)

# --- Página ND / Grupos / UL ---
@main.route('/nd_grupos_ul')
@login_required
def nd_grupos_ul():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return '', 204  # Evita recarregamento da estrutura em requisições AJAX
    return render_template('nd_grupos_ul.html')

# --- Página de instrução de troca de senha ---
@main.route('/esqueci_senha')
def esqueci_senha():
    return render_template('esqueci_senha.html')

# --- Página de Relatórios (botões desativados por padrão) ---
@main.route('/relatorios')
@login_required
def relatorios():
    return render_template('relatorios.html', usuario=current_user)

# --- Página Dashboard de Organização ---
@main.route('/dashboard_organizacao')
@login_required
def dashboard_organizacao():
    return render_template('organizacao/dashboard_organizacao.html', usuario=current_user)

