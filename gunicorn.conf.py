import os
import multiprocessing
import logging
import sys

# Configuração de logging
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': sys.stdout
        },
    },
    'loggers': {
        'gunicorn.error': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'gunicorn.access': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}

# Configurações do Gunicorn
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = 1
threads = int(os.environ.get('GUNICORN_THREADS', '4'))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gthread')
worker_tmp_dir = os.environ.get('GUNICORN_WORKER_TMP_DIR', '/dev/shm')
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))
keepalive = 65
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 120
log_level = os.environ.get('GUNICORN_LOG_LEVEL', 'debug')

# Hooks
def on_starting(server):
    logging.info("Gunicorn está iniciando...")

def on_reload(server):
    logging.info("Gunicorn está recarregando...")

def when_ready(server):
    logging.info("Gunicorn está pronto para receber conexões")

def pre_fork(server, worker):
    logging.info(f"Criando worker {worker.pid}")

def post_fork(server, worker):
    logging.info(f"Worker {worker.pid} criado")

def pre_exec(server):
    logging.info("Gunicorn master está re-executando")

def worker_abort(worker):
    logging.error(f"Worker {worker.pid} foi abortado!") 
