from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Instância do SQLAlchemy
db = SQLAlchemy()

# Instância do Flask-Migrate
migrate = Migrate()

def init_app(app):
    """Inicializa as extensões do banco de dados com a aplicação Flask."""
    db.init_app(app)
    migrate.init_app(app, db)

