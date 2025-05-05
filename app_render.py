import os
import smtplib
from dotenv import load_dotenv
from flask import Flask, Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from werkzeug.security import check_password_hash, generate_password_hash
from database import db
from models import Usuario, Perfil, Item, NaturezaDespesa
from sqlalchemy import inspect, text
from email.mime.text import MIMEText
from config import Config

# Carrega variáveis de ambiente
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Função de envio de e-mail
def enviar_email(destinatario, assunto, mensagem):
    try:
        msg = MIMEText(mensagem, "plain")
        msg["Subject"] = assunto
        msg["From"] = Config.EMAIL_REMETENTE
        msg["To"] = destinatario

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(Config.EMAIL_REMETENTE, Config.EMAIL_SENHA)
            servidor.sendmail(Config.EMAIL_REMETENTE, destinatario, msg.as_string())
    except Exception as e:
        print("Erro ao enviar e-mail:", e)

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

            perfil_nome = usuario.perfil.nome if usuario.perfil else ''
            if perfil_nome == 'Administrador':
                return redirect(url_for('main.home'))
            elif perfil_nome == 'Solicitante':
                return redirect(url_for('main.home_solicitante'))
            elif perfil_nome == 'Consultor':
                return redirect(url_for('main.home_consultor'))
            else:
                return redirect(url_for('main.home'))
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
            flash('Senha alterada com sucesso.')

            # Envia e-mail após alteração da senha
            if current_user.email:
                enviar_email(
                    current_user.email,
                    'Senha alterada com sucesso',
                    f'Olá {current_user.nome}, sua senha foi atualizada com sucesso no sistema Almoxarifado Embrapa.'
                )

            perfil_nome = current_user.perfil.nome if current_user.perfil else ''
            if perfil_nome == 'Administrador':
                return redirect(url_for('main.home'))
            elif perfil_nome == 'Solicitante':
                return redirect(url_for('main.home_solicitante'))
            elif perfil_nome == 'Consultor':
                return redirect(url_for('main.home_consultor'))
            else:
                return redirect(url_for('main.home'))

    return render_template('trocar_senha.html')

@main.route('/home')
@login_required
def home():
    return render_template('home.html', usuario=current_user)

@main.route('/home_solicitante')
@login_required
def home_solicitante():
    return render_template('home_solicitante.html', usuario=current_user)

@main.route('/home_consultor')
@login_required
def home_consultor():
    return render_template('home_consultor.html', usuario=current_user)

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
