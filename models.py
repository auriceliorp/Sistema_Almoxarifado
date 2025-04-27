# -*- coding: utf-8 -*-
from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # Importar UserMixin

# Tabela de Associação para o relacionamento muitos-para-muitos (se necessário, mas não usado diretamente aqui)
# Exemplo: Se um usuário pudesse ter múltiplos perfis
# user_profiles = db.Table(
#     'user_profiles',
#     db.Column('user_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
#     db.Column('profile_id', db.Integer, db.ForeignKey('perfis.id'), primary_key=True)
# )

class Perfil(db.Model):
    __tablename__ = 'perfis'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False) # Ex: 'Administrador', 'Solicitante'
    usuarios = db.relationship('Usuario', backref='perfil', lazy=True)

    def __repr__(self):
        return f'<Perfil {self.nome}>'

# Adicionar UserMixin à classe Usuario
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfis.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    requisicoes_solicitadas = db.relationship('Requisicao', foreign_keys='Requisicao.solicitante_id', backref='solicitante', lazy=True)
    requisicoes_aprovadas = db.relationship('Requisicao', foreign_keys='Requisicao.aprovador_id', backref='aprovador', lazy=True)
    movimentos_registrados = db.relationship('MovimentoEstoque', backref='registrado_por', lazy=True)

    def set_password(self, password):
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)

    # Propriedades/métodos requeridos por Flask-Login (além de UserMixin)
    # is_active já é atendido pelo campo 'ativo'
    # get_id já é atendido pelo campo 'id'
    # is_authenticated é gerenciado pelo Flask-Login
    # is_anonymous é gerenciado pelo Flask-Login

    # Métodos para verificação de perfil (simplificado)
    def is_admin(self):
        return self.perfil and self.perfil.nome == 'Administrador'

    def is_solicitante(self):
        return self.perfil and self.perfil.nome == 'Solicitante'

    def __repr__(self):
        return f'<Usuario {self.nome}>'

class NaturezaDespesa(db.Model):
    __tablename__ = 'naturezas_despesa'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    descricao = db.Column(db.String(255), nullable=False)
    ativa = db.Column(db.Boolean, default=True)
    itens = db.relationship('Item', backref='natureza_despesa', lazy=True)

    def __repr__(self):
        return f'<NaturezaDespesa {self.codigo} - {self.descricao}>'

class Item(db.Model):
    __tablename__ = 'itens'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, index=True)
    descricao = db.Column(db.Text)
    unidade_medida = db.Column(db.String(30))
    natureza_despesa_id = db.Column(db.Integer, db.ForeignKey('naturezas_despesa.id'), nullable=False, index=True)
    estoque_minimo = db.Column(db.Integer, default=0)
    ponto_ressuprimento = db.Column(db.Integer, default=0)
    saldo_atual = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    movimentos = db.relationship('MovimentoEstoque', backref='item', lazy='dynamic') # lazy='dynamic' para poder filtrar/ordenar
    itens_requisicao = db.relationship('RequisicaoItem', backref='item', lazy=True)

    def __repr__(self):
        return f'<Item {self.nome}>'

class Requisicao(db.Model):
    __tablename__ = 'requisicoes'
    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    data_requisicao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='PENDENTE', index=True)
    observacao_solicitante = db.Column(db.Text)
    aprovador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    observacao_aprovador = db.Column(db.Text)

    # Relacionamento com itens da requisição
    itens_requisicao = db.relationship('RequisicaoItem', backref='requisicao', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Requisicao {self.id} - Status: {self.status}>'

class RequisicaoItem(db.Model):
    __tablename__ = 'requisicao_itens'
    id = db.Column(db.Integer, primary_key=True)
    requisicao_id = db.Column(db.Integer, db.ForeignKey('requisicoes.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False, index=True)
    quantidade_solicitada = db.Column(db.Integer, nullable=False)
    quantidade_atendida = db.Column(db.Integer, default=0)

    # Relacionamento com movimentos (se uma saída for diretamente ligada a este item)
    movimentos_estoque = db.relationship('MovimentoEstoque', backref='requisicao_item_associado', lazy=True)

    # Unique constraint (opcional no modelo, mas presente no DDL)
    __table_args__ = (db.UniqueConstraint('requisicao_id', 'item_id', name='uq_requisicao_item'),)

    def __repr__(self):
        return f'<RequisicaoItem Req:{self.requisicao_id} Item:{self.item_id} Qtd:{self.quantidade_solicitada}>'

class MovimentoEstoque(db.Model):
    __tablename__ = 'movimentos_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # ENTRADA, SAIDA_REQUISICAO, SAIDA_AJUSTE, ENTRADA_AJUSTE, INVENTARIO_INICIAL
    quantidade = db.Column(db.Integer, nullable=False)
    data_movimento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    observacao = db.Column(db.Text)
    saldo_anterior = db.Column(db.Integer, nullable=False)
    saldo_posterior = db.Column(db.Integer, nullable=False)
    requisicao_item_id = db.Column(db.Integer, db.ForeignKey('requisicao_itens.id'), nullable=True)
    
    # Relacionamentos
    item = db.relationship('Item', backref=db.backref('movimentos', lazy=True))
    registrado_por = db.relationship('Usuario', backref=db.backref('movimentos_registrados', lazy=True))
    requisicao_item_associado = db.relationship('RequisicaoItem', backref=db.backref('movimentos', lazy=True))


# Nota: A lógica do trigger `atualizar_saldo_item` presente no schema.sql
# precisará ser implementada na lógica da aplicação (antes de salvar um MovimentoEstoque)
# se não estivermos usando o trigger diretamente no banco de dados.
# Flask-SQLAlchemy não executa triggers automaticamente ao fazer db.session.add/commit.
# Uma abordagem comum é usar os eventos do SQLAlchemy ou lógica explícita nas rotas/serviços.
# Para simplificar inicialmente, podemos assumir que o trigger do BD está ativo
# ou implementar a lógica de atualização de saldo no backend antes do commit.

