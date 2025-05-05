# app_render.py

from flask import Flask, render_template, redirect, url_for, request, flash, Blueprint
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import inspect, text
from config import Config
from database import db
from models import Usuario, Perfil
import os
import smtplib
from email.mime.text import MIMEText

# Login Manager
login_manager = LoginManager()
login_manager.login_view = "main.login"

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None and str(user_id).isdigit():
        return Usuario.query.get(int(user_id))
    return None

# Blueprint principal
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            if getattr(usuario, 'senha_temporaria', False):
                return redirect(url_for('main.trocar_senha'))
            return redirecionar_por_perfil(usuario)
        else:
            flash('E-mail ou senha inválidos.')
    return render_template('login.html')

@main.route('/trocar_senha', methods=['GET', 'POST'])
@login_required
def trocar_senha():
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')

        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem.')
        else:
            current_user.senha = generate_password_hash(nova_senha)
            current_user.senha_temporaria = False
            db.session.commit()
            enviar_email_troca_senha(current_user.email)
            flash('Senha alterada com sucesso.')
            return redirecionar_por_perfil(current_user)

    return render_template('trocar_senha.html')

@main.route('/home')
@login_required
def home():
    return redirecionar_por_perfil(current_user)

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

@main.route('/almoxarifado')
@login_required
def almoxarifado():
    return render_template('almoxarifado.html', usuario=current_user)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

def redirecionar_por_perfil(usuario):
    nome_perfil = usuario.perfil.nome.lower()
    if nome_perfil == 'administrador':
        return render_template('home.html', usuario=usuario)
    elif nome_perfil == 'solicitante':
        return render_template('home_solicitante.html', usuario=usuario)
    elif nome_perfil == 'consultor':
        return render_template('home_consultor.html', usuario=usuario)
    else:
        flash('Perfil desconhecido.')
        return redirect(url_for('main.login'))

def enviar_email_troca_senha(destinatario):
    try:
        remetente = os.environ.get('EMAIL_REMETENTE')
        senha = os.environ.get('EMAIL_SENHA')
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))

        assunto = "Senha alterada com sucesso"
        corpo = "Sua senha foi alterada com sucesso no sistema Almoxarifado Embrapa. Caso não tenha sido você, informe imediatamente o administrador."

        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = remetente
        msg['To'] = destinatario

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(remetente, senha)
            server.send_message(msg)
    except Exception as e:
        print(f"Erro ao enviar e-mail de troca de senha: {e}")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main)

    from routes_nd import nd_bp
    from routes_item import item_bp
    from routes_usuario import usuario_bp
    from routes_estoque import estoque_bp
    from routes_fornecedor import fornecedor_bp
    from routes_area_ul import area_ul_bp

    app.register_blueprint(nd_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(fornecedor_bp)
    app.register_blueprint(area_ul_bp)

    with app.app_context():
        db.create_all()

        def adicionar_coluna(tabela, coluna_sql):
            try:
                db.session.execute(text(f'ALTER TABLE {tabela} ADD COLUMN {coluna_sql};'))
                db.session.commit()
                print(f"Coluna adicionada: {coluna_sql} em {tabela}")
            except Exception:
                db.session.rollback()

        def coluna_existe(nome_tabela, nome_coluna):
            insp = inspect(db.engine)
            return nome_coluna in [col["name"] for col in insp.get_columns(nome_tabela)]

        if not coluna_existe('usuario', 'matricula'):
            adicionar_coluna('usuario', 'matricula VARCHAR(50)')
        if not coluna_existe('usuario', 'senha_temporaria'):
            adicionar_coluna('usuario', 'senha_temporaria BOOLEAN DEFAULT FALSE')

        perfil_admin = Perfil.query.filter_by(nome='Admin').first()
        if not perfil_admin:
            perfil_admin = Perfil(nome='Admin')
            db.session.add(perfil_admin)
            db.session.commit()

        admin_email = "admin@admin.com"
        if not Usuario.query.filter_by(email=admin_email).first():
            usuario_admin = Usuario(
                nome="Administrador",
                email=admin_email,
                senha=generate_password_hash("admin123"),
                perfil_id=perfil_admin.id,
                matricula="0001",
                senha_temporaria=True
            )
            db.session.add(usuario_admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    app = create_app()
