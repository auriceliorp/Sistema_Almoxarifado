# popular_dados.py
# Popula o banco com dados fictícios sem duplicação

from faker import Faker
import random
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app_render import db
from models import NaturezaDespesa, Grupo, Item, Fornecedor, Usuario, Perfil, UnidadeLocal, Local, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem

fake = Faker('pt_BR')

# ---------------------- PERFIS ----------------------
perfis = ['Administrador', 'Solicitante', 'Consultor']
for nome in perfis:
    if not Perfil.query.filter_by(nome=nome).first():
        db.session.add(Perfil(nome=nome))
db.session.commit()

# ---------------------- LOCAL E UNIDADE LOCAL ----------------------
locais = []
for i in range(1, 6):
    descricao = f"Bloco {chr(64+i)}"
    if not Local.query.filter_by(descricao=descricao).first():
        local = Local(descricao=descricao)
        db.session.add(local)
        locais.append(local)
db.session.commit()
locais = Local.query.all()

uls = []
for i, local in enumerate(locais, start=1):
    codigo = f"UL{i:02}"
    if not UnidadeLocal.query.filter_by(codigo=codigo).first():
        ul = UnidadeLocal(codigo=codigo, descricao=fake.company(), local=local)
        db.session.add(ul)
        uls.append(ul)
db.session.commit()
uls = UnidadeLocal.query.all()

# ---------------------- USUÁRIOS ----------------------
for i in range(1, 6):
    email = f"usuario{i}@teste.com"
    if not Usuario.query.filter_by(email=email).first():
        user = Usuario(
            nome=fake.name(),
            email=email,
            senha=generate_password_hash("123456"),
            matricula=f"MAT{i:03}",
            ramal=f"{random.randint(1000,9999)}",
            unidade_local=random.choice(uls),
            perfil=Perfil.query.filter_by(nome='Solicitante').first(),
            senha_temporaria=False
        )
        db.session.add(user)
db.session.commit()

# ---------------------- NATUREZAS DE DESPESA ----------------------
naturezas = []
for i in range(1, 21):
    codigo = f"ND{i:03}"
    if not NaturezaDespesa.query.filter_by(codigo=codigo).first():
        nd = NaturezaDespesa(
            codigo=codigo,
            nome=fake.unique.word().capitalize(),
            valor=0.0
        )
        db.session.add(nd)
        naturezas.append(nd)
db.session.commit()
naturezas = NaturezaDespesa.query.all()

# ---------------------- GRUPOS ----------------------
grupos = []
for nd in naturezas:
    nome = fake.unique.word().capitalize()
    if not Grupo.query.filter_by(nome=nome, natureza_despesa=nd).first():
        grupo = Grupo(nome=nome, natureza_despesa=nd)
        db.session.add(grupo)
        grupos.append(grupo)
db.session.commit()
grupos = Grupo.query.all()

# ---------------------- ITENS ----------------------
itens = []
for i in range(20):
    codigo_sap = f"SAP{i+1000}"
    if not Item.query.filter_by(codigo_sap=codigo_sap).first():
        grupo = grupos[i]
        item = Item(
            codigo_sap=codigo_sap,
            codigo_siads=f"SIADS{i+2000}",
            nome=fake.unique.word().capitalize(),
            descricao=fake.sentence(),
            unidade="UN",
            grupo=grupo,
            natureza_despesa=grupo.natureza_despesa,
            valor_unitario=round(random.uniform(10, 500), 2),
            saldo_financeiro=0.0,
            estoque_atual=0,
            estoque_minimo=random.randint(1, 10),
            localizacao=f"Estante {random.randint(1, 10)}",
            data_validade=date.today() + timedelta(days=random.randint(30, 365))
        )
        db.session.add(item)
        itens.append(item)
db.session.commit()
itens = Item.query.all()

# ---------------------- FORNECEDORES ----------------------
for _ in range(20):
    cnpj = fake.unique.cnpj()
    if not Fornecedor.query.filter_by(cnpj=cnpj).first():
        fornecedor = Fornecedor(
            nome=fake.company(),
            cnpj=cnpj,
            email=fake.company_email(),
            telefone=fake.phone_number(),
            celular=fake.cellphone_number(),
            endereco=fake.street_name(),
            numero=str(fake.building_number()),
            complemento=fake.bairro(),
            cep=fake.postcode(),
            cidade=fake.city(),
            uf=fake.estado_sigla(),
            inscricao_estadual=str(random.randint(1000000, 9999999)),
            inscricao_municipal=str(random.randint(1000000, 9999999))
        )
        db.session.add(fornecedor)
db.session.commit()
fornecedores = Fornecedor.query.all()
usuarios = Usuario.query.all()

# ---------------------- ENTRADAS ----------------------
for _ in range(10):
    entrada = EntradaMaterial(
        data_movimento=date.today(),
        data_nota_fiscal=date.today(),
        numero_nota_fiscal=fake.numerify(text='###.###.###'),
        fornecedor=random.choice(fornecedores),
        usuario=random.choice(usuarios)
    )
    db.session.add(entrada)
    db.session.flush()

    for _ in range(3):
        item = random.choice(itens)
        quantidade = random.randint(1, 10)
        valor_unitario = item.valor_unitario

        db.session.add(EntradaItem(
            entrada_id=entrada.id,
            item_id=item.id,
            quantidade=quantidade,
            valor_unitario=valor_unitario
        ))

        item.estoque_atual += quantidade
        item.saldo_financeiro += quantidade * valor_unitario
db.session.commit()

# ---------------------- SAÍDAS ----------------------
for _ in range(10):
    saida = SaidaMaterial(
        data_movimento=date.today(),
        numero_documento=fake.bothify(text='DOC-#####'),
        observacao=fake.sentence(),
        usuario=random.choice(usuarios),
        solicitante=random.choice(usuarios)
    )
    db.session.add(saida)
    db.session.flush()

    for _ in range(2):
        item = random.choice(itens)
        quantidade = random.randint(1, 3)
        valor_unitario = item.valor_unitario

        if item.estoque_atual >= quantidade:
            db.session.add(SaidaItem(
                saida_id=saida.id,
                item_id=item.id,
                quantidade=quantidade,
                valor_unitario=valor_unitario
            ))

            item.estoque_atual -= quantidade
            item.saldo_financeiro -= quantidade * valor_unitario
db.session.commit()

print("Base de dados populada com sucesso!")