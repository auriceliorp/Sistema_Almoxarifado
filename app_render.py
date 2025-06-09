# app_render.py
# Arquivo principal do sistema Flask para o Almoxarifado e Patrimônio

import os
from flask import Flask, render_template
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import CSRFError
from flask_login import login_required

# Importa extensões globais (db, login_manager, migrate, csrf)
from extensoes import db, login_manager, migrate, csrf

# Importa modelos necessários
from models import (
    Usuario, Perfil, UnidadeLocal, NaturezaDespesa, Grupo, Item,
    Fornecedor, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem, 
    BemPatrimonial, Publicacao, PublicacaoPartesEmbrapa, PublicacaoPartesFornecedor,
    PublicacaoSignatariosEmbrapa, PublicacaoSignatariosExternos, Tarefa,
    CategoriaTarefa, OrigemTarefa, RequisicaoMaterial, RequisicaoItem
)

# -------------------- Carrega variáveis de ambiente do arquivo .env (para uso local) --------------------
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# -------------------- Configuração do login --------------------
login_manager.login_view = 'main.login'  # Rota usada para redirecionar ao login
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# -------------------- Função Factory que cria a aplicação --------------------
def create_app():
    app = Flask(__name__)

    # -------------------- Configurações principais --------------------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao'
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-chave-secreta-padrao'

    # Tenta usar variáveis do Railway primeiro
    if os.environ.get('PGDATABASE'):
        db_user = os.environ.get('PGUSER')
        db_password = os.environ.get('PGPASSWORD')
        db_host = os.environ.get('PGHOST')
        db_port = os.environ.get('PGPORT')
        db_name = os.environ.get('PGDATABASE')
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        # Se não houver variáveis do Railway, tenta DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        
        # Se ainda não houver, usa as variáveis locais
        if not database_url:
            db_user = os.environ.get('DB_USER')
            db_password = os.environ.get('DB_PASSWORD')
            db_host = os.environ.get('DB_HOST', 'localhost')
            db_port = os.environ.get('DB_PORT', '5432')
            db_name = os.environ.get('DB_NAME')
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Corrige URL se necessário (Railway às vezes usa postgres:// ao invés de postgresql://)
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"Using database URL: {database_url}")  # Para debug

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 60,
        'pool_pre_ping': True
    }

    # -------------------- Inicializa extensões com o app --------------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  # Inicializa o CSRF

    # -------------------- Define função de carregamento do usuário --------------------
    @login_manager.user_loader
    def load_user(user_id):
        if user_id is None:
            return None
        try:
            return Usuario.query.get(int(user_id))
        except:
            return None

    # -------------------- Handler para erros de CSRF --------------------
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('error.html', 
                             message="Token de segurança expirado. Por favor, tente novamente."), 400

    # -------------------- Registra os blueprints --------------------
    from routes_main import main as main_blueprint
    from routes_usuario import usuario_bp as usuario_blueprint
    from routes_requisicao import requisicao_bp as requisicao_blueprint
    from routes_auditoria import auditoria_bp as auditoria_blueprint
    from routes_publicacao import publicacao_bp as publicacao_blueprint
    from routes_autorizacao import autorizacao_bp as autorizacao_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(usuario_blueprint)
    app.register_blueprint(requisicao_blueprint)
    app.register_blueprint(auditoria_blueprint)
    app.register_blueprint(publicacao_blueprint)
    app.register_blueprint(autorizacao_blueprint)

    # -------------------- Cria perfis padrão --------------------
    with app.app_context():
        db.create_all()  # Cria todas as tabelas
        Perfil.criar_perfis_padrao()  # Cria os perfis padrão

    return app

# -------------------- Cria a instância final do app --------------------
app = create_app()

# -------------------- Cria tabelas e dados iniciais se ainda não existirem --------------------
def init_db():
    with app.app_context():
        db.create_all()

        # Cria perfis padrão se não existirem
        perfis_padrao = ['Administrador', 'Solicitante', 'Consultor']
        for nome in perfis_padrao:
            if not Perfil.query.filter_by(nome=nome).first():
                db.session.add(Perfil(nome=nome))
        try:
            db.session.commit()
        except:
            db.session.rollback()

        # Cria usuário admin se não existir
        if not Usuario.query.filter_by(email='admin@admin.com').first():
            perfil_admin = Perfil.query.filter_by(nome='Administrador').first()
            if perfil_admin:
                admin = Usuario(
                    nome='Administrador',
                    email='admin@admin.com',
                    senha=generate_password_hash('admin'),
                    perfil_id=perfil_admin.id
                )
                db.session.add(admin)
                try:
                    db.session.commit()
                except:
                    db.session.rollback()

# Inicializa o banco de dados apenas se estiver rodando diretamente
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
