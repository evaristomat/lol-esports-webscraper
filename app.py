from flask import Flask, redirect, render_template, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Load the CSV data into a DataFrame
bets_df = pd.read_csv('bets/bets.csv')

# A global dictionary to hold users' bets (in a real-world app, this would be in a database)
user_bets = {}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class UserBet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bet_data = db.Column(db.String, nullable=False)  # Store bet data as a serialized string for simplicity
    status = db.Column(db.String, default='Pending', nullable=False)  # New status column
    user = db.relationship('User', backref=db.backref('bets', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash('Login failed. Check username and password.', 'danger')
    return render_template("login.html")

import re

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # Check if the passwords match
        if password != confirmation:
            flash('Passwords do not match. Please try again.', 'danger')
            return render_template("register.html")
        
        # Check if the password is at least 6 characters and contains only letters and numbers
        if not re.match('^[A-Za-z0-9]{6,}$', password):
            flash('Password must be at least 6 characters long and contain only letters and numbers.', 'danger')
            return render_template("register.html")

        # Check for existing user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Choose another.', 'danger')
            return render_template("register.html")

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Auto login after registration
        login_user(new_user)
        
        flash('Registration successful.', 'success')
        return redirect(url_for('index'))
    
    return render_template("register.html")

@app.route('/history', methods=['GET'])
@login_required
def history():
    # Get the bets for the logged-in user from the database
    user_bets_db = UserBet.query.filter_by(user_id=current_user.id).filter(UserBet.status != "Pending").all()  # Filtering out 'Pending' bets
    bets = [{'data': bet.bet_data.split(','), 'id': bet.id, 'status': bet.status} for bet in user_bets_db]
    return render_template('history.html', bets=bets)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", 'success')  # Update the flash message
    return redirect(url_for("login"))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    filtered_df = bets_df.copy()
    houses = bets_df['House'].unique().tolist()
    selected_house = request.args.get('house', '')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = request.args.get('sort_column', 'ROI')
    filtered_df = filtered_df[filtered_df['status'] != 'Pending']

    if selected_house:
        filtered_df = filtered_df[filtered_df['House'] == selected_house]

    if sort_column == "ROI":
        filtered_df['ROI'] = filtered_df['ROI'].str.rstrip('%').astype('float')

    if sort_order == 'asc':
        filtered_df = filtered_df.sort_values(by=sort_column, ascending=True)
    else:
        filtered_df = filtered_df.sort_values(by=sort_column, ascending=False)

    if sort_column == "ROI":
        filtered_df['ROI'] = filtered_df['ROI'].astype(str) + '%'

    filtered_df = filtered_df.drop(columns=['status'])

    # Get the serialized bet data for bets in the user's history
    user_bets_db = UserBet.query.filter_by(user_id=current_user.id).all()
    added_bet_data = [bet.bet_data for bet in user_bets_db]

    return render_template('index.html', data=filtered_df.iterrows(), houses=houses, selected_house=selected_house, sort_order=sort_order, sort_column=sort_column, added_bet_data=added_bet_data)


@app.route('/bets', methods=['GET'])
@login_required
def bets():
    # Get the bets for the logged-in user from the database
    user_bets_db = UserBet.query.filter_by(user_id=current_user.id).all()
    bets = [{'data': bet.bet_data.split(','), 'id': bet.id} for bet in user_bets_db]
    return render_template('bets.html', bets=bets)


@app.route('/add_bet', methods=['POST'])
@login_required
def add_bet():
    try:
        bet_id = int(request.form.get('bet_id'))
        bet = bets_df.iloc[bet_id].tolist()
    except (TypeError, ValueError, IndexError):
        flash('Invalid bet ID.', 'danger')
        return redirect(url_for('index'))

    # Check if bet already exists for user
    serialized_bet = ','.join(map(str, bet))
    existing_bet = UserBet.query.filter_by(user_id=current_user.id, bet_data=serialized_bet).first()
    if existing_bet:
        flash('This bet is already in your history.', 'warning')
        return redirect(url_for('index'))

    # Store the bet in the database
    new_bet = UserBet(user_id=current_user.id, bet_data=serialized_bet)
    db.session.add(new_bet)
    db.session.commit()

    flash('Bet added successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/remove_bet', methods=['POST'])
@login_required
def remove_bet():
    bet_id = request.form.get('bet_id')
    print(f"Trying to remove bet with ID: {bet_id}")  # Logging
    bet_to_remove = UserBet.query.get(bet_id)
    if bet_to_remove:
        db.session.delete(bet_to_remove)
        db.session.commit()
        flash('Bet removed successfully!', 'success')
    else:
        print(f"No bet found with ID: {bet_id}")  # Logging
        flash('Error removing bet.', 'danger')
    return redirect(url_for('bets'))

if __name__ == "__main__":
    #db.create_all()
    app.run(debug=True)