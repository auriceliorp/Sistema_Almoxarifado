from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import datetime

# Inicializar extensões
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# Modelos simplificados
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'), nullable=False)
    perfil = db.relationship('Perfil', backref=db.backref('usuarios', lazy=True))
    
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)

class Perfil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)

# Carregador de usuário para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Filtro para formatação de data
def datetimeformat(value, format='%d/%m/%Y'):
    if value == "now":
        value = datetime.datetime.now()
    return value.strftime(format) if value else ""

# Criar blueprint
main = Blueprint('main', __name__)

# Rotas do blueprint
@main.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index_simple.html')
    return render_template('index_simple.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Adicionar logs para depuração
        print(f"Tentativa de login: Email={email}")
        
        # Verificar se o usuário existe
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            print(f"Usuário encontrado: {usuario.nome}, Perfil: {usuario.perfil.nome}")
            
            # Simplificar a verificação de senha
            if usuario.senha == senha:
                login_user(usuario)
                print(f"Login bem-sucedido para {usuario.email}")
                
                # Redirecionar para uma página simples após o login
                return render_template('login_success.html', usuario=usuario)
            else:
                print("Senha incorreta")
        else:
            print("Usuário não encontrado")
            
        flash('Email ou senha inválidos', 'danger')
    
    return render_template('login_simple.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/hello')
def hello():
    return "Olá, Mundo! Configuração básica do Flask funcionando."

# Função para criar a aplicação
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-secreta-temporaria')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    # Registrar blueprint
    app.register_blueprint(main)
    
    # Registrar filtro
    app.jinja_env.filters['datetimeformat'] = datetimeformat
    
    # Inicializar banco de dados
    with app.app_context():
        db.create_all()
        
        # Verificar se já existem perfis cadastrados
        if Perfil.query.count() == 0:
            # Criar perfis básicos
            admin = Perfil(nome="Administrador")
            solicitante = Perfil(nome="Solicitante")
            db.session.add(admin)
            db.session.add(solicitante)
            
            # Criar um usuário administrador padrão
            admin_user = Usuario(
                nome="Administrador",
                email="admin@example.com",
                senha="admin123",
                perfil=admin
            )
            db.session.add(admin_user)
            db.session.commit()
    
    return app

# Criar a aplicação
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
