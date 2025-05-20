# routes_patrimonio.py
# Rotas para gerenciamento de bens patrimoniais com upload e redimensionamento de imagem

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensoes import db
from models import BemPatrimonial, Usuario, GrupoPatrimonio  # Atualizado para GrupoPatrimonio
from PIL import Image  # Pillow para redimensionar imagem
import os

# Cria o blueprint do módulo de Patrimônio
patrimonio_bp = Blueprint('patrimonio_bp', __name__, url_prefix='/patrimonio')

# Pasta para salvar as fotos dos bens
UPLOAD_FOLDER = 'static/fotos_bens'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Cria a pasta se ela não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Função auxiliar para validar extensão do arquivo
def arquivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------ ROTA: LISTAGEM DE BENS ------------------------ #
@patrimonio_bp.route('/bens')
@login_required
def listar_bens():
    termo = request.args.get('termo')
    query = BemPatrimonial.query.filter_by(excluido=False)

    if termo:
        query = query.filter(
            BemPatrimonial.nome.ilike(f"%{termo}%") |
            BemPatrimonial.numero_ul.ilike(f"%{termo}%") |
            BemPatrimonial.numero_sap.ilike(f"%{termo}%")
        )

    bens = query.order_by(BemPatrimonial.nome.asc()).all()
    return render_template('patrimonio/listar_bens.html', bens=bens, usuario=current_user)

# ------------------------ ROTA: CADASTRAR BEM ------------------------ #
@patrimonio_bp.route('/bens/novo', methods=['GET', 'POST'])
@login_required
def novo_bem():
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    grupos = GrupoPatrimonio.query.order_by(GrupoPatrimonio.codigo).all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        numero_ul = request.form.get('numero_ul')
        numero_sap = request.form.get('numero_sap')
        numero_siads = request.form.get('numero_siads')
        descricao = request.form.get('descricao')
        grupo_bem = request.form.get('grupo_bem')  # agora é string, vindo do select
        classificacao_contabil = request.form.get('classificacao_contabil')
        detentor_id = request.form.get('detentor_id')
        status = request.form.get('situacao')
        data_aquisicao = request.form.get('data_aquisicao')
        valor_aquisicao = request.form.get('valor_aquisicao')
        observacoes = request.form.get('observacoes')

        # Processamento da imagem
        foto = request.files.get('foto')
        foto_path = None
        if foto and foto.filename != '':
            if not arquivo_permitido(foto.filename):
                flash('Formato de imagem não permitido. Use PNG, JPG ou JPEG.', 'danger')
                return redirect(request.url)

            filename = secure_filename(foto.filename)
            foto_path = os.path.join(UPLOAD_FOLDER, filename)

            try:
                img = Image.open(foto)
                img.thumbnail((800, 600))
                img.save(foto_path)
            except Exception as e:
                flash(f'Erro ao processar imagem: {e}', 'danger')
                return redirect(request.url)

        bem = BemPatrimonial(
            nome=nome,
            numero_ul=numero_ul,
            numero_sap=numero_sap,
            numero_siads=numero_siads,
            descricao=descricao,
            grupo_bem=grupo_bem,
            classificacao_contabil=classificacao_contabil,
            detentor_id=detentor_id,
            status=status,
            data_aquisicao=data_aquisicao or None,
            valor_aquisicao=valor_aquisicao or None,
            foto=foto_path
        )
        db.session.add(bem)
        db.session.commit()
        flash('Bem cadastrado com sucesso!', 'success')
        return redirect(url_for('patrimonio_bp.listar_bens'))

    return render_template('patrimonio/novo_bem.html', usuarios=usuarios, grupos=grupos, usuario=current_user)

# ------------------------ ROTA: EDITAR BEM ------------------------ #
@patrimonio_bp.route('/bens/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_bem(id):
    bem = BemPatrimonial.query.get_or_404(id)
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    grupos = GrupoPatrimonio.query.order_by(GrupoPatrimonio.codigo).all()

    if request.method == 'POST':
        bem.nome = request.form.get('nome')
        bem.numero_ul = request.form.get('numero_ul')
        bem.numero_sap = request.form.get('numero_sap')
        bem.numero_siads = request.form.get('numero_siads')
        bem.descricao = request.form.get('descricao')
        bem.grupo_bem = request.form.get('grupo_bem')
        bem.classificacao_contabil = request.form.get('classificacao_contabil')
        bem.detentor_id = request.form.get('detentor_id')
        bem.status = request.form.get('situacao')
        bem.data_aquisicao = request.form.get('data_aquisicao') or None
        bem.valor_aquisicao = request.form.get('valor_aquisicao') or None

        foto = request.files.get('foto')
        if foto and foto.filename != '':
            if not arquivo_permitido(foto.filename):
                flash('Formato de imagem não permitido. Use PNG, JPG ou JPEG.', 'danger')
                return redirect(request.url)

            filename = secure_filename(foto.filename)
            foto_path = os.path.join(UPLOAD_FOLDER, filename)

            try:
                img = Image.open(foto)
                img.thumbnail((800, 600))
                img.save(foto_path)
                bem.foto = foto_path
            except Exception as e:
                flash(f'Erro ao processar imagem: {e}', 'danger')
                return redirect(request.url)

        db.session.commit()
        flash('Bem atualizado com sucesso!', 'success')
        return redirect(url_for('patrimonio_bp.listar_bens'))

    return render_template('patrimonio/editar_bem.html', bem=bem, usuarios=usuarios, grupos=grupos, usuario=current_user)

# ------------------------ ROTA: VISUALIZAR BEM ------------------------ #
@patrimonio_bp.route('/bens/visualizar/<int:id>')
@login_required
def visualizar_bem(id):
    bem = BemPatrimonial.query.get_or_404(id)
    return render_template('patrimonio/visualizar_bem.html', bem=bem, usuario=current_user)
