# -*- coding: utf-8 -*-
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import datetime
from sqlalchemy.exc import OperationalError # Importar para tratamento de erro no load_user

# --- É melhor prática ter modelos em models.py e config em config.py ---
# --- Mas mantendo a estrutura do seu ficheiro por agora ---

# Inicializar extensões globalmente
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login" # Assumindo que 'main' trata do login
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# Modelos (Copiados do seu ficheiro)
# (É recomendado movê-los para models.py)
class Usuario(db.Model):
    __tablename__ = 'usuario' # Definir nome da tabela explicitamente é boa prática
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False) # Aumentar tamanho para hashes
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'), nullable=False)
    # Relação com Perfil (já definida no seu código)
    # perfil = db.relationship('Perfil', backref=db.backref('usuarios', lazy=True))

    # Métodos Flask-Login (simplificados, assumindo que UserMixin não está a ser usado)
    @property
    def is_authenticated(self):
        return True
    @property
    def is_active(self):
        # Poderia verificar um campo 'ativo' no futuro
        return True
    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    # Método para verificar se é admin (exemplo, ajuste conforme necessário)
    def is_admin(self):
        return self.perfil and self.perfil.nome == 'Administrador'

class Perfil(db.Model):
    __tablename__ = 'perfil'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    usuarios = db.relationship('Usuario', backref='perfil', lazy=True)

class NaturezaDespesa(db.Model):
    __tablename__ = 'natureza_despesa'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    itens = db.relationship('Item', backref='natureza_despesa', lazy=True)

    def __repr__(self):
        return f"<NaturezaDespesa {self.codigo} - {self.nome}>"

class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    valor_unitario = db.Column(db.Float, default=0)
    estoque_atual = db.Column(db.Float, default=0)
    estoque_minimo = db.Column(db.Float, default=0)
    natureza_despesa_id = db.Column(db.Integer, db.ForeignKey('natureza_despesa.id'), nullable=False)

    @property
    def valor_total(self):
        return self.estoque_atual * self.valor_unitario

# Carregador de usuário para o Flask-Login (COM TRATAMENTO DE ERRO)
@login_manager.user_loader
def load_user(user_id):
    print(f"Tentando carregar utilizador com ID: {user_id}")
    try:
        if user_id is None or not str(user_id).isdigit():
            print(f"ID de utilizador inválido recebido: {user_id}")
            return None
        user = Usuario.query.get(int(user_id))
        if user:
            print(f"Utilizador {user_id} carregado com sucesso.")
        else:
            print(f"Utilizador com ID {user_id} não encontrado na base de dados.")
        return user
    except OperationalError as e:
        print(f"ERRO OPERACIONAL de base de dados ao carregar utilizador {user_id}: {e}")
        return None
    except Exception as e:
        print(f"ERRO INESPERADO ao carregar utilizador {user_id}: {e}")
        return None

# Filtro para formatação de data
def datetimeformat(value, format='%d/%m/%Y'):
    if value == "now":
        value = datetime.datetime.now()
    return value.strftime(format) if value else ""

# Criar blueprint 'main'
main = Blueprint('main', __name__)

# Rotas do blueprint 'main' (Copiadas do seu ficheiro)
@main.route('/')
def index():
    if current_user.is_authenticated:
        # Certifique-se que 'index_logged_in.html' existe
        return render_template('index_logged_in.html')
    # Certifique-se que 'index_simple.html' existe
    return render_template('index_simple.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.senha == senha: # Simplificado - Use hashing na vida real!
            login_user(usuario)
            return redirect(url_for('main.index'))
        else:
            flash('Email ou senha inválidos', 'danger')
    # Certifique-se que 'login_simple.html' existe
    return render_template('login_simple.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# ... (Outras rotas do blueprint 'main' para Naturezas e Itens - copiadas do seu ficheiro) ...
# Rotas para Naturezas de Despesa
@main.route('/naturezas-despesa')
@login_required
def listar_naturezas_despesa():
    naturezas = NaturezaDespesa.query.all()
    return render_template('naturezas_despesa/list.html', naturezas=naturezas)

# ... (nova_natureza_despesa, editar_natureza_despesa, etc.) ...

# Rotas para Itens
@main.route('/itens')
@login_required
def listar_itens():
    itens = Item.query.all()
    return render_template('itens/list.html', itens=itens)

# ... (novo_item, editar_item, etc.) ...

# Função para criar e configurar a aplicação Flask
def create_app():
    app = Flask(__name__)
    # Carregar configurações (do ambiente ou de um ficheiro config.py)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("DATABASE_URL não definida no ambiente!")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensões com a app
    db.init_app(app)
    login_manager.init_app(app)

    # Registrar blueprint 'main'
    app.register_blueprint(main)

    # --- IMPORTAR E REGISTRAR O BLUEPRINT 'movimentos' --- 
    try:
        # Assumindo que routes_movimentos.py está na mesma pasta ou pacote
        from .routes_movimentos import movimentos_bp
        app.register_blueprint(movimentos_bp)
        print("Blueprint 'movimentos_bp' registrado com sucesso.")
    except ImportError as e:
        print(f"ERRO ao importar/registrar 'movimentos_bp': {e}")
    # --- FIM DO REGISTRO DE MOVIMENTOS --- 

    # --- Registre outros blueprints aqui se existirem (ex: requisicoes, relatorios) ---
    # from .routes_requisicoes import requisicoes_bp
    # app.register_blueprint(requisicoes_bp)
    # from .routes_relatorios import relatorios_bp
    # app.register_blueprint(relatorios_bp)
    # --- FIM DE OUTROS BLUEPRINTS ---

    # Registrar filtro Jinja
    app.jinja_env.filters['datetimeformat'] = datetimeformat

    # Criar tabelas e dados iniciais (Cuidado com create_all() em produção)
    with app.app_context():
        print("Criando tabelas (se não existirem)...")
        db.create_all()
        print("Tabelas verificadas/criadas.")
        # ... (Seu código para adicionar perfis e usuário admin padrão) ...
        if Perfil.query.count() == 0:
            print("Criando perfis padrão...")
            admin = Perfil(nome="Administrador")
            solicitante = Perfil(nome="Solicitante")
            db.session.add_all([admin, solicitante])
            db.session.flush() # Garante que os IDs são gerados antes de usar
            print("Perfis criados.")
            
            # Criar usuário admin padrão
            if not Usuario.query.filter_by(email="admin@example.com").first():
                print("Criando usuário admin padrão...")
                # Use hashing de senha na vida real!
                admin_user = Usuario(
                    nome="Administrador",
                    email="admin@example.com",
                    senha="admin123", # NÃO FAÇA ISTO EM PRODUÇÃO!
                    perfil_id=admin.id
                )
                db.session.add(admin_user)
                print("Usuário admin criado.")
            db.session.commit()
            print("Commit inicial de dados feito.")
        else:
            print("Perfis já existem, não foram criados.")

    print("Função create_app concluída.")
    return app

# Criar a instância da aplicação para o Gunicorn usar
# O comando no Render deve ser 'gunicorn app_render:app'
print("Chamando create_app() para criar a instância 'app'...")
app = create_app()
print("Instância 'app' criada.")

# O bloco if __name__ == '__main__': é para execução local, não usado pelo Gunicorn
if __name__ == '__main__':
    print("Executando localmente com app.run()...")
    # Use host='0.0.0.0' para ser acessível na rede local, se necessário
    app.run(debug=True, host='0.0.0.0', port=5000) 

