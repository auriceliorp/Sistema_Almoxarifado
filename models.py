from flask_login import UserMixin


# ------------------- USUÁRIO E PERFIL -------------------
class Perfil(db.Model):
    __tablename__ = 'perfis'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    matricula = db.Column(db.String(50))
    ramal = db.Column(db.String(20))
    unidade_local_id = db.Column(db.Integer, db.ForeignKey('unidade_local.id'))
    unidade_local = db.relationship('UnidadeLocal', back_populates='usuarios')
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfis.id'))
    perfil = db.relationship('Perfil', backref='usuarios')
    senha_temporaria = db.Column(db.Boolean, default=True)

# ------------------- NATUREZA DE DESPESA -------------------
class NaturezaDespesa(db.Model):
    __tablename__ = 'natureza_despesa'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    grupos = db.relationship('Grupo', back_populates='natureza_despesa')
    itens = db.relationship('Item', back_populates='natureza_despesa')

# ------------------- GRUPO DE ITENS -------------------
class Grupo(db.Model):
    __tablename__ = 'grupos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    natureza_despesa_id = db.Column(db.Integer, db.ForeignKey('natureza_despesa.id'), nullable=False)
    natureza_despesa = db.relationship('NaturezaDespesa', back_populates='grupos')
    itens = db.relationship('Item', back_populates='grupo')

# ------------------- ITEM -------------------
class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    codigo_sap = db.Column(db.String(50), nullable=False)
    codigo_siads = db.Column(db.String(50))
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False, default='')
    unidade = db.Column(db.String(50), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'))
    grupo = db.relationship('Grupo', back_populates='itens')
    natureza_despesa_id = db.Column(db.Integer, db.ForeignKey('natureza_despesa.id'), nullable=False)
    natureza_despesa = db.relationship('NaturezaDespesa', back_populates='itens')
    valor_unitario = db.Column(db.Float, default=0.0)
    saldo_financeiro = db.Column(db.Float, default=0.0)
    estoque_atual = db.Column(db.Float, default=0.0)
    estoque_minimo = db.Column(db.Float, default=0.0)
    localizacao = db.Column(db.String(120), default='')
    data_validade = db.Column(db.Date, nullable=True)

# ------------------- ESTOQUE -------------------
class Estoque(db.Model):
    __tablename__ = 'estoque'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    item = db.relationship('Item')
    fornecedor = db.Column(db.String(120), nullable=False)
    nota_fiscal = db.Column(db.String(50))
    valor_unitario = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    local = db.Column(db.String(120), nullable=False)
    valor_total = db.Column(db.Float, nullable=False)

# ------------------- FORNECEDOR -------------------
class Fornecedor(db.Model):
    __tablename__ = 'fornecedor'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)

# ------------------- LOCAL E UNIDADE LOCAL -------------------
class Local(db.Model):
    __tablename__ = 'local'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(120), nullable=False)
    uls = db.relationship('UnidadeLocal', back_populates='local', lazy=True)

class UnidadeLocal(db.Model):
    __tablename__ = 'unidade_local'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(120), nullable=False)
    local_id = db.Column(db.Integer, db.ForeignKey('local.id'), nullable=False)
    local = db.relationship('Local', back_populates='uls')
    usuarios = db.relationship('Usuario', back_populates='unidade_local')
  