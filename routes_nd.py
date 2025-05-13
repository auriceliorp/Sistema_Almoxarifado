from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from extensoes import db
from models import NaturezaDespesa

nd_bp = Blueprint('nd_bp', __name__, url_prefix='/nd')

# -------------------------- LISTA ND (retorno HTML parcial) -------------------------- #
@nd_bp.route('/')
@login_required
def lista_nd():
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template('lista_nd.html', nds=nds)

# -------------------------- NOVA ND -------------------------- #
@nd_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def nova_nd():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')

        if not codigo or not nome:
            return jsonify({'erro': 'Preencha todos os campos obrigatórios.'}), 400

        nova = NaturezaDespesa(codigo=codigo, nome=nome)
        db.session.add(nova)
        db.session.commit()
        return jsonify({'mensagem': 'ND criada com sucesso'}), 201

    return render_template('form_nd.html', nd=None)

# -------------------------- EDITAR ND -------------------------- #
@nd_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)

    if request.method == 'POST':
        nd.codigo = request.form.get('codigo')
        nd.nome = request.form.get('nome')

        if not nd.codigo or not nd.nome:
            return jsonify({'erro': 'Preencha todos os campos obrigatórios.'}), 400

        db.session.commit()
        return jsonify({'mensagem': 'ND atualizada com sucesso'}), 200

    return render_template('form_nd.html', nd=nd)

# -------------------------- EXCLUIR ND -------------------------- #
@nd_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    db.session.delete(nd)
    db.session.commit()
    return jsonify({'mensagem': 'ND excluída com sucesso'}), 200
