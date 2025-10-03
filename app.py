from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Needed for login sessions
db = SQLAlchemy(app)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'   # redirect to login if not logged in

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Model for an expense
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.Date)

class FavoritePlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class FavoriteFood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class FavoriteShow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


@app.route('/')
@login_required
def home():
    budget = 1000  # Fixed monthly budget (you can change)
    today = datetime.date.today()
    monthly_expenses = Expense.query.filter(
        Expense.date >= datetime.date(today.year, today.month, 1)).all()
    total_spent = sum(e.amount for e in monthly_expenses)
    remaining_budget = budget - total_spent
    return render_template('home.html', expenses=monthly_expenses,
                           total_spent=total_spent, remaining_budget=remaining_budget)

@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    desc = request.form.get('description')
    amt = float(request.form.get('amount'))
    date = datetime.date.today()
    new_expense = Expense(description=desc, amount=amt, date=date)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/favorites')
@login_required
def favorites():
    places = FavoritePlace.query.all()
    foods = FavoriteFood.query.all()
    shows = FavoriteShow.query.all()
    return render_template('favorites.html', places=places, foods=foods, shows=shows)

@app.route('/add_place', methods=['POST'])
@login_required
def add_place():
    name = request.form.get('name')
    new_place = FavoritePlace(name=name)
    db.session.add(new_place)
    db.session.commit()
    return redirect(url_for('favorites'))

@app.route('/add_food', methods=['POST'])
@login_required
def add_food():
    name = request.form.get('name')
    new_food = FavoriteFood(name=name)
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('favorites'))

@app.route('/add_show', methods=['POST'])
@login_required
def add_show():
    name = request.form.get('name')
    new_show = FavoriteShow(name=name)
    db.session.add(new_show)
    db.session.commit()
    return redirect(url_for('favorites'))

@app.route('/delete_expense/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_place/<int:id>', methods=['POST'])
@login_required
def delete_place(id):
    place = FavoritePlace.query.get_or_404(id)
    db.session.delete(place)
    db.session.commit()
    return redirect(url_for('favorites'))

@app.route('/delete_food/<int:id>', methods=['POST'])
@login_required
def delete_food(id):
    food = FavoriteFood.query.get_or_404(id)
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for('favorites'))

@app.route('/delete_show/<int:id>', methods=['POST'])
@login_required
def delete_show(id):
    show = FavoriteShow.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return redirect(url_for('favorites'))

# Registration route
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

# Login route
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

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates database tables if they don't exist
    app.run(debug=True)
