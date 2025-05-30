from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_, extract
from datetime import datetime, timedelta
import traceback
from extensoes import db
from models import (
    EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial,
    NaturezaDespesa, Item, Fornecedor, PainelContratacao, Grupo,
    BemPatrimonial, Local, TipoBem, MovimentacaoBem,
    Publicacao, TipoPublicacao, Usuario, UnidadeLocal
)

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

def get_default_dashboard_values():
    """Retorna um dicionário com valores padrão para o dashboard"""
    return {
        'usuario': current_user,
        'error': True,
        'dados_entrada': [],
        'grafico_grupo_labels': [],
        'grafico_grupo_dados': [],
        'total_itens': 0,
        'total_grupos': 0,
        'valor_total_estoque': 0.0,
        'total_itens_com_valor': 0,
        'total_itens_criticos': 0,
        'total_movimentacoes': 0,
        'itens_abaixo_minimo': [],
        'itens_movimentados': [],
        'labels_grupos': [],
        'valores_grupos': [],
        'total_bens_ativos': 0,
        'total_locais': 0,
        'valor_total_bens': 0.0,
        'total_bens_com_valor': 0,
        'total_pendentes_inventario': 0,
        'percentual_inventariado': 0,
        'total_em_manutencao': 0,
        'total_manutencoes_mes': 0,
        'total_para_alienar': 0,
        'total_alienados_ano': 0,
        'labels_locais': [],
        'valores_locais': [],
        'labels_tipos': [],
        'valores_tipos': [],
        'ultimos_bens': [],
        'total_publicacoes': 0,
        'total_tipos': 0,
        'total_publicacoes_mes': 0,
        'percentual_mes': 0,
        'total_pendentes': 0,
        'media_dias_publicacao': 0,
        'total_urgentes': 0,
        'labels_meses': [],
        'valores_meses': [],
        'publicacoes_recentes': [],
        'total_fornecedores': 0,
        'total_entradas': 0,
        'total_saidas': 0,
        'total_processos': 0,
        'total_estimado': 0.0,
        'total_com_sei': 0,
        'total_concluidos': 0,
        'labels_modalidades': [],
        'valores_modalidades': [],
        'ultimos_processos': [],
        'valores_entradas_meses': [],
        'valores_saidas_meses': []
    }

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
        total_movimentacoes = (
            db.session.query(func.count(EntradaMaterial.id))
            .filter(EntradaMaterial.data_movimento >= data_limite)
            .scalar() or 0
        ) + (
            db.session.query(func.count(SaidaMaterial.id))
            .filter(SaidaMaterial.data_movimento >= data_limite)
            .scalar() or 0
        )

        # Itens mais movimentados
        itens_movimentados = []
        itens_query = Item.query.limit(10).all()
        
        for item in itens_query:
            entradas = db.session.query(func.sum(EntradaItem.quantidade))\
                .join(EntradaMaterial)\
                .filter(
                    EntradaItem.item_id == item.id,
                    EntradaMaterial.data_movimento >= data_limite
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
            .filter(
                BemPatrimonial.situacao == 'Em uso',
                BemPatrimonial.excluido == False
            )\
            .scalar() or 0

        # Contagem de locais únicos baseado na localização dos bens
        total_locais = db.session.query(func.count(db.distinct(BemPatrimonial.localizacao)))\
            .filter(
                BemPatrimonial.excluido == False,
                BemPatrimonial.localizacao.isnot(None)
            )\
            .scalar() or 0

        # Contagem de tipos usando grupo_bem
        total_tipos = db.session.query(func.count(db.distinct(BemPatrimonial.grupo_bem)))\
            .filter(
                BemPatrimonial.excluido == False,
                BemPatrimonial.grupo_bem.isnot(None)
            )\
            .scalar() or 0

        valor_total_bens = db.session.query(func.coalesce(func.sum(BemPatrimonial.valor_aquisicao), 0))\
            .filter(
                BemPatrimonial.excluido == False,
                BemPatrimonial.situacao == 'Em uso',
                BemPatrimonial.valor_aquisicao.isnot(None)
            )\
            .scalar() or 0

        total_bens_com_valor = db.session.query(func.count(BemPatrimonial.id))\
            .filter(
                BemPatrimonial.valor_aquisicao.isnot(None),
                BemPatrimonial.excluido == False
            )\
            .scalar() or 0

        total_pendentes_inventario = db.session.query(func.count(BemPatrimonial.id))\
            .filter(
                BemPatrimonial.situacao == 'Inventariar',
                BemPatrimonial.excluido == False
            )\
            .scalar() or 0

        total_bens = db.session.query(func.count(BemPatrimonial.id))\
            .filter(BemPatrimonial.excluido == False)\
            .scalar() or 1
        percentual_inventariado = round(((total_bens - total_pendentes_inventario) / total_bens) * 100)

        total_em_manutencao = db.session.query(func.count(BemPatrimonial.id))\
            .filter(
                BemPatrimonial.situacao == 'Manutenção',
                BemPatrimonial.excluido == False
            )\
            .scalar() or 0

        data_inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_manutencoes_mes = db.session.query(func.count(MovimentacaoBem.id))\
            .select_from(MovimentacaoBem)\
            .join(BemPatrimonial)\
            .filter(
                MovimentacaoBem.tipo_movimentacao == 'Manutenção',
                MovimentacaoBem.data_movimentacao >= data_inicio_mes,
                BemPatrimonial.excluido == False
            ).scalar() or 0

        total_para_alienar = db.session.query(func.count(BemPatrimonial.id))\
            .filter(
                BemPatrimonial.situacao == 'Alienar',
                BemPatrimonial.excluido == False
            )\
            .scalar() or 0

        data_inicio_ano = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        total_alienados_ano = db.session.query(func.count(MovimentacaoBem.id))\
            .select_from(MovimentacaoBem)\
            .join(BemPatrimonial)\
            .filter(
                MovimentacaoBem.tipo_movimentacao == 'Alienação',
                MovimentacaoBem.data_movimentacao >= data_inicio_ano,
                BemPatrimonial.excluido == False
            ).scalar() or 0

        # Query para locais agrupando por localização dos bens
        locais_data = db.session.query(
            BemPatrimonial.localizacao.label('nome'),
            func.count(BemPatrimonial.id).label('total')
        ).filter(
            BemPatrimonial.excluido == False,
            BemPatrimonial.localizacao.isnot(None),
            BemPatrimonial.localizacao != ''  # Adiciona filtro para strings vazias
        ).group_by(BemPatrimonial.localizacao)\
        .order_by(func.count(BemPatrimonial.id).desc())\
        .all()

        labels_locais = [l.nome for l in locais_data if l.nome and l.nome.strip()]
        valores_locais = [int(l.total) for l in locais_data if l.nome and l.nome.strip()]

        # Query para tipos agrupando por grupo_bem
        tipos_data = db.session.query(
            BemPatrimonial.grupo_bem.label('nome'),
            func.count(BemPatrimonial.id).label('total')
        ).filter(
            BemPatrimonial.excluido == False,
            BemPatrimonial.grupo_bem.isnot(None),
            BemPatrimonial.grupo_bem != ''  # Adiciona filtro para strings vazias
        ).group_by(BemPatrimonial.grupo_bem)\
        .order_by(func.count(BemPatrimonial.id).desc())\
        .all()

        labels_tipos = [t.nome for t in tipos_data if t.nome and t.nome.strip()]
        valores_tipos = [int(t.total) for t in tipos_data if t.nome and t.nome.strip()]

        # Query para últimos bens
        data_limite = datetime.now() - timedelta(days=30)
        ultimos_bens = db.session.query(BemPatrimonial)\
            .filter(
                BemPatrimonial.data_cadastro >= data_limite,
                BemPatrimonial.excluido == False
            )\
            .order_by(BemPatrimonial.data_cadastro.desc())\
            .all()

        # Garantir que todos os bens tenham valores definidos
        for bem in ultimos_bens:
            bem.valor = bem.valor_aquisicao if bem.valor_aquisicao is not None else 0.0
            bem.local = bem.localizacao if bem.localizacao else 'Não informado'

                            # ---------------- ABA PUBLICAÇÕES ----------------
        total_publicacoes = db.session.query(func.count(Publicacao.id))\
            .filter(Publicacao.excluido == False)\
            .scalar() or 0

        # Contagem por tipo
        tipos_data = db.session.query(
            TipoPublicacao.nome.label('nome'),
            func.count(Publicacao.id).label('total')
        ).join(
            Publicacao,
            and_(
                Publicacao.tipo_id == TipoPublicacao.id,
                Publicacao.excluido == False
            )
        )\
        .group_by(TipoPublicacao.id, TipoPublicacao.nome)\
        .order_by(func.count(Publicacao.id).desc())\
        .all()

        labels_tipos = [t.nome for t in tipos_data]
        valores_tipos = [int(t.total) for t in tipos_data]

        data_inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_publicacoes_mes = db.session.query(func.count(Publicacao.id))\
            .filter(
                Publicacao.excluido == False,
                Publicacao.data_assinatura >= data_inicio_mes.date()  # Convertendo para date
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
        
        media_dias_publicacao = round(float(media_dias) if media_dias else 0)

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

        # Publicações recentes com join para tipo
        data_limite_recentes = datetime.now().date() - timedelta(days=30)
        data_limite_urgente = datetime.now().date() + timedelta(days=2)
        publicacoes_query = db.session.query(
            Publicacao, 
            TipoPublicacao.nome.label('tipo_nome')
        ).join(
            TipoPublicacao,
            Publicacao.tipo_id == TipoPublicacao.id
        ).filter(
            Publicacao.excluido == False,
            Publicacao.data_assinatura >= data_limite_recentes
        ).order_by(Publicacao.data_assinatura.desc())

        publicacoes_recentes = []
        for pub, tipo_nome in publicacoes_query.all():
            # Determinar o status baseado nas datas
            if pub.vigencia_inicio:
                if pub.vigencia_inicio <= data_limite_urgente:
                    status = 'Urgente'
                elif pub.vigencia_inicio > data_atual:
                    status = 'Pendente'
                else:
                    status = 'Normal'
            else:
                status = 'Normal'

            # Criar dicionário com todos os campos necessários
            publicacao_dict = {
                'data': pub.data_assinatura,
                'assunto': pub.objeto,  # Usando objeto como assunto
                'tipo': tipo_nome,
                'responsavel': pub.signatarios_embrapa[0].nome if pub.signatarios_embrapa else 'Não atribuído',
                'status': status,
                'link_do': None  # Campo não existe no modelo
            }
            publicacoes_recentes.append(publicacao_dict)

        # Atualizar contagem de tipos
        total_tipos = len(tipos_data)

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
                    extract('month', EntradaMaterial.data_movimento) == data.month,
                    extract('year', EntradaMaterial.data_movimento) == data.year
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
        current_app.logger.error(f"Erro no dashboard: {str(e)}\nTraceback: {traceback.format_exc()}")
        if 'db' in locals():
            db.session.rollback()
        
        # Usar valores padrão em caso de erro
        default_values = get_default_dashboard_values()
        return render_template('dashboard.html', **default_values)
