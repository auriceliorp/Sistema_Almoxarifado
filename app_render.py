# app_render.py corrigido

from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import OperationalError
from config import Config
from database import db
from models import Usuario, Perfil
from sqlalchemy import text

# Configura Login Manager
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
            return redirect(url_for('main.dashboard'))
        else:
            flash('E-mail ou senha inválidos.')

    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

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

    try:
        from routes_nd import nd_bp
        app.register_blueprint(nd_bp)
    except ImportError:
        pass

    try:
        from routes_item import item_bp
        app.register_blueprint(item_bp)
    except ImportError:
        pass

    with app.app_context():
        db.create_all()

        # Corrige colunas se necessário
        try:
            db.session.execute(text('ALTER TABLE natureza_despesa ADD COLUMN descricao VARCHAR(255);'))
            db.session.commit()
            print("Coluna 'descricao' adicionada na tabela natureza_despesa!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Coluna 'descricao' pode já existir: {e}")

        try:
            db.session.execute(text('ALTER TABLE natureza_despesa ADD COLUMN numero VARCHAR(50);'))
            db.session.commit()
            print("Coluna 'numero' adicionada na tabela natureza_despesa!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Coluna 'numero' pode já existir: {e}")

        try:
            db.session.execute(text('ALTER TABLE usuario ADD COLUMN matricula VARCHAR(50);'))
            db.session.commit()
            print("Coluna 'matricula' adicionada na tabela usuario!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Coluna 'matricula' pode já existir: {e}")

        try:
            db.session.execute(text('ALTER TABLE item ADD COLUMN natureza_despesa_id INTEGER REFERENCES natureza_despesa(id);'))
            db.session.commit()
            print("Coluna 'natureza_despesa_id' adicionada na tabela item!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Coluna 'natureza_despesa_id' pode já existir: {e}")

        # Cria perfil ADMIN se não existir
        perfil_admin = Perfil.query.filter_by(nome='Admin').first()
        if not perfil_admin:
            perfil_admin = Perfil(nome='Admin')
            db.session.add(perfil_admin)
            db.session.commit()

        # Cria usuário ADMIN se não existir
        admin_email = "admin@admin.com"
        if not Usuario.query.filter_by(email=admin_email).first():
            usuario_admin = Usuario(
                nome="Administrador",
                email=admin_email,
                senha=generate_password_hash("admin123"),
                perfil_id=perfil_admin.id,
                matricula="0001"
            )
            db.session.add(usuario_admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    app = create_app()
