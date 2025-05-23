# -*- coding: utf-8 -*-
from flask import Flask
from flask_login import LoginManager
from .database import db
from .models import Usuario  # Importa Usuario aqui
from sqlalchemy.exc import OperationalError
import os

def create_app():
    app = Flask(__name__)

    # Configuração do aplicativo
    app.config.from_object("config.Config")  # Carrega configurações do config.py

    # Inicializar extensões
    db.init_app(app)

    # Configurar Login Manager
    login_manager = LoginManager()
    login_manager.login_view = "main.login"  # Endpoint para a página de login
    login_manager.init_app(app)

    # Função para carregar o usuário
    @login_manager.user_loader
    def load_user(user_id):
        print(f"Tentando carregar usuário com ID: {user_id}")
        try:
            if user_id is None or not str(user_id).isdigit():
                print(f"ID de usuário inválido recebido: {user_id}")
                return None
            user = Usuario.query.get(int(user_id))
            if user:
                print(f"Usuário {user_id} carregado com sucesso.")
            else:
                print(f"Usuário com ID {user_id} não encontrado no banco de dados.")
            return user
        except OperationalError as e:
            print(f"ERRO OPERACIONAL de banco de dados ao carregar usuário {user_id}: {e}")
            return None
        except Exception as e:
            print(f"ERRO INESPERADO ao carregar usuário {user_id}: {e}")
            return None

    # Registrar blueprints
    from .routes import init_app as init_main_routes
    from .routes_movimentos import init_app as init_movimentos_routes
    from .routes_requisicoes import init_app as init_requisicoes_routes
    from .
