from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://henry:Tfosbuya?1479@localhost:3306/fw_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model for login
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __init__(self, username, password=None):
        self.username = username
        if password:
            self.set_password(password)


# Define the Feedback model
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(200))
    student_id = db.Column(db.String(200), unique=True)
    lecturer = db.Column(db.String(200))
    rating = db.Column(db.Integer)
    comments = db.Column(db.Text())

    def __init__(self, student, student_id, lecturer, rating, comments):
        self.student = student
        self.student_id = student_id
        self.lecturer = lecturer
        self.rating = rating
        self.comments = comments

def calculate_avg(data):
    # Calculate the average rating and return it along with other data
    total_ratings = data['num_ratings']
    average_rating = data['average_rating'] if total_ratings > 0 else 0
    return {
        'average_rating': average_rating,
        'num_ratings': total_ratings,
        'rank': 0  # Placeholder for rank
    }

def sort_results(results):
    # Sort the lecturers based on their average rating
    sorted_results = sorted(results.items(), key=lambda x: x[1]['average_rating'], reverse=True)

    # Calculate the rank of each lecturer
    for i, (lecturer, details) in enumerate(sorted_results, start=1):
        details['rank'] = i

    return dict(sorted_results)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes for login and signup
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose another.', 'error')
        else:
            # Create a new user
            new_user = User(username=username, password=password)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Signup successful! You can now login.', 'success')
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    # Query the database to get results (assuming Feedback is the model)
    results = db.session.query(Feedback.lecturer,
                               db.func.avg(Feedback.rating).label('average_rating'),
                               db.func.count(Feedback.rating).label('num_ratings')) \
                        .group_by(Feedback.lecturer).all()

    # Create a dictionary to store the results
    results_dict = {row[0]: {'average_rating': row[1], 'num_ratings': row[2]} for row in results}

    sorted_results = sort_results(results_dict)

    return render_template('results.html', results=sorted_results)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        student = request.form['student']
        student_id = request.form['student_id']
        lecturer = request.form['lecturer']
        rating = request.form['rating']
        comments = request.form['comments']

        # Validate the input data
        if not student or not lecturer or not rating:
            return render_template('index.html', message='Please enter required fields')

        # Check if the student has already submitted feedback for the lecturer
        existing_feedback = Feedback.query.filter_by(student_id=student_id, lecturer=lecturer).first()
        if existing_feedback:
            return render_template('index.html', message='You have already submitted feedback for this lecturer')

        # Save the feedback to the database
        feedback = Feedback(student=student, student_id=student_id, lecturer=lecturer, rating=rating, comments=comments)
        db.session.add(feedback)
        db.session.commit()

        # Redirect the user to the success page
        return render_template('success.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)