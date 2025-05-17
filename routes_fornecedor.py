# routes_fornecedor.py
# Rotas para cadastro e exibição de fornecedores, com filtros e paginação

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Fornecedor
import re

# Criação do blueprint
fornecedor_bp = Blueprint('fornecedor_bp', __name__, url_prefix='/fornecedor')

# -------------------- LISTAR FORNECEDORES COM FILTRO E PAGINAÇÃO -------------------- #
@fornecedor_bp.route('/')
@login_required
def lista_fornecedor():
    page = request.args.get('page', 1, type=int)
    filtro = request.args.get('filtro', 'nome')
    busca = request.args.get('busca', '').strip().lower()

    query = Fornecedor.query

    if busca:
        if filtro == 'nome':
            query = query.filter(Fornecedor.nome.ilike(f'%{busca}%'))
        elif filtro == 'cnpj':
            query = query.filter(Fornecedor.cnpj.ilike(f'%{busca}%'))
        elif filtro == 'cidade':
            query = query.filter(Fornecedor.cidade.ilike(f'%{busca}%'))
        elif filtro == 'uf':
            query = query.filter(Fornecedor.uf.ilike(f'%{busca}%'))

    fornecedores = query.order_by(Fornecedor.nome.asc()).paginate(page=page, per_page=10)

    return render_template('lista_fornecedor.html', fornecedores=fornecedores, filtro=filtro, busca=busca)


# -------------------- CADASTRAR NOVO FORNECEDOR -------------------- #
@fornecedor_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_fornecedor():
    if request.method == 'POST':
        try:
            # Coleta os dados do formulário
            nome = request.form.get('nome', '').strip()
            cnpj = request.form.get('cnpj', '').strip()
            email = request.form.get('email', '').strip()
            telefone = request.form.get('telefone', '').strip()
            celular = request.form.get('celular', '').strip()
            endereco = request.form.get('endereco', '').strip()
            numero = request.form.get('numero', '').strip()
            complemento = request.form.get('complemento', '').strip()
            cep = request.form.get('cep', '').strip()
            cidade = request.form.get('cidade', '').strip()
            uf = request.form.get('uf', '').strip()
            inscricao_estadual = request.form.get('inscricao_estadual', '').strip()
            inscricao_municipal = request.form.get('inscricao_municipal', '').strip()

            # Debug: imprime os dados recebidos
            print("[DEBUG] Dados recebidos para novo fornecedor:")
            print(f"{nome=}, {cnpj=}, {email=}, {telefone=}, {celular=}")
            print(f"{endereco=}, {numero=}, {complemento=}, {cep=}, {cidade=}, {uf=}")
            print(f"{inscricao_estadual=}, {inscricao_municipal=}")

            # Validação dos campos obrigatórios
            if not nome or not cnpj:
                flash('Nome e CNPJ são obrigatórios.', 'danger')
                return redirect(url_for('fornecedor_bp.novo_fornecedor'))

            # Validação simples de CNPJ (formato/tamanho)
            cnpj_limpo = re.sub(r'\D', '', cnpj)
            if len(cnpj_limpo) != 14:
                flash('CNPJ inválido.', 'danger')
                return redirect(url_for('fornecedor_bp.novo_fornecedor'))

            # Cria o fornecedor
            fornecedor = Fornecedor(
                nome=nome,
                cnpj=cnpj,
                email=email,
                telefone=telefone,
                celular=celular,
                endereco=endereco,
                numero=numero,
                complemento=complemento,
                cep=cep,
                cidade=cidade,
                uf=uf,
                inscricao_estadual=inscricao_estadual,
                inscricao_municipal=inscricao_municipal
            )

            db.session.add(fornecedor)
            db.session.commit()
            flash('Fornecedor cadastrado com sucesso!', 'success')
            return redirect(url_for('fornecedor_bp.lista_fornecedor'))

        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar fornecedor.', 'danger')
            print(f'[ERRO AO CADASTRAR FORNECEDOR] {e}')
            return redirect(url_for('fornecedor_bp.novo_fornecedor'))

    return render_template('novo_fornecedor.html')


# -------------------- EDITAR FORNECEDOR -------------------- #
@fornecedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)

    if request.method == 'POST':
        fornecedor.nome = request.form.get('nome', '').strip()
        fornecedor.cnpj = request.form.get('cnpj', '').strip()
        fornecedor.email = request.form.get('email', '').strip()
        fornecedor.telefone = request.form.get('telefone', '').strip()
        fornecedor.celular = request.form.get('celular', '').strip()
        fornecedor.endereco = request.form.get('endereco', '').strip()
        fornecedor.numero = request.form.get('numero', '').strip()
        fornecedor.complemento = request.form.get('complemento', '').strip()
        fornecedor.cep = request.form.get('cep', '').strip()
        fornecedor.cidade = request.form.get('cidade', '').strip()
        fornecedor.uf = request.form.get('uf', '').strip()
        fornecedor.inscricao_estadual = request.form.get('inscricao_estadual', '').strip()
        fornecedor.inscricao_municipal = request.form.get('inscricao_municipal', '').strip()

        db.session.commit()
        flash('Fornecedor atualizado com sucesso!', 'success')
        return redirect(url_for('fornecedor_bp.lista_fornecedor'))

    return render_template('editar_fornecedor.html', fornecedor=fornecedor)


# -------------------- EXCLUIR FORNECEDOR -------------------- #
@fornecedor_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)
    db.session.delete(fornecedor)
    db.session.commit()
    flash('Fornecedor excluído com sucesso!', 'success')
    return redirect(url_for('fornecedor_bp.lista_fornecedor'))