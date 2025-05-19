# routes_patrimonio.py
# CRUD de bens patrimoniais

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from extensoes import db
from models import Bem, Usuario, Grupo

patrimonio_bp = Blueprint('patrimonio_bp', __name__, url_prefix='/patrimonio')

# -------------------- LISTAR BENS -------------------- #
@patrimonio_bp.route('/bens')
@login_required
def listar_bens():
    termo = request.args.get('termo', '')
    bens = Bem.query

    if termo:
        bens = bens.filter(Bem.nome.ilike(f"%{termo}%"))

    bens = bens.order_by(Bem.nome).all()
    return render_template('patrimonio/listar_bens.html', bens=bens, usuario=current_user)

# -------------------- CADASTRAR BEM -------------------- #
@patrimonio_bp.route('/bens/novo', methods=['GET', 'POST'])
@login_required
def novo_bem():
    grupos = Grupo.query.order_by(Grupo.nome).all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()

    if request.method == 'POST':
        bem = Bem(
            numero_patrimonio_local=request.form['numero_patrimonio_local'],
            numero_patrimonio_sap=request.form['numero_patrimonio_sap'],
            numero_patrimonio_siads=request.form.get('numero_patrimonio_siads'),
            nome=request.form['nome'],
            descricao=request.form.get('descricao'),
            grupo_id=request.form.get('grupo_id'),
            usuario_id=request.form.get('usuario_id') or None
        )

        foto = request.files.get('foto')
        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            caminho_foto = os.path.join('static/fotos_bens', filename)
            foto.save(caminho_foto)
            bem.foto = caminho_foto

        db.session.add(bem)
        db.session.commit()
        flash('Bem cadastrado com sucesso!', 'success')
        return redirect(url_for('patrimonio_bp.listar_bens'))

    return render_template('patrimonio/novo_bem.html', grupos=grupos, usuarios=usuarios, usuario=current_user)

# -------------------- EDITAR BEM -------------------- #
@patrimonio_bp.route('/bens/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_bem(id):
    bem = Bem.query.get_or_404(id)
    grupos = Grupo.query.order_by(Grupo.nome).all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()

    if request.method == 'POST':
        bem.numero_patrimonio_local = request.form['numero_patrimonio_local']
        bem.numero_patrimonio_sap = request.form['numero_patrimonio_sap']
        bem.numero_patrimonio_siads = request.form.get('numero_patrimonio_siads')
        bem.nome = request.form['nome']
        bem.descricao = request.form.get('descricao')
        bem.grupo_id = request.form.get('grupo_id')
        bem.usuario_id = request.form.get('usuario_id') or None

        foto = request.files.get('foto')
        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            caminho_foto = os.path.join('static/fotos_bens', filename)
            foto.save(caminho_foto)
            bem.foto = caminho_foto

        db.session.commit()
        flash('Bem atualizado com sucesso!', 'success')
        return redirect(url_for('patrimonio_bp.listar_bens'))

    return render_template('patrimonio/editar_bem.html', bem=bem, grupos=grupos, usuarios=usuarios, usuario=current_user)

# -------------------- VISUALIZAR BEM -------------------- #
@patrimonio_bp.route('/bens/visualizar/<int:id>')
@login_required
def visualizar_bem(id):
    bem = Bem.query.get_or_404(id)
    return render_template('patrimonio/visualizar_bem.html', bem=bem, usuario=current_user)
