# routes_bem.py
# Rotas para cadastro e listagem de bens patrimoniais

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from extensoes import db
from models import Usuario  # Usado para detentor
from models import BensPatrimoniais  # Será criado depois, temporariamente ignorado

bem_bp = Blueprint('bem_bp', __name__, url_prefix='/bem')

# Pasta de upload de fotos
UPLOAD_FOLDER = 'static/fotos_bens'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------- NOVO BEM -------------------- #
@bem_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_bem():
    usuarios = Usuario.query.order_by(Usuario.nome).all()

    if request.method == 'POST':
        try:
            numero_ul = request.form.get('numero_ul')
            numero_sap = request.form.get('numero_sap')
            numero_siads = request.form.get('numero_siads')
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            grupo_bem = request.form.get('grupo_bem')
            classificacao_contabil = request.form.get('classificacao_contabil')
            localizacao = request.form.get('localizacao')
            data_aquisicao = request.form.get('data_aquisicao')
            valor_aquisicao = request.form.get('valor_aquisicao')
            detentor_id = request.form.get('detentor_id')

            # Processar foto, se houver
            foto = request.files.get('foto')
            foto_path = None
            if foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                foto_path = os.path.join(UPLOAD_FOLDER, filename)
                foto.save(foto_path)

            bem = BensPatrimoniais(
                numero_ul=numero_ul,
                numero_sap=numero_sap,
                numero_siads=numero_siads,
                nome=nome,
                descricao=descricao,
                grupo_bem=grupo_bem,
                classificacao_contabil=classificacao_contabil,
                localizacao=localizacao,
                data_aquisicao=datetime.strptime(data_aquisicao, '%Y-%m-%d') if data_aquisicao else None,
                valor_aquisicao=float(valor_aquisicao.replace(',', '.')) if valor_aquisicao else None,
                foto=foto_path,
                detentor_id=int(detentor_id) if detentor_id else None,
                status='Ativo'
            )

            db.session.add(bem)
            db.session.commit()
            flash('Bem patrimonial cadastrado com sucesso!', 'success')
            return redirect(url_for('bem_bp.lista_bens'))

        except Exception as e:
            print(f"Erro ao salvar bem: {e}")
            flash('Erro ao salvar bem patrimonial.', 'danger')

    return render_template('bem/novo_bem.html', usuarios=usuarios, usuario=current_user)

# -------------------- LISTA DE BENS -------------------- #
@bem_bp.route('/lista')
@login_required
def lista_bens():
    bens = BensPatrimoniais.query.order_by(BensPatrimoniais.nome).all()
    return render_template('bem/lista_bens.html', bens=bens, usuario=current_user)
