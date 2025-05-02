from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, logout_user, current_user

main = Blueprint('main', __name__)

@main.route('/home')
@login_required
def home():
    return render_template('home.html', usuario=current_user)

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

