# app_render.py
# Arquivo principal do sistema Flask para o Almoxarifado

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from sqlalchemy import text
import os

# -------------------- Carrega variáveis de ambiente --------------------
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# -------------------- Instancia extensões globais --------------------
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# -------------------- Configuração do login --------------------
login_manager.login_view = 'main.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# -------------------- Cria a aplicação --------------------
def create_app():
    app = Flask(__name__)

    # -------------------- Configurações do app --------------------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------- Inicializa extensões com o app --------------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # -------------------- Importa modelos após init_app --------------------
    from models import Usuario, Perfil, UnidadeLocal, NaturezaDespesa, Grupo, Item, Fornecedor, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem

    # -------------------- Define função de carregamento do usuário --------------------
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # -------------------- Cria tabelas e dados iniciais --------------------
    with app.app_context():
        db.create_all()

        # 🔴 NOVO: exclui tabela 'usuarios' se ainda existir (erro herdado antigo)
        try:
            db.session.execute(text("DROP TABLE IF EXISTS usuarios;"))
            db.session.commit()
            print("Tabela 'usuarios' removida com sucesso.")
        except Exception as e:
            print(f"Erro ao remover tabela 'usuarios': {e}")

        # Criação dos perfis padrão, se não existirem
        perfis_padrao = ['Administrador', 'Solicitante', 'Consultor']
        for nome in perfis_padrao:
            if not Perfil.query.filter_by(nome=nome).first():
                db.session.add(Perfil(nome=nome))
        db.session.commit()

        # Criação do usuário administrador, se não existir
        if not Usuario.query.filter_by(email='admin@admin.com').first():
            perfil_admin = Perfil.query.filter_by(nome='Administrador').first()
            admin = Usuario(
                nome='Administrador',
                email='admin@admin.com',
                senha=generate_password_hash('admin'),  # Senha criptografada
                perfil_id=perfil_admin.id
            )
            db.session.add(admin)
            db.session.commit()

    # -------------------- Importa e registra blueprints --------------------
    from routes_main import main
    from routes_usuario import usuario_bp
    from routes_area_ul import area_ul_bp
    from routes_nd import nd_bp
    from routes_grupo import grupo_bp
    from routes_item import item_bp
    from routes_fornecedor import fornecedor_bp
    from routes_entrada import entrada_bp
    from routes_saida import saida_bp

    app.register_blueprint(main)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(area_ul_bp)
    app.register_blueprint(nd_bp)
    app.register_blueprint(grupo_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(fornecedor_bp)
    app.register_blueprint(entrada_bp)
    app.register_blueprint(saida_bp)

    return app

# -------------------- Instancia final do app --------------------
app = create_app()
