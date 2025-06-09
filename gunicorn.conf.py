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
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
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
            'propagate': True,
        },
        'gunicorn.access': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    }
}

# Configurações básicas
bind = "0.0.0.0:8000"
workers = 1
threads = 1
worker_class = 'sync'
timeout = 120
keepalive = 2

# Configurações de debug
capture_output = True
enable_stdio_inheritance = True
preload_app = False
reload = False

# Hooks para logging
def on_starting(server):
    logging.info("Gunicorn está iniciando...")

def when_ready(server):
    logging.info("Gunicorn está pronto para receber conexões")

def pre_fork(server, worker):
    logging.info(f"Criando worker {worker.pid}")

def post_fork(server, worker):
    logging.info(f"Worker {worker.pid} criado")

def worker_abort(worker):
    logging.error(f"Worker {worker.pid} foi abortado!") 
