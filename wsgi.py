import os
import sys
import logging
import traceback

# Configura logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao PYTHONPATH
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)
logger.info(f"Diretório atual: {current_dir}")
logger.info(f"PYTHONPATH: {sys.path}")

try:
    logger.info("Iniciando importação do app")
    from app_render import app
    logger.info("App importado com sucesso")
except Exception as e:
    logger.error(f"Erro ao importar app: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

# Configura host e porta
host = os.environ.get('HOST', '0.0.0.0')
port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    logger.info(f"Iniciando servidor em {host}:{port}")
    app.run(host=host, port=port)
