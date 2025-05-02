from flask import Blueprint, render_template
from flask_login import login_required

ul = Blueprint('ul', __name__, url_prefix='/ul')

@ul.route('/')
@login_required
def lista_uls():
    return render_template('lista_uls.html')