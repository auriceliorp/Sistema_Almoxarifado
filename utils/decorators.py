from functools import wraps
from flask import redirect, url_for, flash, request, session
from flask_login import current_user, login_required
from datetime import datetime
from extensoes import db

def permissao_required(permissao, requer_autorizacao=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor, faça login para acessar esta página.', 'warning')
                return redirect(url_for('main.login'))

            if not current_user.tem_permissao(permissao):
                flash('Você não tem permissão para acessar esta funcionalidade.', 'danger')
                return redirect(url_for('main.home'))

            # Se o usuário é super admin ou admin, não precisa de autorização
            if current_user.is_super_admin() or current_user.is_admin():
                return f(*args, **kwargs)

            # Se a operação requer autorização e o usuário precisa de autorização
            if requer_autorizacao and current_user.requer_autorizacao():
                # Importa AutorizacaoOperacao apenas quando necessário
                from models import AutorizacaoOperacao
                
                # Verifica se já existe uma autorização pendente
                autorizacao = AutorizacaoOperacao.query.filter_by(
                    solicitante_id=current_user.id,
                    operacao=f.__name__,
                    status='PENDENTE'
                ).first()

                if not autorizacao:
                    # Cria nova solicitação de autorização
                    autorizacao = AutorizacaoOperacao(
                        operacao=f.__name__,
                        solicitante_id=current_user.id,
                        dados_operacao={
                            'url': request.url,
                            'metodo': request.method,
                            'args': dict(request.args),
                            'form': dict(request.form)
                        }
                    )
                    db.session.add(autorizacao)
                    db.session.commit()
                    
                    flash('Sua solicitação foi enviada para autorização.', 'info')
                    return redirect(url_for('autorizacao.lista_pendentes'))
                else:
                    flash('Já existe uma solicitação pendente para esta operação.', 'warning')
                    return redirect(url_for('autorizacao.lista_pendentes'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('main.login'))
            
        if not current_user.perfil or current_user.perfil.nome != 'Super Administrador':
            flash('Apenas Super Administradores podem acessar esta página.', 'danger')
            return redirect(url_for('main.home'))
            
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('main.login'))
            
        if not current_user.perfil or (not current_user.is_admin() and not current_user.is_super_admin()):
            flash('Acesso negado. Você precisa ser administrador para acessar esta página.', 'error')
            return redirect(url_for('main.home'))
            
        return f(*args, **kwargs)
    return decorated_function

def operador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('main.login'))
            
        if not current_user.perfil or current_user.perfil.nome != 'Operador':
            flash('Apenas Operadores podem acessar esta página.', 'danger')
            return redirect(url_for('main.home'))
            
        return f(*args, **kwargs)
    return decorated_function

def autorizador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('main.login'))
            
        if not current_user.perfil or current_user.perfil.nome != 'Autorizador':
            flash('Apenas Autorizadores podem acessar esta página.', 'danger')
            return redirect(url_for('main.home'))
            
        return f(*args, **kwargs)
    return decorated_function

def perfil_required(perfis_autorizados):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.perfil or current_user.perfil.nome not in perfis_autorizados:
                flash('Acesso não autorizado para seu perfil.', 'danger')
                return redirect(url_for('main.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def almoxarifado_access_required(permissao=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor, faça login para acessar esta página.', 'warning')
                return redirect(url_for('main.login'))
            
            # Super Admin sempre tem acesso
            if current_user.is_super_admin():
                return f(*args, **kwargs)
                
            # Se não for super admin, verifica outras permissões
            if permissao and not current_user.tem_permissao(permissao):
                flash('Você não tem permissão para acessar esta funcionalidade.', 'danger')
                return redirect(url_for('main.home'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator 
