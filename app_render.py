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

# Modelos
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

# Modelo para Natureza de Despesa
class NaturezaDespesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    itens = db.relationship('Item', backref='natureza_despesa', lazy=True)
    
    def __repr__(self):
        return f"<NaturezaDespesa {self.codigo} - {self.nome}>"

# Modelo para Item (atualizado com campo de valor)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    valor_unitario = db.Column(db.Float, default=0)  # Campo para valor unitário
    estoque_atual = db.Column(db.Float, default=0)
    estoque_minimo = db.Column(db.Float, default=0)
    natureza_despesa_id = db.Column(db.Integer, db.ForeignKey('natureza_despesa.id'), nullable=False)
    
    @property
    def valor_total(self):
        """Calcula o valor total do item (quantidade x valor unitário)"""
        return self.estoque_atual * self.valor_unitario

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

# Rotas do blueprint - Páginas básicas
@main.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index_logged_in.html')
    return render_template('index_simple.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Verificar se o usuário existe
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Simplificar a verificação de senha
            if usuario.senha == senha:
                login_user(usuario)
                
                # Redirecionar para a página inicial após o login
                return redirect(url_for('main.index'))
            else:
                flash('Senha incorreta', 'danger')
        else:
            flash('Email não encontrado', 'danger')
            
        flash('Email ou senha inválidos', 'danger')
    
    return render_template('login_simple.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# Rotas para Naturezas de Despesa
@main.route('/naturezas-despesa')
@login_required
def listar_naturezas_despesa():
    naturezas = NaturezaDespesa.query.all()
    return render_template('naturezas_despesa/list.html', naturezas=naturezas)

@main.route('/naturezas-despesa/nova', methods=['GET', 'POST'])
@login_required
def nova_natureza_despesa():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        
        # Validar dados
        if not codigo or not nome:
            flash('Todos os campos são obrigatórios', 'danger')
            return render_template('naturezas_despesa/form.html')
        
        # Verificar se já existe uma ND com o mesmo código
        if NaturezaDespesa.query.filter_by(codigo=codigo).first():
            flash('Já existe uma Natureza de Despesa com este código', 'danger')
            return render_template('naturezas_despesa/form.html')
        
        # Criar nova ND
        nova_nd = NaturezaDespesa(codigo=codigo, nome=nome)
        db.session.add(nova_nd)
        db.session.commit()
        
        flash('Natureza de Despesa criada com sucesso', 'success')
        return redirect(url_for('main.listar_naturezas_despesa'))
    
    return render_template('naturezas_despesa/form.html')

@main.route('/naturezas-despesa/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_natureza_despesa(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        
        # Validar dados
        if not codigo or not nome:
            flash('Todos os campos são obrigatórios', 'danger')
            return render_template('naturezas_despesa/form.html', nd=nd)
        
        # Verificar se já existe outra ND com o mesmo código
        nd_existente = NaturezaDespesa.query.filter_by(codigo=codigo).first()
        if nd_existente and nd_existente.id != id:
            flash('Já existe outra Natureza de Despesa com este código', 'danger')
            return render_template('naturezas_despesa/form.html', nd=nd)
        
        # Atualizar ND
        nd.codigo = codigo
        nd.nome = nome
        db.session.commit()
        
        flash('Natureza de Despesa atualizada com sucesso', 'success')
        return redirect(url_for('main.listar_naturezas_despesa'))
    
    return render_template('naturezas_despesa/form.html', nd=nd)

@main.route('/naturezas-despesa/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_natureza_despesa(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    
    # Verificar se há itens vinculados a esta ND
    if nd.itens:
        flash('Não é possível excluir esta Natureza de Despesa pois existem itens vinculados a ela', 'danger')
        return redirect(url_for('main.listar_naturezas_despesa'))
    
    db.session.delete(nd)
    db.session.commit()
    
    flash('Natureza de Despesa excluída com sucesso', 'success')
    return redirect(url_for('main.listar_naturezas_despesa'))

@main.route('/naturezas-despesa/saldo')
@login_required
def saldo_naturezas_despesa():
    naturezas = NaturezaDespesa.query.all()
    
    # Calcular saldo para cada natureza de despesa
    saldos = []
    for nd in naturezas:
        itens = Item.query.filter_by(natureza_despesa_id=nd.id).all()
        total_itens = len(itens)
        valor_total = sum(item.valor_total for item in itens)
        
        saldos.append({
            'natureza': nd,
            'total_itens': total_itens,
            'valor_total': valor_total
        })
    
    return render_template('naturezas_despesa/saldo.html', saldos=saldos)

# Rotas para Itens
@main.route('/itens')
@login_required
def listar_itens():
    itens = Item.query.all()
    return render_template('itens/list.html', itens=itens)

@main.route('/itens/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    naturezas = NaturezaDespesa.query.all()
    
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')
        unidade = request.form.get('unidade')
        estoque_minimo = request.form.get('estoque_minimo')
        valor_unitario = request.form.get('valor_unitario')
        natureza_despesa_id = request.form.get('natureza_despesa_id')
        
        # Validar dados
        if not codigo or not descricao or not unidade or not natureza_despesa_id:
            flash('Todos os campos obrigatórios devem ser preenchidos', 'danger')
            return render_template('itens/form.html', naturezas=naturezas)
        
        # Verificar se já existe um item com o mesmo código
        if Item.query.filter_by(codigo=codigo).first():
            flash('Já existe um Item com este código', 'danger')
            return render_template('itens/form.html', naturezas=naturezas)
        
        # Converter estoque_minimo para float
        try:
            estoque_minimo = float(estoque_minimo) if estoque_minimo else 0
        except ValueError:
            flash('Estoque mínimo deve ser um número válido', 'danger')
            return render_template('itens/form.html', naturezas=naturezas)
            
        # Converter valor_unitario para float
        try:
            valor_unitario = float(valor_unitario) if valor_unitario else 0
        except ValueError:
            flash('Valor unitário deve ser um número válido', 'danger')
            return render_template('itens/form.html', naturezas=naturezas)
        
        # Criar novo item
        novo_item = Item(
            codigo=codigo,
            descricao=descricao,
            unidade=unidade,
            valor_unitario=valor_unitario,
            estoque_minimo=estoque_minimo,
            estoque_atual=0,  # Inicia com estoque zero
            natureza_despesa_id=natureza_despesa_id
        )
        db.session.add(novo_item)
        db.session.commit()
        
        flash('Item criado com sucesso', 'success')
        return redirect(url_for('main.listar_itens'))
    
    return render_template('itens/form.html', naturezas=naturezas)

@main.route('/itens/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)
    naturezas = NaturezaDespesa.query.all()
    
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')
        unidade = request.form.get('unidade')
        estoque_minimo = request.form.get('estoque_minimo')
        valor_unitario = request.form.get('valor_unitario')
        natureza_despesa_id = request.form.get('natureza_despesa_id')
        
        # Validar dados
        if not codigo or not descricao or not unidade or not natureza_despesa_id:
            flash('Todos os campos obrigatórios devem ser preenchidos', 'danger')
            return render_template('itens/form.html', item=item, naturezas=naturezas)
        
        # Verificar se já existe outro item com o mesmo código
        item_existente = Item.query.filter_by(codigo=codigo).first()
        if item_existente and item_existente.id != id:
            flash('Já existe outro Item com este código', 'danger')
            return render_template('itens/form.html', item=item, naturezas=naturezas)
        
        # Converter estoque_minimo para float
        try:
            estoque_minimo = float(estoque_minimo) if estoque_minimo else 0
        except ValueError:
            flash('Estoque mínimo deve ser um número válido', 'danger')
            return render_template('itens/form.html', item=item, naturezas=naturezas)
            
        # Converter valor_unitario para float
        try:
            valor_unitario = float(valor_unitario) if valor_unitario else 0
        except ValueError:
            flash('Valor unitário deve ser um número válido', 'danger')
            return render_template('itens/form.html', item=item, naturezas=naturezas)
        
        # Atualizar item
        item.codigo = codigo
        item.descricao = descricao
        item.unidade = unidade
        item.estoque_minimo = estoque_minimo
        item.valor_unitario = valor_unitario
        item.natureza_despesa_id = natureza_despesa_id
        db.session.commit()
        
        flash('Item atualizado com sucesso', 'success')
        return redirect(url_for('main.listar_itens'))
    
    return render_template('itens/form.html', item=item, naturezas=naturezas)

@main.route('/itens/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    
    # Verificar se há movimentações vinculadas a este item
    # (Esta verificação será implementada na Fase 3, quando criarmos o modelo de Movimentação)
    
    db.session.delete(item)
    db.session.commit()
    
    flash('Item excluído com sucesso', 'success')
    return redirect(url_for('main.listar_itens'))

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
    
    # Inicializar banco de dados e realizar migração
    with app.app_context():
        db.create_all()
        
        # Verificar se a coluna valor_unitario já existe na tabela item
        inspector = db.inspect(db.engine)
        colunas_existentes = [coluna['name'] for coluna in inspector.get_columns('item')]
        
        if 'valor_unitario' not in colunas_existentes:
            # Adicionar a coluna valor_unitario à tabela item
            db.session.execute(db.text("ALTER TABLE item ADD COLUMN valor_unitario FLOAT DEFAULT 0"))
            db.session.commit()
            print("Coluna valor_unitario adicionada com sucesso à tabela item")
        
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
