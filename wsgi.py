import os
import sys
import logging

# Configura logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    logger.info("Iniciando importação do app")
    from app_render import app
    logger.info("App importado com sucesso")
except Exception as e:
    logger.error(f"Erro ao importar app: {str(e)}")
    raise

# Configura host e porta
host = os.environ.get('HOST', '0.0.0.0')
port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    logger.info(f"Iniciando servidor em {host}:{port}")
    app.run(host=host, port=port)

