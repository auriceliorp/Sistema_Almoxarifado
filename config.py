# config.py

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'

    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or \
        f"postgresql://{os.environ.get('DB_USER', 'user')}:{os.environ.get('DB_PASSWORD', 'password')}@" \
        f"{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '5432')}/" \
        f"{os.environ.get('DB_NAME', 'almoxarifado_db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # E-mail (usado no app_render)
    EMAIL_REMETENTE = os.environ.get('EMAIL_REMETENTE')
    EMAIL_SENHA = os.environ.get('EMAIL_SENHA')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
