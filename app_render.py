from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os

# Configuração
app = Flask(__name__)
# Adicione este código após a linha "app = Flask(__name__)"
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y'):
    if value == "now":
        value = datetime.datetime.now()
    return value.strftime(format) if value else ""

# Não esqueça de adicionar o import no topo do arquivo
import datetime
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-secreta-temporaria')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensões
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
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

# Página inicial simplificada
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index_logged_in.html')
    return render_template('index.html')

# Rota de login simplificada
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.senha == senha:
            login_user(usuario)
            return redirect(url_for('index'))
        flash('Email ou senha inválidos', 'danger')
    return render_template('login.html')

# Rota de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Carregador de usuário para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Rota de teste
@app.route('/hello')
def hello():
    return "Olá, Mundo! Configuração básica do Flask funcionando."

if __name__ == '__main__':
    app.run(debug=True)
