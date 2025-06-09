import os
import sys

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from cli import app

if __name__ == "__main__":
    app.run()
