from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Replace 'username', 'password', 'localhost', and 'dbname' with your actual credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Gunjan2005@localhost/eventease'
app.secret_key = 'your_secret_key'  # Make sure to set a secret key for session management
db = SQLAlchemy(app)

# Setting up login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models for EventEase
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))
    role = db.Column(db.String(20))  # 'attendee' or 'organizer'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.String(50))
    location = db.Column(db.String(100))
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    organizer = db.relationship('User', backref='organized_events')

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    user = db.relationship('User', backref='bookings')
    event = db.relationship('Event', backref='attendees')

# Routes
@app.route('/')
def index():
    events = Event.query.all()
    return render_template('index.html', events=events)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Please login.", "warning")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", "danger")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "warning")
    return redirect(url_for('login'))

@app.route('/create_event', methods=['POST', 'GET'])
@login_required
def create_event():
    if current_user.role != 'organizer':
        flash("You need to be an organizer to create events.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        date = request.form.get('date')
        location = request.form.get('location')
        
        new_event = Event(name=name, description=description, date=date, location=location, organizer=current_user)
        db.session.add(new_event)
        db.session.commit()
        flash("Event created successfully.", "success")
        return redirect(url_for('index'))
    
    return render_template('create_event.html')

@app.route('/book_event/<int:event_id>')
@login_required
def book_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for('index'))

    booking = Booking(user_id=current_user.id, event_id=event.id)
    db.session.add(booking)
    db.session.commit()
    flash("You have successfully booked this event.", "success")
    return redirect(url_for('index'))

@app.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('my_bookings.html', bookings=bookings)

# Running the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This creates the tables only once, so place it in a main guard
    app.run(debug=True)
