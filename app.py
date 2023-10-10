from flask import Flask, redirect, render_template, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def get_last_db_update_date(log_file_path):
    with open(log_file_path, 'r') as f:
        lines = f.readlines()

    for line in reversed(lines):
        #print("Processing line:", line)
        if "Database Uptaded" in line:
            try:
                timestamp_str = line.strip().split(' - ')[0].strip()  # Modified split pattern
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').strftime('%Y-%m-%d')
            except ValueError as e:
                print(f"Error parsing line '{line}': {e}")  # Debug line
                continue
    return None

def populate_bets_from_csv():
    df = pd.read_csv('bets/bets.csv')
    for _, row in df.iterrows():
        existing_bet = Bets.query.filter_by(
            date=row['date'],
            league=row['league'],
            t1=row['t1'],
            t2=row['t2'],
            bet_type=row['bet_type'],
            bet_line=row['bet_line'],
            ROI=row['ROI'],
            odds=row['odds'],
            House=row['House']
        ).first()

        if existing_bet:
            # Update the status if it has changed
            if existing_bet.status != row['status']:
                existing_bet.status = row['status']
        else:
            # If the bet doesn't exist in the DB, add it
            bet = Bets(date=row['date'], league=row['league'], t1=row['t1'], t2=row['t2'], bet_type=row['bet_type'], bet_line=row['bet_line'], ROI=row['ROI'], odds=row['odds'], House=row['House'], status=row['status'])
            db.session.add(bet)
    
    db.session.commit()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Bets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False)
    league = db.Column(db.String, nullable=False)
    t1 = db.Column(db.String, nullable=False)
    t2 = db.Column(db.String, nullable=False)
    bet_type = db.Column(db.String, nullable=False)
    bet_line = db.Column(db.String, nullable=False)
    ROI = db.Column(db.String, nullable=False)
    odds = db.Column(db.String, nullable=False)
    House = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default='Pending', nullable=False)

class UserBet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String, nullable=False)
    league = db.Column(db.String, nullable=False)
    t1 = db.Column(db.String, nullable=False)
    t2 = db.Column(db.String, nullable=False)
    bet_type = db.Column(db.String, nullable=False)
    bet_line = db.Column(db.String, nullable=False)
    ROI = db.Column(db.String, nullable=False)
    odds = db.Column(db.String, nullable=False)
    House = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    user = db.relationship('User', backref=db.backref('bets', lazy=True))

class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String, nullable=False)
    league = db.Column(db.String, nullable=False)
    t1 = db.Column(db.String, nullable=False)
    t2 = db.Column(db.String, nullable=False)
    bet_type = db.Column(db.String, nullable=False)
    bet_line = db.Column(db.String, nullable=False)
    ROI = db.Column(db.String, nullable=False)
    odds = db.Column(db.String, nullable=False)
    House = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    user = db.relationship('User', backref=db.backref('history_bets', lazy=True))

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
    # Fetch the bets for the logged-in user from the UserHistory table
    user_history_bets_db = UserHistory.query.filter_by(user_id=current_user.id).all()
    
    total_profit = 0
    history_bets = []
    for bet in user_history_bets_db:
        profit = 0
        if bet.status == "win":
            profit = round(float(bet.odds) - 1, 2)
        elif bet.status == "loss":
            profit = -1
        
        total_profit += profit
        total_profit = round(total_profit, 2)  # Round the total profit after each addition

        formatted_profit = f"{profit} U"  # Format the profit with the "U" prefix
        
        history_bets.append({
            'data': [bet.date, bet.league, bet.t1, bet.t2, bet.bet_type, bet.bet_line, bet.ROI, bet.odds, bet.House, bet.status, formatted_profit],
            'id': bet.id
        })

    formatted_total_profit = f"{total_profit} U"  # Format the total profit with the "U" prefix

    return render_template('history.html', bets=history_bets, total_profit=formatted_total_profit)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", 'success')  # Update the flash message
    return redirect(url_for("login"))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Load the CSV data into a DataFrame
    bets_df = pd.read_csv('bets/bets.csv')
    last_update_date = get_last_db_update_date('database\logs\data_processing.log')

    # Ensure 'Date' column is in datetime format for correct sorting
    bets_df['date'] = pd.to_datetime(bets_df['date'])
    bets_df['date'] = bets_df['date'].dt.strftime('%Y-%m-%d')

    houses = bets_df['House'].unique().tolist()
    selected_house = request.args.get('house', '')
    sort_order = request.args.get('sort_order', 'asc')
    sort_column = request.args.get('sort_column', 'ROI')

    if selected_house:
        bets_df = bets_df[bets_df['House'] == selected_house]

    # Handle ROI as a float for proper sorting, then return it to its string representation afterwards
    if sort_column == "ROI":
        bets_df['ROI'] = bets_df['ROI'].str.rstrip('%').astype('float')

    # Sort the DataFrame
    sorting_columns = ['date', 't1', 'ROI']
    ascending_order = [True, True, True] if sort_order == 'asc' else [False, True, False]
    bets_df = bets_df.sort_values(by=sorting_columns, ascending=ascending_order)

    # Convert ROI back to a formatted string if needed
    if 'ROI' in bets_df.columns:
        bets_df['ROI'] = bets_df['ROI'].map("{:.2f}%".format)

    # Fetch bets added by the user
    user_bets_db = UserBet.query.filter_by(user_id=current_user.id, status="pending").all()
    added_bet_data = [','.join([str(bet.date), bet.league, bet.t1, bet.t2, bet.bet_type, bet.bet_line, bet.ROI, bet.odds, bet.House, bet.status]) for bet in user_bets_db]

    return render_template('index.html',
                            data=bets_df.iterrows(),
                            houses=houses,
                            selected_house=selected_house,
                            sort_order=sort_order,
                            sort_column=sort_column,
                            added_bet_data=added_bet_data,
                            last_update_date=last_update_date)


