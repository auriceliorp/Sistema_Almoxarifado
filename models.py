# ------------------------------ IMPORTAÇÕES ------------------------------
from flask_login import UserMixin
from extensoes import db
from datetime import datetime

# ------------------- USUÁRIO E PERFIL -------------------
class Perfil(db.Model):
    __tablename__ = 'perfil'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    matricula = db.Column(db.String(50))
    ramal = db.Column(db.String(20))
    unidade_local_id = db.Column(db.Integer, db.ForeignKey('unidade_local.id'))
    unidade_local = db.relationship('UnidadeLocal', back_populates='usuarios')
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'))
    perfil = db.relationship('Perfil', backref='usuarios')
    senha_temporaria = db.Column(db.Boolean, default=True)

# ------------------- NATUREZA DE DESPESA -------------------
class NaturezaDespesa(db.Model):
    __tablename__ = 'natureza_despesa'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, default=0.0)
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
    __tablename__ = 'fornecedores'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # 'Pessoa Física' ou 'Pessoa Jurídica'
    nome = db.Column(db.String(120), nullable=False)
    cnpj_cpf = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    celular = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(200), nullable=True)
    numero = db.Column(db.String(10), nullable=True)
    complemento = db.Column(db.String(100), nullable=True)
    cep = db.Column(db.String(10), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    uf = db.Column(db.String(2), nullable=True)
    inscricao_estadual = db.Column(db.String(50), nullable=True)
    inscricao_municipal = db.Column(db.String(50), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('nome', 'cnpj_cpf', name='uq_nome_cnpjcpf'),
    )

    def __repr__(self):
        return f'<Fornecedor {self.nome} - {self.cnpj_cpf}>'


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
    estornada = db.Column(db.Boolean, default=False)  # <-- NOVO

    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    fornecedor = db.relationship('Fornecedor', backref='entradas')

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', backref='entradas')

    itens = db.relationship(
        'EntradaItem',
        backref='entrada_material',
        cascade="all, delete-orphan",
        overlaps="entrada,itens_relacionados"
    )

class EntradaItem(db.Model):
    __tablename__ = 'entrada_item'
    id = db.Column(db.Integer, primary_key=True)
    entrada_id = db.Column(db.Integer, db.ForeignKey('entrada_material.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    item = db.relationship('Item', backref='entradas')
    entrada = db.relationship(
        'EntradaMaterial',
        backref='itens_relacionados',
        overlaps="entrada_material,itens"
    )

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario

# ------------------- SAÍDA DE MATERIAL -------------------
class SaidaMaterial(db.Model):
    __tablename__ = 'saida_material'
    id = db.Column(db.Integer, primary_key=True)
    data_movimento = db.Column(db.Date, nullable=False)
    numero_documento = db.Column(db.String(50), nullable=True)
    observacao = db.Column(db.Text, nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='saidas')

    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref='solicitacoes_saida')

    # ✅ Campo correto: deve estar aqui
    estornada = db.Column(db.Boolean, default=False)

    # Relacionamento com itens da saída
    itens = db.relationship(
        'SaidaItem',
        backref='saida_material',
        cascade='all, delete-orphan',
        overlaps="saida,itens_relacionados"
    )


# ------------------- ITEM DA SAÍDA -------------------
class SaidaItem(db.Model):
    __tablename__ = 'saida_item'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)

    saida_id = db.Column(db.Integer, db.ForeignKey('saida_material.id'), nullable=False)

    item = db.relationship('Item', backref='saidas')

    # Evita conflito de relacionamento reverso com overlaps
    saida = db.relationship(
        'SaidaMaterial',
        backref='itens_relacionados',
        overlaps="saida_material,itens"
    )

# ------------------- LOG AUDITÁVEL -------------------
class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    # Chave primária do log
    id = db.Column(db.Integer, primary_key=True)

    # ID do usuário responsável pela ação (nullable em casos automatizados)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario')

    # Tipo de ação realizada: ex: 'inserção', 'edição', 'exclusão', 'estorno', etc.
    acao = db.Column(db.String(20), nullable=False)

    # Nome da tabela afetada (ex: 'entrada_material', 'item', etc.)
    tabela = db.Column(db.String(50), nullable=False)

    # ID do registro afetado na tabela (opcional)
    registro_id = db.Column(db.Integer, nullable=True)

    # Dados antes da ação (JSON serializado em string)
    dados_anteriores = db.Column(db.Text)

    # Dados após a ação (JSON serializado em string)
    dados_novos = db.Column(db.Text)

    # Data e hora da operação
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- PAINEL DE CONTRATAÇÕES -------------------
class PainelContratacao(db.Model):
    __tablename__ = 'painel_contratacoes'

    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    data_abertura = db.Column(db.Date, nullable=True)
    data_homologacao = db.Column(db.Date, nullable=True)
    periodo_dias = db.Column(db.Integer, nullable=True)

    numero_sei = db.Column(db.String(25), nullable=False)  # Ex: 21152.000001/2025-57
    modalidade = db.Column(db.String(100), nullable=True)
    registro_precos = db.Column(db.String(100), nullable=True)
    orgaos_participantes = db.Column(db.Text, nullable=True)
    numero_licitacao = db.Column(db.String(50), nullable=True)

    parecer_juridico = db.Column(db.String(100), nullable=True)
    fundamentacao_legal = db.Column(db.Text, nullable=True)
    objeto = db.Column(db.Text, nullable=False)

    natureza_despesa = db.Column(db.String(100), nullable=True)
    valor_estimado = db.Column(db.Numeric(14, 2), nullable=True)
    valor_homologado = db.Column(db.Numeric(14, 2), nullable=True)
    percentual_economia = db.Column(db.String(10), nullable=True)

    impugnacao = db.Column(db.String(10), nullable=True)
    recurso = db.Column(db.String(10), nullable=True)
    itens_desertos = db.Column(db.String(10), nullable=True)

    responsavel_conducao = db.Column(db.String(100), nullable=True)
    setor_responsavel = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    excluido = db.Column(db.Boolean, default=False)

    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id])



    def __repr__(self):
        return f"<PainelContratacao {self.numero_sei}>"


