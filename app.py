from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
from io import StringIO
import csv
from werkzeug.utils import secure_filename
from collections import defaultdict
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# Flask-Mail setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_gmail_app_password'
mail = Mail(app)

UPLOAD_FOLDER = os.path.join('static', 'avatars')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def generate_reset_token(email, secret_key, expiration=3600):
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, secret_key, expiration=3600):
    s = URLSafeTimedSerializer(secret_key)
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=expiration)
    except Exception:
        return None
    return email

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class VisitedPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class FoodTried(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WatchedShow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('_flashes', None)
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.password.startswith('pbkdf2:'):
                if check_password_hash(user.password, password):
                    login_user(user)
                    flash('Logged in successfully!')
                    return redirect(url_for('home'))
            else:
                if user.password == password:
                    user.password = generate_password_hash(password)
                    db.session.commit()
                    login_user(user)
                    flash('Logged in successfully!')
                    return redirect(url_for('home'))
        flash('Wrong username or password!')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None)
    flash('Logged out!')
    return redirect(url_for('login'))

# Forgot password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email, app.config['SECRET_KEY'])
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_url}"
            mail.send(msg)
            flash('Check your email for the password reset link.')
        else:
            flash('No user found with that email.')
    return render_template('forgot_password.html')

# Reset password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token, app.config['SECRET_KEY'])
    if not email:
        flash('Reset link expired or invalid.')
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        new_password = request.form['new_password']
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Your password has been updated. Please log in.')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

# ... (rest of your existing routes like home, add_expense, etc.) ...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
