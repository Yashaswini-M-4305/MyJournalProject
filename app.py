from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
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

class VisitedPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class FoodTried(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class WatchedShow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

@app.route('/')
@login_required
def home():
    budget = 1000
    today = datetime.date.today()
    monthly_expenses = Expense.query.filter(
        Expense.date >= datetime.date(today.year, today.month, 1)).all()
    total_spent = sum(e.amount for e in monthly_expenses)
    remaining_budget = budget - total_spent
    return render_template('home.html', expenses=monthly_expenses,
                           total_spent=total_spent, remaining_budget=remaining_budget)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    desc = request.form.get('description')
    amt = float(request.form.get('amount'))
    date = datetime.date.today()
    new_expense = Expense(description=desc, amount=amt, date=date)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/experiences')
@login_required
def experiences():
    places = VisitedPlace.query.all()
    foods = FoodTried.query.all()
    shows = WatchedShow.query.all()
    return render_template('experiences.html', places=places, foods=foods, shows=shows)

@app.route('/add_visited_place', methods=['POST'])
@login_required
def add_visited_place():
    name = request.form.get('name')
    new_place = VisitedPlace(name=name)
    db.session.add(new_place)
    db.session.commit()
    return redirect(url_for('experiences'))

@app.route('/add_food_tried', methods=['POST'])
@login_required
def add_food_tried():
    name = request.form.get('name')
    new_food = FoodTried(name=name)
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('experiences'))

@app.route('/add_watched_show', methods=['POST'])
@login_required
def add_watched_show():
    name = request.form.get('name')
    new_show = WatchedShow(name=name)
    db.session.add(new_show)
    db.session.commit()
    return redirect(url_for('experiences'))

@app.route('/delete_expense/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_visited_place/<int:id>', methods=['POST'])
@login_required
def delete_visited_place(id):
    place = VisitedPlace.query.get_or_404(id)
    db.session.delete(place)
    db.session.commit()
    return redirect(url_for('experiences'))

@app.route('/delete_food_tried/<int:id>', methods=['POST'])
@login_required
def delete_food_tried(id):
    food = FoodTried.query.get_or_404(id)
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for('experiences'))

@app.route('/delete_watched_show/<int:id>', methods=['POST'])
@login_required
def delete_watched_show(id):
    show = WatchedShow.query.get_or_404(id)
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
