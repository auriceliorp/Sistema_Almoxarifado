# routes_painel.py
# CRUD para o Painel de Contratações

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from extensoes import db
from models import PainelContratacao

painel_bp = Blueprint('painel_bp', __name__, url_prefix='/painel')

# -------------------- LISTAGEM DE PROCESSOS -------------------- #
@painel_bp.route('/lista')
@login_required
def lista_painel():
    processos = PainelContratacao.query.order_by(PainelContratacao.ano.desc(), PainelContratacao.data_abertura.desc()).all()
    return render_template('painel/lista_painel.html', processos=processos, usuario=current_user)


# -------------------- NOVO PROCESSO -------------------- #
@painel_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_painel():
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            ano = int(request.form.get('ano'))
            data_abertura = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d') if request.form.get('data_abertura') else None
            data_homologacao = datetime.strptime(request.form.get('data_homologacao'), '%Y-%m-%d') if request.form.get('data_homologacao') else None
            periodo_dias = request.form.get('periodo_dias')
            numero_sei = request.form.get('numero_sei')
            modalidade = request.form.get('modalidade')
            registro_precos = request.form.get('registro_precos')
            orgaos_participantes = request.form.get('orgaos_participantes')
            numero_licitacao = request.form.get('numero_licitacao')
            parecer_juridico = request.form.get('parecer_juridico')
            fundamentacao_legal = request.form.get('fundamentacao_legal')
            objeto = request.form.get('objeto')
            natureza_despesa = request.form.get('natureza_despesa')
            valor_estimado = request.form.get('valor_estimado').replace(',', '.')
            valor_homologado = request.form.get('valor_homologado').replace(',', '.')
            percentual_economia = request.form.get('percentual_economia')
            impugnacao = request.form.get('impugnacao')
            recurso = request.form.get('recurso')
            itens_desertos = request.form.get('itens_desertos')
            responsavel_conducao = request.form.get('responsavel_conducao')
            setor_responsavel = request.form.get('setor_responsavel')
            status = request.form.get('status')

            # Criar nova instância
            processo = PainelContratacao(
                ano=ano,
                data_abertura=data_abertura,
                data_homologacao=data_homologacao,
                periodo_dias=int(periodo_dias) if periodo_dias else None,
                numero_sei=numero_sei,
                modalidade=modalidade,
                registro_precos=registro_precos,
                orgaos_participantes=orgaos_participantes,
                numero_licitacao=numero_licitacao,
                parecer_juridico=parecer_juridico,
                fundamentacao_legal=fundamentacao_legal,
                objeto=objeto,
                natureza_despesa=natureza_despesa,
                valor_estimado=float(valor_estimado) if valor_estimado else None,
                valor_homologado=float(valor_homologado) if valor_homologado else None,
                percentual_economia=percentual_economia,
                impugnacao=impugnacao,
                recurso=recurso,
                itens_desertos=itens_desertos,
                responsavel_conducao=responsavel_conducao,
                setor_responsavel=setor_responsavel,
                status=status
            )

            # Salvar no banco
            db.session.add(processo)
            db.session.commit()
            flash('Processo cadastrado com sucesso!', 'success')
            return redirect(url_for('painel_bp.lista_painel'))

        except Exception as e:
            print(f"Erro ao salvar processo: {e}")
            flash('Erro ao salvar processo. Verifique os dados e tente novamente.', 'danger')

    return render_template('painel/novo_painel.html', usuario=current_user)
