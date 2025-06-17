# extensoes.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Cria instâncias das extensões
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_csrf(app):
    csrf.init_app(app)
