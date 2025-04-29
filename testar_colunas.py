from app_render import app
from models import Item
from database import db

with app.app_context():
    print("Colunas da tabela 'item':")
    for coluna in Item.__table__.columns:
        print(f"- {coluna.name} ({coluna.type})")
