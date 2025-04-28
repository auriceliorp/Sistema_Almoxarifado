from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import db
from models import NaturezaDespesa

nd_bp = Blueprint('nd_bp', __name__, url_prefix='/nd')

# Listar NDs
@nd_bp.route('/')
def lista_nd():
    nds = NaturezaDespesa.query.all()
    return render_template('lista_nd.html', nds=nds)

# Cadastrar nova ND
@nd_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_nd():
    if request.method == 'POST':
        codigo = request.form['codigo']
        descricao = request.form['descricao']

        if NaturezaDespesa.query.filter_by(codigo=codigo).first():
            flash('Este código já existe.', 'danger')
            return redirect(url_for('nd_bp.cadastrar_nd'))

        nova_nd = NaturezaDespesa(codigo=codigo, descricao=descricao)
        db.session.add(nova_nd)
        db.session.commit()

        flash('ND cadastrada com sucesso!', 'success')
        return redirect(url_for('nd_bp.lista_nd'))

    return render_template('cadastrar_nd.html')

# Excluir ND
@nd_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    db.session.delete(nd)
    db.session.commit()
    flash('ND excluída com sucesso!', 'success')
    return redirect(url_for('nd_bp.lista_nd'))
