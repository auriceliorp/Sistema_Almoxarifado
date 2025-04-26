import os
import sys
import importlib.util

# Adiciona o diretório atual ao path do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carrega o módulo app.py como um módulo independente
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)

# Substitui as importações relativas por importações absolutas
sys.modules["app_module"] = app_module
sys.modules["app_module.config"] = importlib.import_module("config")
sys.modules["app_module.database"] = importlib.import_module("database")
sys.modules["app_module.models"] = importlib.import_module("models")
sys.modules["app_module.routes"] = importlib.import_module("routes")

# Executa o módulo app.py
spec.loader.exec_module(app_module)

# Obtém a função create_app e cria a aplicação
create_app = getattr(app_module, "create_app")
app = create_app()

if __name__ == "__main__":
    app.run()
