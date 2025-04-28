# app_render.py

from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from sqlalchemy.exc import OperationalError
from sqlalchemy import text  # Importação necessária para comandos SQL diretos
from werkzeug.security import generate_password_hash
from config import Config  # Importa a configuração correta
from database import db
from models import Usuario, Perfil  # Importa Usuario e Perfil

# Inicializa o login manager
login_manager = LoginManager()
login_manager.login_view = "main.login"

@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id is None or not str(user_id).isdigit():
            return None
        user = Usuario.query.get(int(user_id))
        return user
    except OperationalError:
        return None
    except Exception:
        return None

# Cria o blueprint principal
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "Sistema de Almoxarifado Funcionando!"

@main.route('/login', methods=['GET', 'POST'])
def login():
    return "Página de login aqui"

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main)

    try:
        from routes_movimentos import movimentos_bp
        app.register_blueprint(movimentos_bp)
    except ImportError:
        pass

    with app.app_context():
        db.create_all()

        # Cria perfil ADMIN se não existir
        if not Perfil.query.filter_by(nome="Admin").first():
            perfil_admin = Perfil(nome="Admin")
            db.session.add(perfil_admin)
            db.session.commit()

        # Cria usuário ADMIN se não existir
        if not Usuario.query.filter_by(email="admin@admin.com").first():
            admin = Usuario(
                nome="Administrador",
                email="admin@admin.com",
                senha=generate_password_hash("admin123"),
                perfil_id=Perfil.query.filter_by(nome="Admin").first().id
            )
            db.session.add(admin)
            db.session.commit()

    return app

# Cria o app
app = create_app()

# Só executa localmente
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
