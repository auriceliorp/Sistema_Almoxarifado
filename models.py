# models.py
from database import db
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(150), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'))

    perfil = db.relationship('Perfil', back_populates='usuarios')

class Perfil(db.Model):
    __tablename__ = 'perfil'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)

    usuarios = db.relationship('Usuario', back_populates='perfil')

class NaturezaDespesa(db.Model):
    __tablename__ = 'natureza_despesa'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)   # Novo campo obrigatório
    numero = db.Column(db.String(20), nullable=False)   # Número da ND
    nome = db.Column(db.String(255), nullable=False)    # Nome resumido
    descricao = db.Column(db.String(255))               # Descrição opcional
