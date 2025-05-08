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

# Instancia as extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Configuração do login
login_manager.login_view = 'main.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Função para criar a aplicação Flask
def create_app():
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Importa os modelos antes de criar o banco (ordem importa para FK funcionar)
    from usuario import Usuario
    from perfil import Perfil
    from unidade_local import UnidadeLocal
    from natureza_despesa import NaturezaDespesa
    from grupo_item import GrupoItem
    from item import Item
    from fornecedor import Fornecedor
    from entrada_material import EntradaMaterial, EntradaItem

    # Cria tabelas no banco, se não existirem
    with app.app_context():
        db.create_all()

        # Garante existência do perfil Admin e usuário admin
        if not Perfil.query.filter_by(nome='Admin').first():
            perfil_admin = Perfil(nome='Admin')
            db.session.add(perfil_admin)
            db.session.commit()

        if not Usuario.query.filter_by(email='admin@admin.com').first():
            admin = Usuario(
                nome='Administrador',
                email='admin@admin.com',
                senha='admin',  # Alterar depois
                perfil_id=Perfil.query.filter_by(nome='Admin').first().id
            )
            db.session.add(admin)
            db.session.commit()

    # Registro de Blueprints
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
