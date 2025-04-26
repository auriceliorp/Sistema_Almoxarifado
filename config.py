import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'
    # Configuração do Banco de Dados PostgreSQL
    # Use DATABASE_URL se estiver definido (comum em plataformas de hospedagem), senão construa a URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql://{os.environ.get('DB_USER', 'user')}:{os.environ.get('DB_PASSWORD', 'password')}@" \
        f"{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '5432')}/" \
        f"{os.environ.get('DB_NAME', 'almoxarifado_db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Outras configurações podem ser adicionadas aqui
    # Ex: Configurações de email, etc.

