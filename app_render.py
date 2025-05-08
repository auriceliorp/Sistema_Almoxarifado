# app_render.py
# Arquivo principal do sistema Flask para o Almoxarifado
# Responsável por configurar o app, extensões e registrar os blueprints

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Carrega variáveis do arquivo .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Instancia extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Configuração do login
login_manager.login_view = 'main_bp.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Cria a aplicação
def create_app():
    app = Flask(__name__)

    # Configurações do app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Importa modelos
    from models import Usuario, Perfil, UnidadeLocal, NaturezaDespesa, Grupo, Item, Fornecedor, EntradaMaterial, EntradaItem

    # Define função de carregamento do usuário para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Cria tabelas e usuário admin se necessário
    with app.app_context():
        db.create_all()

        if not Perfil.query.filter_by(nome='Admin').first():
            perfil_admin = Perfil(nome='Admin')
            db.session.add(perfil_admin)
            db.session.commit()

        if not Usuario.query.filter_by(email='admin@admin.com').first():
            admin = Usuario(
                nome='Administrador',
                email='admin@admin.com',
                senha='admin',
                perfil_id=Perfil.query.filter_by(nome='Admin').first().id
            )
            db.session.add(admin)
            db.session.commit()

    # Importa e registra os blueprints
    from routes_main import main_bp
    from routes_usuario import usuario_bp
    from routes_area_ul import area_ul_bp
    from routes_nd import nd_bp
    from routes_grupo import grupo_bp
    from routes_item import item_bp
    from routes_fornecedor import fornecedor_bp
    from routes_entrada import entrada_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(area_ul_bp)
    app.register_blueprint(nd_bp)
    app.register_blueprint(grupo_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(fornecedor_bp)
    app.register_blueprint(entrada_bp)

    return app

# Instancia o app
app = create_app()