@app.route('/bets', methods=['GET'])
@login_required
def bets():
    # Get the bets for the logged-in user from the database
    user_bets_db = UserBet.query.filter_by(user_id=current_user.id).all()
    bets = [{'data': [bet.date, bet.league, bet.t1, bet.t2, bet.bet_type, bet.bet_line, bet.ROI, bet.odds, bet.House, bet.status], 'id': bet.id} for bet in user_bets_db]
    return render_template('bets.html', bets=bets)

@app.route('/all_bets', methods=['GET'])
@login_required
def all_bets():
    # Read CSV data
    all_bets_df = pd.read_csv('bets/results.csv')
    
    # Remove the '%' sign from the 'ROI' column and convert it to float
    all_bets_df['ROI'] = all_bets_df['ROI'].str.rstrip('%').astype('float')

    # Fetch the last 20 records
    last_20_bets = all_bets_df.tail(10)
    
    # Calculate and format total profit
    rounded_profit = round(all_bets_df['profit'].sum(), 2)
    total_profit = f"{rounded_profit} U"    
    
    # Convert DataFrame to a list of dictionaries for easy rendering in templates
    bets_list = last_20_bets.to_dict(orient='records')

    # Calculate profits by ROI range
    profit_by_range = {
        "0-10": all_bets_df[(all_bets_df['ROI'] > 0) & (all_bets_df['ROI'] <= 10)]['profit'].sum(),
        "10+": all_bets_df[all_bets_df['ROI'] > 10]['profit'].sum(),
        "20+": all_bets_df[all_bets_df['ROI'] > 20]['profit'].sum(),
        "30+": all_bets_df[all_bets_df['ROI'] > 30]['profit'].sum()
    }
    profit_by_range_json = json.dumps(profit_by_range)
    profit_by_league = all_bets_df.groupby('league')['profit'].sum().to_dict()

    return render_template('all_bets.html', all_bets=all_bets_df, bets=bets_list,
                            total_profit=total_profit,
                            profit_by_range_json=profit_by_range_json,
                            profit_by_league=profit_by_league)

