
# app_render.py
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database import db
from models import Usuario, Perfil
from sqlalchemy import text, inspect

# Login Manager
login_manager = LoginManager()
login_manager.login_view = "main.login"

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None and str(user_id).isdigit():
        return Usuario.query.get(int(user_id))
    return None

# Blueprint principal
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for('main.home'))
        else:
            flash('E-mail ou senha inválidos.')
    return render_template('login.html')

@main.route('/home')
@login_required
def home():
    return render_template('home.html', usuario=current_user)

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Blueprints
    app.register_blueprint(main)

    # Outros blueprints (importados com os nomes corretos)
    from routes_nd import nd
    from routes_item import item
    from routes_usuario import usuario
    from routes_estoque import estoque
    from routes_fornecedor import fornecedor
    from routes_area_ul import area_ul

    app.register_blueprint(nd)
    app.register_blueprint(item)
    app.register_blueprint(usuario)
    app.register_blueprint(estoque)
    app.register_blueprint(fornecedor)
    app.register_blueprint(area_ul)

    with app.app_context():
        db.create_all()

        # Criação automática de colunas
        def adicionar_coluna(tabela, coluna_sql):
            try:
                db.session.execute(text(f'ALTER TABLE {tabela} ADD COLUMN {coluna_sql};'))
                db.session.commit()
                print(f"Coluna adicionada: {coluna_sql} em {tabela}")
            except Exception:
                db.session.rollback()

        def coluna_existe(nome_tabela, nome_coluna):
            insp = inspect(db.engine)
            return nome_coluna in [col["name"] for col in insp.get_columns(nome_tabela)]

        # Exemplo: adiciona campos extras, se não existirem
        if not coluna_existe('usuario', 'matricula'):
            adicionar_coluna('usuario', 'matricula VARCHAR(50)')

        # Garante perfil Admin e usuário admin padrão
        perfil_admin = Perfil.query.filter_by(nome='Admin').first()
        if not perfil_admin:
            perfil_admin = Perfil(nome='Admin')
            db.session.add(perfil_admin)
            db.session.commit()

        admin_email = "admin@admin.com"
        if not Usuario.query.filter_by(email=admin_email).first():
            usuario_admin = Usuario(
                nome="Administrador",
                email=admin_email,
                senha=generate_password_hash("admin123"),
                perfil_id=perfil_admin.id,
                matricula="0001"
            )
            db.session.add(usuario_admin)
            db.session.commit()

    return app

# Executável
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    app = create_app()