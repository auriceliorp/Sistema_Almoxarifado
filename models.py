# models.py atualizado

from flask_login import UserMixin
from database import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfis.id'), nullable=False)

class Perfil(db.Model):
    __tablename__ = 'perfis'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)

class NaturezaDespesa(db.Model):
    __tablename__ = 'natureza_despesa'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    numero = db.Column(db.String(20), nullable=True)  # Coluna numero confirmada
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