@app.route('/add_bet', methods=['POST'])
@login_required
def add_bet():
    bet_id = int(request.form.get('bet_id'))
    
    # Fetch the relevant bet from the CSV
    bets_df = pd.read_csv('bets/bets.csv')
    try:
        bet = bets_df.iloc[bet_id]
    except (TypeError, ValueError, IndexError):
        flash('Invalid bet ID.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bet already exists for user
    existing_bet = UserBet.query.filter_by(user_id=current_user.id, date=bet['date'], league=bet['league'], t1=bet['t1'], t2=bet['t2'], bet_type=bet['bet_type'], bet_line=bet['bet_line'], ROI=bet['ROI'], odds=bet['odds'], House=bet['House'], status=bet["status"]).first()
    
    if existing_bet:
        flash('This bet is already in your history.', 'warning')
        return redirect(url_for('index'))

    # Store the bet in the database
    new_bet = UserBet(user_id=current_user.id, date=bet['date'], league=bet['league'], t1=bet['t1'], t2=bet['t2'], bet_type=bet['bet_type'], bet_line=bet['bet_line'], ROI=bet['ROI'], odds=bet['odds'], House=bet['House'], status=bet["status"])
    
    db.session.add(new_bet)
    db.session.commit()

    flash('Bet added successfully!', 'success')
    return redirect(url_for('index'))

# @app.route('/move_all_to_history', methods=['POST'])
# @login_required
# def move_all_to_history():
#     # Update the status of all pending bets to "History" in the database
#     UserBet.query.filter_by(user_id=current_user.id, status="pending").update({"status": "History"})
#     db.session.commit()
#     flash('All pending bets have been moved to history.', 'success')
#     return redirect(url_for('bets'))  # Redirect back to the "My Bets" page

@app.route('/remove_bet', methods=['POST'])
@login_required
def remove_bet():
    bet_id = request.form.get('bet_id')
    app.logger.info(f"Trying to remove bet with ID: {bet_id}")  # Updated logging
    bet_to_remove = UserBet.query.get(bet_id)
    if bet_to_remove:
        db.session.delete(bet_to_remove)
        db.session.commit()
        flash('Bet removed successfully!', 'success')
    else:
        app.logger.error(f"No bet found with ID: {bet_id}")  # Updated logging
        flash('Error removing bet.', 'danger')
    return redirect(url_for('bets'))

@app.route('/remove_history_bet', methods=['POST'])
@login_required
def remove_history_bet():
    bet_id = request.form.get('bet_id')  # Get bet ID from the form
    
    if bet_id:
        # Find the bet in UserHistory using the bet_id
        bet_to_remove = UserHistory.query.filter_by(id=bet_id, user_id=current_user.id).first()
        
        # If the bet exists in the history, delete it
        if bet_to_remove:
            db.session.delete(bet_to_remove)
            db.session.commit()
            flash('Bet successfully removed from history!', 'success')
        else:
            flash('Error: Bet not found in history.', 'danger')
    else:
        flash('Error: Invalid bet ID.', 'danger')

    return redirect(url_for('history'))

@app.route('/update_bets', methods=['POST'])
@login_required
def update_bets():
    # First, repopulate and update the main Bets table from the CSV
    populate_bets_from_csv()

    # Loop through all UserBets
    for user_bet in UserBet.query.filter_by(user_id=current_user.id).all():
        # Fetch the corresponding bet in the Bets table using unique identifiers like date, league, t1, t2, etc.
        corresponding_bet = Bets.query.filter_by(
            date=user_bet.date,
            league=user_bet.league,
            t1=user_bet.t1,
            t2=user_bet.t2,
            bet_type=user_bet.bet_type,
            bet_line=user_bet.bet_line,
            ROI=user_bet.ROI,
            odds=user_bet.odds,
            House=user_bet.House
        ).first()

        if corresponding_bet and corresponding_bet.status != "pending":
            # Create a record in UserHistory
            history_bet = UserHistory(
                user_id=user_bet.user_id,
                date=user_bet.date,
                league=user_bet.league,
                t1=user_bet.t1,
                t2=user_bet.t2,
                bet_type=user_bet.bet_type,
                bet_line=user_bet.bet_line,
                ROI=user_bet.ROI,
                odds=user_bet.odds,
                House=user_bet.House,
                status=corresponding_bet.status  # Use the status from the Bets table
            )
            db.session.add(history_bet)
            
            # Remove the bet from UserBet
            db.session.delete(user_bet)
            
    db.session.commit()

    flash('Bets updated successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)