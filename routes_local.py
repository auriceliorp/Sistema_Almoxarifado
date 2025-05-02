from flask import Blueprint, render_template
from flask_login import login_required

local = Blueprint('local', __name__, url_prefix='/local')

@local.route('/')
@login_required
def lista_locais():
    return render_template('lista_locais.html')