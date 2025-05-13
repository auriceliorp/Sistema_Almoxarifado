import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'

    # Usa diretamente a variável correta
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # E-mail (usado no app_render)
    EMAIL_REMETENTE = os.environ.get('EMAIL_REMETENTE')
    EMAIL_SENHA = os.environ.get('EMAIL_SENHA')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