# ------------------- CONTROLE DE BENS -------------------
from extensoes import db
from datetime import datetime
class BemPatrimonial(db.Model):
    __tablename__ = 'bens_patrimoniais'

    id = db.Column(db.Integer, primary_key=True)
    
    numero_ul = db.Column(db.String(50), unique=True, nullable=False)       # Nº Patrimônio da Unidade Local
    numero_sap = db.Column(db.String(50), unique=True, nullable=False)      # Nº SAP
    numero_siads = db.Column(db.String(50), unique=True, nullable=True)     # Nº SIADS (pode ser preenchido depois)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    grupo_bem = db.Column(db.String(100), nullable=True)                    # Grupo ou categoria do bem
    classificacao_contabil = db.Column(db.String(100), nullable=True)       # Classificação contábil
    foto = db.Column(db.String(255), nullable=True)                         # Caminho para o arquivo da foto
    detentor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    excluido = db.Column(db.Boolean, default=False)
    detentor = db.relationship('Usuario', backref='bens')
    localizacao = db.Column(db.String(100), nullable=True)
    data_aquisicao = db.Column(db.Date, nullable=True)
    valor_aquisicao = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='Ativo')  # Ativo, Baixado, Em transferência etc.
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text, nullable=True)


    def __repr__(self):
        return f"<BemPatrimonial {self.numero_ul} - {self.nome}>"

# ------------------- GRUPO DE BENS PATRIMONIAIS -------------------
class GrupoPatrimonio(db.Model):
    __tablename__ = 'grupos_patrimonio'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"<GrupoPatrimonio {self.codigo} - {self.descricao}>"

