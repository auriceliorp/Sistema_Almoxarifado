# -*- coding: utf-8 -*-
from flask import Flask
from flask_login import LoginManager # Importar LoginManager
from .config import Config
from .database import init_app as init_db
from .routes import init_app as init_routes
# Import models here to ensure they are registered with SQLAlchemy
from . import models

# Inicializar LoginManager
login_manager = LoginManager()
login_manager.login_view = "main.login" # Rota para redirecionar se não estiver logado
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    # Carrega o usuário pelo ID
    return models.Usuario.query.get(int(user_id))

def create_app():
    """Factory function para criar e configurar a aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensões
    init_db(app)
    login_manager.init_app(app) # Inicializar LoginManager com a app
    init_routes(app)

    # Exemplo de rota simples para teste inicial (manter ou remover depois)
    @app.route("/hello")
    def hello():
        return "Olá, Mundo! Configuração básica do Flask funcionando."

    return app

