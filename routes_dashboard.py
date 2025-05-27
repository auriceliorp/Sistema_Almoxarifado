from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_, extract
from datetime import datetime, timedelta
from extensoes import db
from models import (
    EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial,
    NaturezaDespesa, Item, Fornecedor, PainelContratacao, Grupo,
    BemPatrimonial, Local, TipoBem, MovimentacaoBem,
    Publicacao, TipoPublicacao, Usuario, UnidadeLocal
)

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

def get_safe_query_result(query_func):
    """Executa uma query com tratamento de erro seguro"""
    try:
        return query_func()
    except Exception as e:
        current_app.logger.error(f"Erro na query: {str(e)}")
        return None

@dashboard_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    try:
        # Inicializa variáveis com valores padrão
        dados_entrada = []
        grafico_grupo_labels = []
        grafico_grupo_dados = []
        
        # ---------------- INDICADORES GERAIS E NATUREZA DE DESPESA ----------------
        total_itens = db.session.query(func.count(Item.id)).scalar() or 0
        total_fornecedores = db.session.query(func.count(Fornecedor.id)).scalar() or 0
        total_entradas = db.session.query(func.count(EntradaMaterial.id)).scalar() or 0
        total_saidas = db.session.query(func.count(SaidaMaterial.id)).scalar() or 0
        
        subquery_saidas = (
            db.session.query(
                Item.natureza_despesa_id.label('nd_id'),
                func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario).label('total_saida')
            )
            .join(SaidaItem, SaidaItem.item_id == Item.id)
            .group_by(Item.natureza_despesa_id)
            .subquery()
        )

        resultados = (
            db.session.query(
                NaturezaDespesa.codigo,
                NaturezaDespesa.nome,
                func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0).label('entradas'),
                func.coalesce(subquery_saidas.c.total_saida, 0).label('saidas')
            )
            .outerjoin(Item, Item.natureza_despesa_id == NaturezaDespesa.id)
            .outerjoin(EntradaItem, EntradaItem.item_id == Item.id)
            .outerjoin(subquery_saidas, subquery_saidas.c.nd_id == NaturezaDespesa.id)
            .group_by(NaturezaDespesa.codigo, NaturezaDespesa.nome, subquery_saidas.c.total_saida)
            .all()
        )

        dados_entrada = [
            {
                'codigo': row.codigo,
                'nome': row.nome,
                'entradas': float(row.entradas),
                'saidas': float(row.saidas)
            }
            for row in resultados
        ]

        # Gráfico de grupos
        grupo_data = (
            db.session.query(
                Grupo.nome,
                func.count(Item.id).label('quantidade')
            )
            .join(Item)
            .group_by(Grupo.nome)
            .all()
        )

        grafico_grupo_labels = [g.nome for g in grupo_data]
        grafico_grupo_dados = [int(g.quantidade) for g in grupo_data]

        # ---------------- ABA ALMOXARIFADO ----------------
        total_grupos = db.session.query(func.count(Grupo.id)).scalar() or 0
        valor_total_estoque = db.session.query(
            func.sum(Item.estoque_atual * Item.valor_unitario)
        ).scalar() or 0
        total_itens_com_valor = db.session.query(func.count(Item.id))\
            .filter(Item.valor_unitario > 0)\
            .scalar() or 0

        itens_abaixo_minimo = Item.query\
            .filter(Item.estoque_atual < Item.estoque_minimo)\
            .order_by((Item.estoque_atual / Item.estoque_minimo).asc())\
            .all()

        total_itens_criticos = len(itens_abaixo_minimo)

        data_limite = datetime.now() - timedelta(days=30)
        total_movimentacoes = db.session.query(
            func.count(EntradaMaterial.id) + func.count(SaidaMaterial.id)
        ).filter(
            or_(
                EntradaMaterial.data_entrada >= data_limite,
                SaidaMaterial.data_movimento >= data_limite
            )
        ).scalar() or 0

        # Itens mais movimentados
        itens_movimentados = []
        itens_query = Item.query.limit(10).all()
        
        for item in itens_query:
            entradas = db.session.query(func.sum(EntradaItem.quantidade))\
                .join(EntradaMaterial)\
                .filter(
                    EntradaItem.item_id == item.id,
                    EntradaMaterial.data_entrada >= data_limite
                ).scalar() or 0

            saidas = db.session.query(func.sum(SaidaItem.quantidade))\
                .join(SaidaMaterial)\
                .filter(
                    SaidaItem.item_id == item.id,
                    SaidaMaterial.data_movimento >= data_limite
                ).scalar() or 0

            valor_movimentado = (entradas + saidas) * (item.valor_unitario or 0)

            item.total_entradas = entradas
            item.total_saidas = saidas
            item.valor_movimentado = valor_movimentado

            if entradas > 0 or saidas > 0:
                itens_movimentados.append(item)

        itens_movimentados.sort(key=lambda x: x.total_entradas + x.total_saidas, reverse=True)

        grupos_data = db.session.query(
            Grupo.nome,
            func.count(Item.id).label('total')
        ).join(Item)\
        .group_by(Grupo.id, Grupo.nome)\
        .order_by(func.count(Item.id).desc())\
        .all()

        labels_grupos = [g.nome for g in grupos_data]
        valores_grupos = [int(g.total) for g in grupos_data]

        # ---------------- ABA PATRIMÔNIO ----------------
        total_bens_ativos = db.session.query(func.count(BemPatrimonial.id))\
            .filter(BemPatrimonial.situacao == 'Em uso')\
            .scalar() or 0

        total_locais = db.session.query(func.count(Local.id)).scalar() or 0
        valor_total_bens = db.session.query(func.sum(BemPatrimonial.valor_aquisicao))\
            .filter(BemPatrimonial.valor_aquisicao.isnot(None))\
            .scalar() or 0

        total_bens_com_valor = db.session.query(func.count(BemPatrimonial.id))\
            .filter(BemPatrimonial.valor_aquisicao.isnot(None))\
            .scalar() or 0

        total_pendentes_inventario = db.session.query(func.count(BemPatrimonial.id))\
            .filter(BemPatrimonial.situacao == 'Inventariar')\
            .scalar() or 0

        total_bens = db.session.query(func.count(BemPatrimonial.id)).scalar() or 1
        percentual_inventariado = round(((total_bens - total_pendentes_inventario) / total_bens) * 100)

        total_em_manutencao = db.session.query(func.count(BemPatrimonial.id))\
            .filter(BemPatrimonial.situacao == 'Manutenção')\
            .scalar() or 0

        data_inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_manutencoes_mes = db.session.query(func.count(MovimentacaoBem.id))\
            .filter(
                MovimentacaoBem.tipo_movimentacao == 'Manutenção',
                MovimentacaoBem.data_movimentacao >= data_inicio_mes
            ).scalar() or 0

        total_para_alienar = db.session.query(func.count(BemPatrimonial.id))\
            .filter(BemPatrimonial.situacao == 'Alienar')\
            .scalar() or 0

        data_inicio_ano = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        total_alienados_ano = db.session.query(func.count(MovimentacaoBem.id))\
            .filter(
                MovimentacaoBem.tipo_movimentacao == 'Alienação',
                MovimentacaoBem.data_movimentacao >= data_inicio_ano
            ).scalar() or 0

        locais_data = db.session.query(
            Local.descricao.label('nome'),
            func.count(BemPatrimonial.id).label('total')
        ).join(BemPatrimonial)\
        .group_by(Local.id, Local.descricao)\
        .order_by(func.count(BemPatrimonial.id).desc())\
        .all()

        labels_locais = [l.nome for l in locais_data]
        valores_locais = [int(l.total) for l in locais_data]

        tipos_data = db.session.query(
            TipoBem.descricao.label('nome'),
            func.count(BemPatrimonial.id).label('total')
        ).join(BemPatrimonial)\
        .group_by(TipoBem.id, TipoBem.descricao)\
        .order_by(func.count(BemPatrimonial.id).desc())\
        .all()

        labels_tipos = [t.nome for t in tipos_data]
        valores_tipos = [int(t.total) for t in tipos_data]

        data_limite = datetime.now() - timedelta(days=30)
        ultimos_bens = BemPatrimonial.query\
            .filter(BemPatrimonial.data_cadastro >= data_limite)\
            .order_by(BemPatrimonial.data_cadastro.desc())\
            .all()

        # ---------------- ABA PUBLICAÇÕES ----------------
        total_publicacoes = db.session.query(func.count(Publicacao.id))\
            .filter(Publicacao.excluido == False)\
            .scalar() or 0

        # Contagem por tipo
        tipos_data = db.session.query(
            TipoPublicacao.nome.label('nome'),
            func.count(Publicacao.id).label('total')
        ).join(Publicacao)\
        .filter(Publicacao.excluido == False)\
        .group_by(TipoPublicacao.id, TipoPublicacao.nome)\
        .order_by(func.count(Publicacao.id).desc())\
        .all()

        labels_tipos = [t.nome for t in tipos_data]
        valores_tipos = [int(t.total) for t in tipos_data]

        data_inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_publicacoes_mes = db.session.query(func.count(Publicacao.id))\
            .filter(
                Publicacao.excluido == False,
                Publicacao.data_assinatura >= data_inicio_mes
            ).scalar() or 0

        percentual_mes = round((total_publicacoes_mes / total_publicacoes * 100) if total_publicacoes > 0 else 0)

        # Publicações pendentes (considerando data de vigência)
        data_atual = datetime.now().date()
        total_pendentes = db.session.query(func.count(Publicacao.id))\
            .filter(
                Publicacao.excluido == False,
                Publicacao.vigencia_inicio > data_atual
            ).scalar() or 0

        # Média de dias entre assinatura e início da vigência
        media_dias = db.session.query(
            func.avg(Publicacao.vigencia_inicio - Publicacao.data_assinatura)
        ).filter(
            Publicacao.excluido == False,
            Publicacao.vigencia_inicio.isnot(None),
            Publicacao.data_assinatura.isnot(None)
        ).scalar()
        
        media_dias_publicacao = round(media_dias.days if media_dias else 0)

        # Publicações urgentes (próximos 2 dias)
        data_limite = datetime.now().date() + timedelta(days=2)
        total_urgentes = db.session.query(func.count(Publicacao.id))\
            .filter(
                Publicacao.excluido == False,
                Publicacao.vigencia_inicio <= data_limite,
                Publicacao.vigencia_inicio > data_atual
            ).scalar() or 0

        # Evolução mensal
        meses_data = []
        for i in range(5, -1, -1):
            data = datetime.now() - timedelta(days=i*30)
            total = db.session.query(func.count(Publicacao.id))\
                .filter(
                    Publicacao.excluido == False,
                    extract('month', Publicacao.data_assinatura) == data.month,
                    extract('year', Publicacao.data_assinatura) == data.year
                ).scalar() or 0
            meses_data.append({
                'mes': data.strftime('%b/%Y'),
                'total': total
            })

        labels_meses = [m['mes'] for m in meses_data]
        valores_meses = [m['total'] for m in meses_data]

        # Publicações recentes
        data_limite = datetime.now() - timedelta(days=30)
        publicacoes_recentes = Publicacao.query\
            .filter(
                Publicacao.excluido == False,
                Publicacao.data_assinatura >= data_limite
            )\
            .order_by(Publicacao.data_assinatura.desc())\
            .all()

        # ---------------- ABA COMPRAS ----------------
        total_processos = db.session.query(func.count(PainelContratacao.id))\
            .filter(PainelContratacao.excluido == False)\
            .scalar() or 0

        total_estimado = db.session.query(func.sum(PainelContratacao.valor_estimado))\
            .filter(PainelContratacao.excluido == False)\
            .scalar() or 0

        total_com_sei = db.session.query(func.count(PainelContratacao.id))\
            .filter(
                PainelContratacao.excluido == False,
                PainelContratacao.numero_sei.isnot(None),
                PainelContratacao.numero_sei != ''
            ).scalar() or 0

        total_concluidos = db.session.query(func.count(PainelContratacao.id))\
            .filter(
                PainelContratacao.excluido == False,
                or_(
                    PainelContratacao.status == 'Concluído',
                    PainelContratacao.status == 'Concluido'
                )
            ).scalar() or 0

        modalidades = db.session.query(
            func.coalesce(PainelContratacao.modalidade, 'Não Informada').label('modalidade'),
            func.count(PainelContratacao.id).label('total')
        ).filter(
            PainelContratacao.excluido == False
        ).group_by(
            PainelContratacao.modalidade
        ).order_by(
            func.count(PainelContratacao.id).desc()
        ).all()

        labels_modalidades = [m.modalidade for m in modalidades]
        valores_modalidades = [int(m.total) for m in modalidades]

        ultimos_processos = PainelContratacao.query\
            .filter(PainelContratacao.excluido == False)\
            .order_by(PainelContratacao.data_abertura.desc())\
            .limit(5).all()

        # ---------------- EVOLUÇÃO DE MOVIMENTAÇÕES ----------------
        data_inicio = datetime.now() - timedelta(days=180)
        meses_data = []
        valores_entradas_meses = []
        valores_saidas_meses = []
        labels_meses = []

        for i in range(5, -1, -1):
            data = datetime.now() - timedelta(days=i*30)
            mes_ano = data.strftime('%b/%Y')
            labels_meses.append(mes_ano)

            total_entradas = db.session.query(func.count(EntradaMaterial.id))\
                .filter(
                    extract('month', EntradaMaterial.data_entrada) == data.month,
                    extract('year', EntradaMaterial.data_entrada) == data.year
                ).scalar() or 0
            valores_entradas_meses.append(total_entradas)

            total_saidas = db.session.query(func.count(SaidaMaterial.id))\
                .filter(
                    extract('month', SaidaMaterial.data_movimento) == data.month,
                    extract('year', SaidaMaterial.data_movimento) == data.year
                ).scalar() or 0
            valores_saidas_meses.append(total_saidas)

        return render_template(
            'dashboard.html',
            usuario=current_user,
            dados_entrada=dados_entrada,
            grafico_grupo_labels=grafico_grupo_labels,
            grafico_grupo_dados=grafico_grupo_dados,
            total_itens=total_itens,
            total_grupos=total_grupos,
            valor_total_estoque=float(valor_total_estoque or 0),
            total_itens_com_valor=total_itens_com_valor,
            total_itens_criticos=total_itens_criticos,
            total_movimentacoes=total_movimentacoes,
            itens_abaixo_minimo=itens_abaixo_minimo,
            itens_movimentados=itens_movimentados,
            labels_grupos=labels_grupos,
            valores_grupos=valores_grupos,
            total_bens_ativos=total_bens_ativos,
            total_locais=total_locais,
            valor_total_bens=valor_total_bens,
            total_bens_com_valor=total_bens_com_valor,
            total_pendentes_inventario=total_pendentes_inventario,
            percentual_inventariado=percentual_inventariado,
            total_em_manutencao=total_em_manutencao,
            total_manutencoes_mes=total_manutencoes_mes,
            total_para_alienar=total_para_alienar,
            total_alienados_ano=total_alienados_ano,
            labels_locais=labels_locais,
            valores_locais=valores_locais,
            labels_tipos=labels_tipos,
            valores_tipos=valores_tipos,
            ultimos_bens=ultimos_bens,
            total_publicacoes=total_publicacoes,
            total_tipos=total_tipos,
            total_publicacoes_mes=total_publicacoes_mes,
            percentual_mes=percentual_mes,
            total_pendentes=total_pendentes,
            media_dias_publicacao=media_dias_publicacao,
            total_urgentes=total_urgentes,
            labels_meses=labels_meses,
            valores_meses=valores_meses,
            publicacoes_recentes=publicacoes_recentes,
            total_fornecedores=total_fornecedores,
            total_entradas=total_entradas,
            total_saidas=total_saidas,
            total_processos=total_processos,
            total_estimado=total_estimado,
            total_com_sei=total_com_sei,
            total_concluidos=total_concluidos,
            labels_modalidades=labels_modalidades,
            valores_modalidades=valores_modalidades,
            ultimos_processos=ultimos_processos,
            valores_entradas_meses=valores_entradas_meses,
            valores_saidas_meses=valores_saidas_meses
        )

    except Exception as e:
        current_app.logger.error(f"Erro no dashboard: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
        return render_template(
            'dashboard.html',
            usuario=current_user,
            error=True,
            dados_entrada=[],
            grafico_grupo_labels=[],
            grafico_grupo_dados=[],
            total_itens=0,
            total_fornecedores=0,
            total_entradas=0,
            total_saidas=0,
            valor_total_estoque=0.0,
            # ... valores padrão para todas as variáveis
        ) 
