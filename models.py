from .database import db
from datetime import datetime # Se necessário para valores padrão
# Colar TODAS as suas classes de modelos aqui
# (Usuario, Perfil, NaturezaDespesa, Item, MovimentoEstoque)

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'), nullable=False)
    # ... resto da classe Usuario ...

class Perfil(db.Model):
    # ... definição de Perfil ...

class NaturezaDespesa(db.Model):
    # ... definição de NaturezaDespesa ...

class Item(db.Model):
    # ... definição de Item ...

# !! Adicione a definição de MovimentoEstoque aqui !!
class MovimentoEstoque(db.Model):
    __tablename__ = 'movimento_estoque'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False) # ENTRADA, SAIDA_AJUSTE, etc.
    quantidade = db.Column(db.Float, nullable=False)
    data_movimento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    observacao = db.Column(db.Text, nullable=True)
    saldo_anterior = db.Column(db.Float, nullable=False)
    saldo_posterior = db.Column(db.Float, nullable=False)

    # Relações (ajuste os nomes backref se necessário)
    item = db.relationship('Item', backref=db.backref('movimentos', lazy=True))
    registrado_por = db.relationship('Usuario', backref=db.backref('movimentos_registrados', lazy=True))

