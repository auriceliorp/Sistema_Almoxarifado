from flask.cli import FlaskGroup
from app_render import app

cli = FlaskGroup(app)

if __name__ == '__main__':
    cli() 
