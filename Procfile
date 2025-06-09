release: flask db upgrade
web: sleep 3 && FLASK_APP=cli.py flask db upgrade && gunicorn app_render:app
