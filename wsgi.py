import os
import sys

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Importa e cria a aplicação
from app_render import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
