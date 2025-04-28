# script_corrigir_usuario.py
from config import Config
from database import db
from flask import Flask
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

app = create_app()

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE usuario ADD COLUMN matricula VARCHAR(50);'))
        db.session.commit()
        print("✅ Coluna 'matricula' adicionada com sucesso na tabela 'usuario'.")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Erro ao adicionar a coluna (provavelmente já existe): {e}")
