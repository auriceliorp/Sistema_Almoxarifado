# config.py

import os
from dotenv import load_dotenv

# Define o caminho base do projeto e carrega variáveis do .env (em ambiente local)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Chave secreta usada para proteger sessões e formulários
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'

    # Configuração da URI do banco de dados (usada pelo SQLAlchemy)
    # Em produção (Render), ela é definida diretamente como variável de ambiente
    # Exemplo: postgresql://usuario:senha@host:porta/nomedobanco
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')

    # Desativa o rastreamento de modificações do SQLAlchemy para melhorar desempenho
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Variáveis opcionais para envio de e-mail (caso implementado)
    EMAIL_REMETENTE = os.environ.get('EMAIL_REMETENTE')
    EMAIL_SENHA = os.environ.get('EMAIL_SENHA')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
