from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from sqlalchemy.exc import OperationalError

# Importar de novos ficheiros
from database import db
from models import Usuario # Importar apenas Usuario aqui, outros modelos são usados nas rotas

login_manager = LoginManager()
login_manager.login_view = "main.login"
# ... config login_manager ...

@login_manager.user_loader
def load_user(user_id):
    # ... (código load_user como antes, mas importa Usuario de models) ...
    print(f"Tentando carregar utilizador com ID: {user_id}")
    try:
        if user_id is None or not str(user_id).isdigit():
            print(f"ID de utilizador inválido recebido: {user_id}")
            return None
        # Importar Usuario aqui ou no topo do ficheiro
        from models import Usuario 
        user = Usuario.query.get(int(user_id))
        # ... (resto do código load_user) ...
    except OperationalError as e:
        # ... (tratamento de erro) ...
    except Exception as e:
        # ... (tratamento de erro) ...

# Criar blueprint 'main'
main = Blueprint('main', __name__)

# Rotas do blueprint 'main'
@main.route('/')
def index():
    # ... (código da rota index) ...

@main.route('/login', methods=['GET', 'POST'])
def login():
    # ... (código da rota login, importa Usuario de models) ...
    from models import Usuario
    # ...

@main.route('/logout')
@login_required
def logout():
    # ... (código da rota logout) ...

# !! DEFINIR AS ROTAS QUE FALTAM !!
# Exemplo: Rota para Naturezas de Despesa (precisa importar NaturezaDespesa de models)
@main.route('/naturezas-despesa')
@login_required
def listar_naturezas_despesa():
    from models import NaturezaDespesa
    naturezas = NaturezaDespesa.query.all()
    # !! Verifique se o template existe !!
    return render_template('naturezas_despesa/list.html', naturezas=naturezas)

# !! Defina a rota main.saldo_naturezas_despesa aqui se ela deve existir !!
# @main.route('/naturezas-despesa/saldo')
# @login_required
# def saldo_naturezas_despesa():
#     # ... lógica para calcular e mostrar saldo ...
#     # return render_template('saldo_template.html', ...) 
#     pass # Remover pass quando implementar

# ... (Definir outras rotas do main: itens, etc., importando modelos de models.py) ...

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app) # Inicializar db de database.py
    login_manager.init_app(app)

    app.register_blueprint(main)

    # Importar e registrar outros blueprints
    try:
        from routes_movimentos import movimentos_bp
        app.register_blueprint(movimentos_bp)
        print("Blueprint 'movimentos_bp' registrado com sucesso.")
    except ImportError as e:
        print(f"ERRO ao importar/registrar 'movimentos_bp': {e}")
    
    # ... (registrar outros blueprints: requisicoes, relatorios) ...

    with app.app_context():
        db.create_all()
        # ... (código para criar dados iniciais, importa Perfil, Usuario de models) ...
        from models import Perfil, Usuario
        # ...

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
