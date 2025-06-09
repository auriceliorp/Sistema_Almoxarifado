import os
import sys
import click
from flask.cli import FlaskGroup

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app_render import app

def create_cli_app():
    return app

cli = FlaskGroup(create_app=create_cli_app)

if __name__ == '__main__':
    cli() 
