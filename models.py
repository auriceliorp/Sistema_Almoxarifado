from database import db
from datetime import datetime
from flask_login import UserMixin

# Classe Usuario (com UserMixin obrigatório para Flask-Login)
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.Text, nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'), nullable=False)

    perfil = db.relationship('Perfil', backref=db.backref('usuarios', lazy=True))

# Classe Perfil
class Perfil(db.Model):
    __tablename__ = 'perfil'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)

# Classe NaturezaDespesa
class NaturezaDespesa(db.Model):
    __tablename__ = 'natureza_despesa'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    descricao = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<NaturezaDespesa {self.codigo} - {self.descricao}>"

# Classe Item
class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    quantidade_estoque = db.Column(db.Float, nullable=False, default=0.0)
    natureza_despesa_id = db.Column(db.Integer, db.ForeignKey('natureza_despesa.id'), nullable=True)

    natureza_despesa = db.relationship('NaturezaDespesa', backref=db.backref('itens', lazy=True))

    def __repr__(self):
        return f"<Item {self.nome} - Qtd: {self.quantidade_estoque}>"

# Classe MovimentoEstoque
class MovimentoEstoque(db.Model):
    __tablename__ = 'movimento_estoque'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # ENTRADA, SAIDA_AJUSTE, etc.
    quantidade = db.Column(db.Float, nullable=False)
    data_movimento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    observacao = db.Column(db.Text, nullable=True)
    saldo_anterior = db.Column(db.Float, nullable=False)
    saldo_posterior = db.Column(db.Float, nullable=False)

    item = db.relationship('Item', backref=db.backref('movimentos', lazy=True))
    registrado_por = db.relationship('Usuario', backref=db.backref('movimentos_registrados', lazy=True))
