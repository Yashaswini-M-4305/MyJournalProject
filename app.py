from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
def home():
    budget = 1000  # Fixed monthly budget (you can change)
    today = datetime.date.today()
    # Filter this month's expenses
    monthly_expenses = Expense.query.filter(
        Expense.date >= datetime.date(today.year, today.month, 1)).all()
    total_spent = sum(e.amount for e in monthly_expenses)
    remaining_budget = budget - total_spent
    return render_template('home.html', expenses=monthly_expenses,
                           total_spent=total_spent, remaining_budget=remaining_budget)

@app.route('/add', methods=['POST'])
def add_expense():
    desc = request.form.get('description')
    amt = float(request.form.get('amount'))
    date = datetime.date.today()
    new_expense = Expense(description=desc, amount=amt, date=date)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('home'))

# View Favorites Page
@app.route('/favorites')
def favorites():
    places = FavoritePlace.query.all()
    foods = FavoriteFood.query.all()
    shows = FavoriteShow.query.all()
    return render_template('favorites.html', places=places, foods=foods, shows=shows)

# Add Place
@app.route('/add_place', methods=['POST'])
def add_place():
    name = request.form.get('name')
    new_place = FavoritePlace(name=name)
    db.session.add(new_place)
    db.session.commit()
    return redirect(url_for('favorites'))

# Add Food
@app.route('/add_food', methods=['POST'])
def add_food():
    name = request.form.get('name')
    new_food = FavoriteFood(name=name)
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('favorites'))

# Add Show
@app.route('/add_show', methods=['POST'])
def add_show():
    name = request.form.get('name')
    new_show = FavoriteShow(name=name)
    db.session.add(new_show)
    db.session.commit()
    return redirect(url_for('favorites'))

# Delete expense
@app.route('/delete_expense/<int:id>', methods=['POST'])
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('home'))

# Delete favorite place
@app.route('/delete_place/<int:id>', methods=['POST'])
def delete_place(id):
    place = FavoritePlace.query.get_or_404(id)
    db.session.delete(place)
    db.session.commit()
    return redirect(url_for('favorites'))

# Delete favorite food
@app.route('/delete_food/<int:id>', methods=['POST'])
def delete_food(id):
    food = FavoriteFood.query.get_or_404(id)
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for('favorites'))

# Delete favorite show
@app.route('/delete_show/<int:id>', methods=['POST'])
def delete_show(id):
    show = FavoriteShow.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return redirect(url_for('favorites'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates database tables if they don't exist
    app.run(debug=True)