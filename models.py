# models.py atualizado

from database import db
from flask_login import UserMixin

class Perfil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    senha = db.Column(db.String(200), nullable=True)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'), nullable=True)
    perfil = db.relationship('Perfil', backref=db.backref('usuarios', lazy=True))
    matricula = db.Column(db.String(50), nullable=True)  # NOVO

class NaturezaDespesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    numero = db.Column(db.String(50), nullable=True)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    natureza_despesa_id = db.Column(db.Integer, db.ForeignKey('natureza_despesa.id'), nullable=False)
    natureza_despesa = db.relationship('NaturezaDespesa', backref=db.backref('itens', lazy=True))

class Estoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    fornecedor = db.Column(db.String(255), nullable=False)
    nota_fiscal = db.Column(db.String(100), nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    local = db.Column(db.String(100), nullable=False)
    valor_total = db.Column(db.Float, nullable=False)

    item = db.relationship('Item', backref=db.backref('estoques', lazy=True))
