import os
import sys

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Importa a instância do app já criada
from app_render import app

# Não é necessário criar uma nova instância pois já existe uma em app_render.py
# O Gunicorn usará a instância 'app' diretamente

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
