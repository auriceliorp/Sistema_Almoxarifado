# ------------------- FORNECEDOR -------------------
class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    id = db.Column(db.Integer, primary_key=True)

    # Campos obrigatórios
    nome = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)

    # Contato
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    celular = db.Column(db.String(20), nullable=True)

    # Endereço
    endereco = db.Column(db.String(200), nullable=True)
    numero = db.Column(db.String(10), nullable=True)
    complemento = db.Column(db.String(100), nullable=True)
    cep = db.Column(db.String(10), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    uf = db.Column(db.String(2), nullable=True)

    # Dados fiscais
    inscricao_estadual = db.Column(db.String(50), nullable=True)
    inscricao_municipal = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Fornecedor {self.nome}>'