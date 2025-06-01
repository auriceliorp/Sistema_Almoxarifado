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

    # Corrige URL de banco de dados caso venha com prefixo postgres:// (incompatível com SQLAlchemy)
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------- Inicializa extensões com o app --------------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  # Inicializa o CSRF

    # -------------------- Handler para erros de CSRF --------------------
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('error.html', 
                             message="Token de segurança expirado. Por favor, tente novamente."), 400

    # -------------------- Importa modelos após init_app para evitar import circular --------------------
    from models import (
        Usuario, Perfil, UnidadeLocal, NaturezaDespesa, Grupo, Item,
        Fornecedor, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem, 
        BemPatrimonial, Publicacao, PublicacaoPartesEmbrapa, PublicacaoPartesFornecedor,
        PublicacaoSignatariosEmbrapa, PublicacaoSignatariosExternos, Tarefa
    )

    # -------------------- Define função de carregamento do usuário --------------------
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # -------------------- Cria tabelas e dados iniciais se ainda não existirem --------------------
    with app.app_context():
        db.create_all()

        # Cria perfis padrão se não existirem
        perfis_padrao = ['Administrador', 'Solicitante', 'Consultor']
        for nome in perfis_padrao:
            if not Perfil.query.filter_by(nome=nome).first():
                db.session.add(Perfil(nome=nome))
        db.session.commit()

        # Cria usuário admin se não existir
        if not Usuario.query.filter_by(email='admin@admin.com').first():
            perfil_admin = Perfil.query.filter_by(nome='Administrador').first()
            admin = Usuario(
                nome='Administrador',
                email='admin@admin.com',
                senha=generate_password_hash('admin'),
                perfil_id=perfil_admin.id
            )
            db.session.add(admin)
            db.session.commit()

    # -------------------- Registra todos os blueprints (rotas do sistema) --------------------
    from routes_main import main
    from routes_usuario import usuario_bp
    from routes_area_ul import area_ul_bp
    from routes_nd import nd_bp
    from routes_grupo import grupo_bp
    from routes_item import item_bp
    from routes_fornecedor import fornecedor_bp
    from routes_entrada import entrada_bp
    from routes_saida import saida_bp
    from routes_relatorio import relatorio_bp
    from routes_dashboard import dashboard_bp
    from routes_popular import popular_bp
    from limpar_dados import limpar_bp
    from routes_auditoria import auditoria_bp
    from routes_painel import painel_bp
    from routes_patrimonio import patrimonio_bp
    from routes_links import links_bp
    from routes_publicacao import bp as publicacoes_bp
    from routes_projetos import projetos_bp as tarefas_bp, api_projetos_bp as tarefas_api_bp

    # Registro dos blueprints
    app.register_blueprint(main)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(area_ul_bp)
    app.register_blueprint(nd_bp)
    app.register_blueprint(grupo_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(fornecedor_bp)
    app.register_blueprint(entrada_bp)
    app.register_blueprint(saida_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(popular_bp)
    app.register_blueprint(limpar_bp)
    app.register_blueprint(auditoria_bp)
    app.register_blueprint(painel_bp)
    app.register_blueprint(patrimonio_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(publicacoes_bp)
    app.register_blueprint(tarefas_bp)
    app.register_blueprint(tarefas_api_bp)  # Registrando o blueprint da API de tarefas

    # Configuração do CSRF para rotas da API
    csrf.exempt(tarefas_api_bp)

    return app

# -------------------- Cria a instância final do app --------------------
app = create_app()

# -------------------- Executa servidor local se rodar diretamente --------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
