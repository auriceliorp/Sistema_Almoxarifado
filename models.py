# ------------------------------ IMPORTAÇÕES ------------------------------
from flask_login import UserMixin
from app_render import db



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
    """Modelo para representar fornecedores cadastrados no sistema."""
    
    __tablename__ = 'fornecedores'  # Nome da tabela no banco de dados

    # Campo identificador primário, gerado automaticamente
    id = db.Column(db.Integer, primary_key=True)

    # Nome do fornecedor (campo obrigatório)
    nome = db.Column(db.String(120), nullable=False)

    # CNPJ do fornecedor (campo obrigatório)
    cnpj = db.Column(db.String(20), nullable=False)

    # E-mail do fornecedor (campo opcional)
    email = db.Column(db.String(120), nullable=True)

    # Telefone do fornecedor (campo opcional)
    telefone = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        """Representação da instância do modelo para depuração."""
        return f'<Fornecedor {self.nome}>'

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


# ------------------- ENTRADA DE MATERIAL -------------------

class EntradaMaterial(db.Model):
    __tablename__ = 'entrada_material'
    id = db.Column(db.Integer, primary_key=True)
    data_movimento = db.Column(db.Date, nullable=False)
    data_nota_fiscal = db.Column(db.Date, nullable=False)
    numero_nota_fiscal = db.Column(db.String(50), nullable=False)

    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)

    fornecedor = db.relationship('Fornecedor', backref='entradas')
    itens = db.relationship('EntradaItem', backref='entrada_material', cascade="all, delete-orphan")


class EntradaItem(db.Model):
    __tablename__ = 'entrada_item'
    id = db.Column(db.Integer, primary_key=True)
    entrada_id = db.Column(db.Integer, db.ForeignKey('entrada_material.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    item = db.relationship('Item', backref='entradas')

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario


# ------------------------------ MODELO DE SAÍDA DE MATERIAL ------------------------------ #
class SaidaMaterial(db.Model):
    __tablename__ = 'saida_material'

    id = db.Column(db.Integer, primary_key=True)
    data_saida = db.Column(db.Date, nullable=False)
    destino = db.Column(db.String(120), nullable=False)
    responsavel = db.Column(db.String(120), nullable=False)

    # Relacionamento com os itens da saída
    itens = db.relationship('SaidaItem', backref='saida', lazy=True, cascade="all, delete-orphan")


# ------------------------------ MODELO DE ITENS DA SAÍDA ------------------------------ #
class SaidaItem(db.Model):
    __tablename__ = 'saida_item'

    id = db.Column(db.Integer, primary_key=True)
    saida_id = db.Column(db.Integer, db.ForeignKey('saida_material.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relacionamento com o item
    item = db.relationship('Item', backref='saidas_item')
  
