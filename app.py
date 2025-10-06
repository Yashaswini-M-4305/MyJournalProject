from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this in production
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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


@app.route('/')
@login_required
def home():
    budget = 1000  # Fixed monthly budget
    today = datetime.date.today()
    monthly_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= datetime.date(today.year, today.month, 1)
    ).all()
    total_spent = sum(e.amount for e in monthly_expenses)
    remaining_budget = budget - total_spent
    return render_template(
        'home.html',
        expenses=monthly_expenses,
        total_spent=total_spent,
        remaining_budget=remaining_budget
    )


@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    desc = request.form.get('description')
    amt = float(request.form.get('amount'))
    date = datetime.date.today()
    new_expense = Expense(description=desc, amount=amt, date=date, user_id=current_user.id)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/experiences')
@login_required
def experiences():
    places = VisitedPlace.query.filter_by(user_id=current_user.id).all()
    foods = FoodTried.query.filter_by(user_id=current_user.id).all()
    shows = WatchedShow.query.filter_by(user_id=current_user.id).all()
    return render_template('experiences.html', places=places, foods=foods, shows=shows)


@app.route('/add_visited_place', methods=['POST'])
@login_required
def add_visited_place():
    name = request.form.get('name')
    new_place = VisitedPlace(name=name, user_id=current_user.id)
    db.session.add(new_place)
    db.session.commit()
    return redirect(url_for('experiences'))


@app.route('/add_food_tried', methods=['POST'])
@login_required
def add_food_tried():
    name = request.form.get('name')
    new_food = FoodTried(name=name, user_id=current_user.id)
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('experiences'))


@app.route('/add_watched_show', methods=['POST'])
@login_required
def add_watched_show():
    name = request.form.get('name')
    new_show = WatchedShow(name=name, user_id=current_user.id)
    db.session.add(new_show)
    db.session.commit()
    return redirect(url_for('experiences'))


@app.route('/delete_expense/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash("Not authorized to delete this expense.")
        return redirect(url_for('home'))
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete_visited_place/<int:id>', methods=['POST'])
@login_required
def delete_visited_place(id):
    place = VisitedPlace.query.get_or_404(id)
    if place.user_id != current_user.id:
        flash("Not authorized to delete this place.")
        return redirect(url_for('experiences'))
    db.session.delete(place)
    db.session.commit()
    return redirect(url_for('experiences'))


@app.route('/delete_food_tried/<int:id>', methods=['POST'])
@login_required
def delete_food_tried(id):
    food = FoodTried.query.get_or_404(id)
    if food.user_id != current_user.id:
        flash("Not authorized to delete this food item.")
        return redirect(url_for('experiences'))
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for('experiences'))


@app.route('/delete_watched_show/<int:id>', methods=['POST'])
@login_required
def delete_watched_show(id):
    show = WatchedShow.query.get_or_404(id)
    if show.user_id != current_user.id:
        flash("Not authorized to delete this show.")
        return redirect(url_for('experiences'))
    db.session.delete(show)
    db.session.commit()
    return redirect(url_for('experiences'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('home'))
        else:
            flash('Wrong username or password!')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        if old_password != current_user.password:
            flash('Old password is incorrect.')
            return redirect(url_for('change_password'))
        current_user.password = new_password
        db.session.commit()
        flash('Password updated successfully!')
        return redirect(url_for('profile'))
    return render_template('change_password.html')

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        # remove user-owned rows first (simple cascade by hand)
        Expense.query.filter_by(user_id=current_user.id).delete()
        VisitedPlace.query.filter_by(user_id=current_user.id).delete()
        FoodTried.query.filter_by(user_id=current_user.id).delete()
        WatchedShow.query.filter_by(user_id=current_user.id).delete()
        uid = current_user.id
        logout_user()
        user = User.query.get(uid)
        db.session.delete(user)
        db.session.commit()
        flash('Account deleted')
        return redirect(url_for('login'))
    return render_template('confirm_delete_account.html')

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'avatars')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

@app.route('/upload_avatar', methods=['GET', 'POST'])
@login_required
def upload_avatar():
    if request.method == 'POST':
        file = request.files.get('avatar')
        if not file or file.filename == '':
            flash('Please choose a file')
            return redirect(url_for('upload_avatar'))
        if not allowed_file(file.filename):
            flash('Invalid file type')
            return redirect(url_for('upload_avatar'))
        fn = secure_filename(f"user_{current_user.id}." + file.filename.rsplit('.',1)[1].lower())
        path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        file.save(path)
        # store path on user (optional: add column avatar_path)
        # If you don't have the column yet, skip saving to DB and just compute URL in template.
        flash('Avatar uploaded')
        return redirect(url_for('profile'))
    return render_template('upload_avatar.html')

@app.route('/edit_username', methods=['GET', 'POST'])
@login_required
def edit_username():
    if request.method == 'POST':
        new_username = request.form['username'].strip()
        if not new_username:
            flash('Username cannot be empty')
            return redirect(url_for('edit_username'))
        # prevent duplicates
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != current_user.id:
            flash('Username already taken')
            return redirect(url_for('edit_username'))
        current_user.username = new_username
        db.session.commit()
        flash('Username updated')
        return redirect(url_for('profile'))
    return render_template('edit_username.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
