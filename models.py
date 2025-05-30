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
    valor = db.Column(db.Numeric(10, 2), default=0.0)  # Alterado para Numeric
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
    valor_unitario = db.Column(db.Numeric(10, 2), default=0.0)  # Alterado para Numeric
    valor_medio = db.Column(db.Numeric(10, 2), default=0.0)  # Alterado para Numeric
    saldo_financeiro = db.Column(db.Numeric(10, 2), default=0.0)  # Alterado para Numeric
    estoque_atual = db.Column(db.Numeric(10, 2), default=0.0)  # Alterado para Numeric
    estoque_minimo = db.Column(db.Numeric(10, 2), default=0.0)  # Alterado para Numeric
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
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # Alterado para Numeric
    quantidade = db.Column(db.Integer, nullable=False)
    local = db.Column(db.String(120), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)  # Alterado para Numeric

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
    estornada = db.Column(db.Boolean, default=False)

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
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # Já está como Numeric

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

    estornada = db.Column(db.Boolean, default=False)

    itens = db.relationship(
        'SaidaItem',
        backref='saida_material',
        cascade='all, delete-orphan',
        overlaps="saida,itens_relacionados"
    )

class SaidaItem(db.Model):
    __tablename__ = 'saida_item'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # Alterado para Numeric

    saida_id = db.Column(db.Integer, db.ForeignKey('saida_material.id'), nullable=False)

    item = db.relationship('Item', backref='saidas')
    saida = db.relationship(
        'SaidaMaterial',
        backref='itens_relacionados',
        overlaps="saida_material,itens"
    )

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario

# ------------------- LOG AUDITÁVEL -------------------
class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario')
    acao = db.Column(db.String(20), nullable=False)
    tabela = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=True)
    dados_anteriores = db.Column(db.Text)
    dados_novos = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- PAINEL DE CONTRATAÇÕES -------------------
