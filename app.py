from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db = SQLAlchemy(app)

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

@app.route('/')
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
        # Create the SQLite database file if not exists and initialize tables
        db.create_all()
    app.run(debug=True)

