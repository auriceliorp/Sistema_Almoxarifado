from flask import Flask
from flask_login import LoginManager
from .database import db
from .models import Usuario
from sqlalchemy.exc import OperationalError # Importar a exceção específica
from .models import Usuario # Certifique-se que Usuario está importado
import os

def create_app():
    app = Flask(__name__)
    
    # Configuração do aplicativo
    app.config.from_object('config.Config')
    
    # Inicializar extensões
    db.init_app(app)
    
    # Configurar Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
def load_user(user_id):
    # Adiciona um log para depuração
    print(f"Tentando carregar utilizador com ID: {user_id}")
    try:
        # Verifica se user_id é uma string numérica válida antes de converter
        if user_id is None or not str(user_id).isdigit():
            print(f"ID de utilizador inválido recebido: {user_id}")
            return None
        
        user = Usuario.query.get(int(user_id))
        
        if user:
            print(f"Utilizador {user_id} carregado com sucesso.")
        else:
            print(f"Utilizador com ID {user_id} não encontrado na base de dados.")
            
        return user
    except OperationalError as e:
        # Erro específico de ligação à base de dados (comum no Render free tier)
        print(f"ERRO OPERACIONAL de base de dados ao carregar utilizador {user_id}: {e}") 
        # Considere usar um sistema de logging mais robusto aqui (ex: logging.error)
        return None # Retorna None para indicar ao Flask-Login que o utilizador não pôde ser carregado
    except Exception as e:
        # Captura outras exceções inesperadas durante o carregamento
        print(f"ERRO INESPERADO ao carregar utilizador {user_id}: {e}")
        # Considere usar um sistema de logging mais robusto aqui
        return None # Trata outros erros como utilizador não carregável
    
    # Registrar blueprints
    from .routes import init_app as init_main_routes
    init_main_routes(app)
    
    # Registrar novos blueprints para as funcionalidades implementadas
    from .routes_movimentos import init_app as init_movimentos_routes
    from .routes_requisicoes import init_app as init_requisicoes_routes
    from .routes_relatorios import init_app as init_relatorios_routes
    
    init_movimentos_routes(app)
    init_requisicoes_routes(app)
    init_relatorios_routes(app)
    
    # Criar banco de dados se não existir
    with app.app_context():
        db.create_all()
    
    return app