class PainelContratacao(db.Model):
    __tablename__ = 'painel_contratacoes'
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    data_abertura = db.Column(db.Date, nullable=True)
    data_homologacao = db.Column(db.Date, nullable=True)
    periodo_dias = db.Column(db.Integer, nullable=True)
    numero_sei = db.Column(db.String(25), nullable=False)
    modalidade = db.Column(db.String(100), nullable=True)
    registro_precos = db.Column(db.String(100), nullable=True)
    orgaos_participantes = db.Column(db.Text, nullable=True)
    numero_licitacao = db.Column(db.String(50), nullable=True)
    parecer_juridico = db.Column(db.String(100), nullable=True)
    fundamentacao_legal = db.Column(db.Text, nullable=True)
    objeto = db.Column(db.Text, nullable=False)
    natureza_despesa = db.Column(db.String(100), nullable=True)
    valor_estimado = db.Column(db.Numeric(14, 2), nullable=True)  # Já está como Numeric
    valor_homologado = db.Column(db.Numeric(14, 2), nullable=True)  # Já está como Numeric
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
class BemPatrimonial(db.Model):
    __tablename__ = 'bens_patrimoniais'
    id = db.Column(db.Integer, primary_key=True)
    numero_ul = db.Column(db.String(50), unique=True, nullable=False)
    numero_sap = db.Column(db.String(50), unique=True, nullable=False)
    numero_siads = db.Column(db.String(50), unique=True, nullable=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    grupo_bem = db.Column(db.String(100), nullable=True)
    classificacao_contabil = db.Column(db.String(100), nullable=True)
    foto = db.Column(db.String(255), nullable=True)
    detentor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    excluido = db.Column(db.Boolean, default=False)
    detentor = db.relationship('Usuario', backref='bens')
    localizacao = db.Column(db.String(100), nullable=True)
    data_aquisicao = db.Column(db.Date, nullable=True)
    valor_aquisicao = db.Column(db.Numeric(10, 2), nullable=True)  # Alterado para Numeric
    status = db.Column(db.String(50), default='Ativo')
    situacao = db.Column(db.String(50), default='Em uso')
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

# ------------------- TIPO DE BEM PATRIMONIAL -------------------
class TipoBem(db.Model):
    __tablename__ = 'tipos_bem'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    descricao = db.Column(db.String(150), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_patrimonio.id'), nullable=False)
    grupo = db.relationship('GrupoPatrimonio', backref='tipos_bem')

    def __repr__(self):
        return f"<TipoBem {self.codigo} - {self.descricao}>"

# ------------------- MOVIMENTAÇÃO DE BENS -------------------
class MovimentacaoBem(db.Model):
    __tablename__ = 'movimentacoes_bem'
    id = db.Column(db.Integer, primary_key=True)
    bem_id = db.Column(db.Integer, db.ForeignKey('bens_patrimoniais.id'), nullable=False)
    bem = db.relationship('BemPatrimonial', backref='movimentacoes')
    tipo_movimentacao = db.Column(db.String(50), nullable=False)
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    origem_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    destino_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    origem = db.relationship('Usuario', foreign_keys=[origem_id])
    destino = db.relationship('Usuario', foreign_keys=[destino_id])
    localizacao_anterior = db.Column(db.String(100))
    nova_localizacao = db.Column(db.String(100))
    motivo = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pendente')
    data_conclusao = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<MovimentacaoBem {self.tipo_movimentacao} - Bem {self.bem_id}>"

# ------------------- TIPO DE PUBLICAÇÃO -------------------
class TipoPublicacao(db.Model):
    __tablename__ = 'tipos_publicacao'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    requer_contrato = db.Column(db.Boolean, default=False)
    requer_valor = db.Column(db.Boolean, default=False)
    requer_vigencia = db.Column(db.Boolean, default=False)
    requer_partes = db.Column(db.Boolean, default=True)
    publicacoes = db.relationship('Publicacao', back_populates='tipo')

    def __repr__(self):
        return f"<TipoPublicacao {self.codigo} - {self.nome}>"

# ------------------- PUBLICAÇÃO -------------------
class Publicacao(db.Model):
    __tablename__ = 'publicacoes'
    id = db.Column(db.Integer, primary_key=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipos_publicacao.id'), nullable=False)
    tipo = db.relationship('TipoPublicacao', back_populates='publicacoes')
    especie = db.Column(db.String(200), nullable=False)
    contrato_saic = db.Column(db.String(100), default='Não Aplicável')
    objeto = db.Column(db.Text, nullable=False)
    modalidade_licitacao = db.Column(db.String(50), default='Não se Aplica')
    fonte_recursos = db.Column(db.String(200), default='Não se Aplica')
    valor_global = db.Column(db.String(100), default='Não Aplicável')
    vigencia_inicio = db.Column(db.Date, nullable=True)
    vigencia_fim = db.Column(db.Date, nullable=True)
    data_assinatura = db.Column(db.Date, nullable=False)
    excluido = db.Column(db.Boolean, default=False)

    partes_embrapa = db.relationship(
        'Usuario',
        secondary='publicacao_partes_embrapa',
        backref=db.backref('publicacoes_partes', lazy='dynamic')
    )
    
    partes_fornecedor = db.relationship(
        'Fornecedor',
        secondary='publicacao_partes_fornecedor',
        backref=db.backref('publicacoes_partes', lazy='dynamic')
    )
    
    signatarios_embrapa = db.relationship(
        'Usuario',
        secondary='publicacao_signatarios_embrapa',
        backref=db.backref('publicacoes_assinadas_embrapa', lazy='dynamic')
    )
    
    signatarios_externos = db.relationship(
        'Fornecedor',
        secondary='publicacao_signatarios_externos',
        backref=db.backref('publicacoes_assinadas_fornecedor', lazy='dynamic')
    )

    def __repr__(self):
        return f"<Publicacao {self.especie} - {self.contrato_saic}>"

# Tabelas de relacionamento many-to-many para Publicações
class PublicacaoPartesEmbrapa(db.Model):
    __tablename__ = 'publicacao_partes_embrapa'
    publicacao_id = db.Column(db.Integer, db.ForeignKey('publicacoes.id'), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)

class PublicacaoPartesFornecedor(db.Model):
    __tablename__ = 'publicacao_partes_fornecedor'
    publicacao_id = db.Column(db.Integer, db.ForeignKey('publicacoes.id'), primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), primary_key=True)

class PublicacaoSignatariosEmbrapa(db.Model):
    __tablename__ = 'publicacao_signatarios_embrapa'
    publicacao_id = db.Column(db.Integer, db.ForeignKey('publicacoes.id'), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)

class PublicacaoSignatariosExternos(db.Model):
    __tablename__ = 'publicacao_signatarios_externos'
    publicacao_id = db.Column(db.Integer, db.ForeignKey('publicacoes.id'), primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), primary_key=True)
