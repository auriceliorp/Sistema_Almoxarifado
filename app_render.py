from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from sqlalchemy.exc import OperationalError

from database import db
from models import Usuario

login_manager = LoginManager()
login_manager.login_view = "main.login"

@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id is None or not str(user_id).isdigit():
            return None
        from models import Usuario
        user = Usuario.query.get(int(user_id))
        return user
    except OperationalError:
        return None
    except Exception:
        return None

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "Sistema de Almoxarifado Funcionando!"

@main.route('/login', methods=['GET', 'POST'])
def login():
    from models import Usuario
    return "Página de login aqui"

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/estoque.db'  # <-- aqui corrigido
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
