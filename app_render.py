# app_render.py
# Arquivo principal do sistema Flask para o Almoxarifado e Patrimônio

import os
import logging
from flask import Flask, render_template, jsonify
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

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        if os.environ.get('PGDATABASE'):
            db_user = os.environ.get('PGUSER')
            db_password = os.environ.get('PGPASSWORD')
            db_host = os.environ.get('PGHOST')
            db_port = os.environ.get('PGPORT')
            db_name = os.environ.get('PGDATABASE')
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            logger.info("Usando configuração do Railway")
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
                logger.info("Usando configuração local")
        
        # Corrige URL se necessário (Railway às vezes usa postgres:// ao invés de postgresql://)
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        logger.info(f"Database URL configurada: {database_url.split('@')[0].split('://')[0]}://*****@{database_url.split('@')[1]}")
    except Exception as e:
        logger.error(f"Erro ao configurar database URL: {str(e)}")
        database_url = "sqlite:///fallback.db"
        logger.info("Usando banco SQLite de fallback")

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 60,
        'pool_pre_ping': True
    }

    # -------------------- Inicializa extensões com o app --------------------
    try:
        db.init_app(app)
        login_manager.init_app(app)
        csrf.init_app(app)  # Inicializa o CSRF
        logger.info("Extensões inicializadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar extensões: {str(e)}")
        raise

    # -------------------- Define função de carregamento do usuário --------------------
    @login_manager.user_loader
    def load_user(user_id):
        if user_id is None:
            return None
        try:
            return Usuario.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Erro ao carregar usuário {user_id}: {str(e)}")
            return None

    # -------------------- Handler para erros de CSRF --------------------
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('error.html', 
                             message="Token de segurança expirado. Por favor, tente novamente."), 400

    # -------------------- Handler para erros 404 --------------------
    @app.errorhandler(404)
    def not_found_error(error):
        if request.is_xhr:
            return jsonify(error="Página não encontrada"), 404
        return render_template('error.html', message="Página não encontrada."), 404

    # -------------------- Handler para erros 500 --------------------
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Erro interno do servidor: {str(error)}")
        if request.is_xhr:
            return jsonify(error="Erro interno do servidor"), 500
        return render_template('error.html', message="Erro interno do servidor."), 500

    # -------------------- Rota de healthcheck --------------------
    @app.route('/health')
    def health():
        return '', 204

    # -------------------- Rota de diagnóstico --------------------
    @app.route('/diagnostic')
    def diagnostic():
        try:
            # Testa a conexão com o banco
            db.session.execute('SELECT 1')
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Erro na conexão com o banco: {str(e)}")
            db_status = "unhealthy"

        return jsonify({
            'status': 'ok',
            'database': db_status,
            'env': {
                'FLASK_ENV': os.environ.get('FLASK_ENV'),
                'FLASK_APP': os.environ.get('FLASK_APP'),
                'DATABASE_URL': os.environ.get('DATABASE_URL', '').split('@')[0].split('://')[0] + '://*****@' + os.environ.get('DATABASE_URL', '').split('@')[1] if os.environ.get('DATABASE_URL') else None,
                'PGHOST': os.environ.get('PGHOST'),
                'PGPORT': os.environ.get('PGPORT'),
                'PGDATABASE': os.environ.get('PGDATABASE')
            }
        }), 200

    # -------------------- Registra os blueprints --------------------
    from routes_main import main as main_blueprint
    from routes_usuario import usuario_bp as usuario_blueprint
    from routes_requisicao import requisicao_bp as requisicao_blueprint
    from routes_auditoria import auditoria_bp as auditoria_blueprint
    from routes_publicacao import publicacao_bp as publicacao_blueprint
    from routes_autorizacao import autorizacao_bp as autorizacao_blueprint
    from routes_entrada import entrada_bp as entrada_blueprint
    from routes_saida import saida_bp as saida_blueprint
    from routes_item import item_bp as item_blueprint
    from routes_grupo import grupo_bp as grupo_blueprint
    from routes_fornecedor import fornecedor_bp as fornecedor_blueprint
    from routes_nd import nd_bp as nd_blueprint
    from routes_patrimonio import patrimonio_bp as patrimonio_blueprint
    from routes_tarefas import tarefas_bp as tarefas_blueprint
    from routes_relatorio import relatorio_bp as relatorio_blueprint
    from routes_dashboard import dashboard_bp as dashboard_blueprint
    from routes_painel import painel_bp as painel_blueprint
    from routes_area_setor import area_setor_bp as area_setor_blueprint
    from routes_area_ul import area_ul_bp as area_ul_blueprint
    from routes_config_tarefas import config_tarefas_bp as config_tarefas_blueprint
    from routes_movimentos import movimentos_bp as movimentos_blueprint
    from routes_projetos import projetos_bp as projetos_blueprint
    from routes_api import api_bp as api_blueprint

    # Registra os blueprints principais
    app.register_blueprint(main_blueprint)
    app.register_blueprint(usuario_blueprint)
    app.register_blueprint(requisicao_blueprint)
    app.register_blueprint(auditoria_blueprint)
    app.register_blueprint(publicacao_blueprint)
    app.register_blueprint(autorizacao_blueprint)

    # Registra os blueprints de gestão de materiais
    app.register_blueprint(entrada_blueprint)
    app.register_blueprint(saida_blueprint)
    app.register_blueprint(item_blueprint)
    app.register_blueprint(grupo_blueprint)
    app.register_blueprint(fornecedor_blueprint)
    app.register_blueprint(nd_blueprint)

    # Registra os blueprints de patrimônio e tarefas
    app.register_blueprint(patrimonio_blueprint)
    app.register_blueprint(tarefas_blueprint)

    # Registra os blueprints de relatórios e dashboards
    app.register_blueprint(relatorio_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(painel_blueprint)

    # Registra os blueprints de estrutura organizacional
    app.register_blueprint(area_setor_blueprint)
    app.register_blueprint(area_ul_blueprint)

    # Registra os blueprints de configuração e utilitários
    app.register_blueprint(config_tarefas_blueprint)
    app.register_blueprint(movimentos_blueprint)
    app.register_blueprint(projetos_blueprint)
    app.register_blueprint(api_blueprint)

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
