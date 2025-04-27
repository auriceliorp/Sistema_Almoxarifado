from flask import Flask
from flask_login import LoginManager
from .database import db
from .models import Usuario
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
        return Usuario.query.get(int(user_id))
    
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

