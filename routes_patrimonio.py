# routes_patrimonio.py
# Rotas para gerenciamento de bens patrimoniais com upload e redimensionamento de imagem

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensoes import db
from models import BemPatrimonial, Usuario, GrupoPatrimonio, UnidadeLocal
from PIL import Image
import os

# Criação do blueprint para o módulo de patrimônio
patrimonio_bp = Blueprint('patrimonio_bp', __name__, url_prefix='/patrimonio')

# Caminho da pasta onde as fotos serão salvas (usando caminho absoluto para segurança)
UPLOAD_FOLDER = os.path.join('static', 'fotos_bens')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Cria a pasta de upload caso ela não exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Função auxiliar para validar extensões de arquivo de imagem
def arquivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------ ROTA: LISTAGEM DE BENS ------------------------ #
@patrimonio_bp.route('/bens')
@login_required
def listar_bens():
    numero_ul = request.args.get('numero_ul')
    numero_sap = request.args.get('numero_sap')
    grupo_bem = request.args.get('grupo_bem')
    localizacao = request.args.get('localizacao')

    query = BemPatrimonial.query.filter_by(excluido=False)

    if numero_ul:
        query = query.filter(BemPatrimonial.numero_ul.ilike(f"%{numero_ul}%"))
    if numero_sap:
        query = query.filter(BemPatrimonial.numero_sap.ilike(f"%{numero_sap}%"))
    if grupo_bem:
        query = query.filter(BemPatrimonial.grupo_bem == grupo_bem)
    if localizacao:
        query = query.filter(BemPatrimonial.localizacao == localizacao)

    bens = query.order_by(BemPatrimonial.nome.asc()).all()
    grupos = GrupoPatrimonio.query.order_by(GrupoPatrimonio.codigo).all()
    uls = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()

    return render_template('patrimonio/listar_bens.html', bens=bens, grupos=grupos, uls=uls, usuario=current_user)

# ------------------------ ROTA: CADASTRAR BEM ------------------------ #
@patrimonio_bp.route('/bens/novo', methods=['GET', 'POST'])
@login_required
def novo_bem():
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    grupos = GrupoPatrimonio.query.order_by(GrupoPatrimonio.codigo).all()
    uls = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        numero_ul = request.form.get('numero_ul')
        numero_sap = request.form.get('numero_sap') or None
        numero_siads = request.form.get('numero_siads') or None
        descricao = request.form.get('descricao')
        grupo_bem = request.form.get('grupo_bem') or None
        classificacao_contabil = request.form.get('classificacao_contabil') or None
        detentor_id = request.form.get('detentor_id')
        status = request.form.get('situacao')
        data_aquisicao = request.form.get('data_aquisicao')
        valor_aquisicao = request.form.get('valor_aquisicao') or None
        localizacao = request.form.get('localizacao')
        observacoes = request.form.get('observacoes')

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
                foto_path = os.path.join('static', 'fotos_bens', filename)
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
            localizacao=localizacao,
            foto=foto_path,
            observacoes=observacoes
        )
        db.session.add(bem)
        db.session.commit()
        flash('Bem cadastrado com sucesso!', 'success')
        return redirect(url_for('patrimonio_bp.listar_bens'))

    return render_template('patrimonio/novo_bem.html', usuarios=usuarios, grupos=grupos, uls=uls, usuario=current_user)

# ------------------------ ROTA: EDITAR BEM ------------------------ #
@patrimonio_bp.route('/bens/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_bem(id):
    bem = BemPatrimonial.query.get_or_404(id)
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    grupos = GrupoPatrimonio.query.order_by(GrupoPatrimonio.codigo).all()
    uls = UnidadeLocal.query.order_by(UnidadeLocal.descricao).all()

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
        bem.localizacao = request.form.get('localizacao')
        bem.observacoes = request.form.get('observacoes')

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
                bem.foto = os.path.join('static', 'fotos_bens', filename)
            except Exception as e:
                flash(f'Erro ao processar imagem: {e}', 'danger')
                return redirect(request.url)

        db.session.commit()
        flash('Bem atualizado com sucesso!', 'success')
        return redirect(url_for('patrimonio_bp.listar_bens'))

    return render_template('patrimonio/editar_bem.html', bem=bem, usuarios=usuarios, grupos=grupos, uls=uls, usuario=current_user)

# ------------------------ ROTA: VISUALIZAR BEM ------------------------ #
@patrimonio_bp.route('/bens/visualizar/<int:id>')
@login_required
def visualizar_bem(id):
    bem = BemPatrimonial.query.get_or_404(id)
    return render_template('patrimonio/visualizar_bem.html', bem=bem, usuario=current_user)
