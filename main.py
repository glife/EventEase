from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:SecureSQL_007@localhost/eventease'
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

# Setup for login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    UserID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(1000), nullable=False)
    UserType = db.Column(db.Enum('Organizer', 'Vendor'), nullable=False)
    Phone = db.Column(db.String(100))

    # Override get_id to return UserID
    def get_id(self):
        return str(self.UserID)

class UserProfile(db.Model):
    __tablename__ = 'User_Profile'
    ProfileID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False, unique=True)
    Gender = db.Column(db.Enum('Male', 'Female', 'Other'))
    Address = db.Column(db.String(255))
    DateOfBirth = db.Column(db.Date)

class Organizer(db.Model):
    __tablename__ = 'Organizer'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    OrganizationName = db.Column(db.String(100), nullable=False)
    EventSpecialty = db.Column(db.String(100))

class Vendor(db.Model):
    __tablename__ = 'Vendor'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    BookingStatus = db.Column(db.Enum('Available', 'Booked', 'Pending'), nullable=False)
    VendorType = db.Column(db.Enum('performer', 'caterer', 'decorator'), nullable=False)
    PricePerHour = db.Column(db.Numeric(10, 2))

class Decorator(db.Model):
    __tablename__ = 'decorator'
    VendorID = db.Column(db.Integer, primary_key=True)
    DecorationStyle = db.Column(db.String(100), nullable=True)

class Performer(db.Model):
    __tablename__ = 'performer'
    VendorID = db.Column(db.Integer, primary_key=True)
    PerformanceType = db.Column(db.String(100), nullable=True)

class Caterer(db.Model):
    __tablename__ = 'caterer'
    VendorID = db.Column(db.Integer, primary_key=True)
    CuisineType = db.Column(db.String(100), nullable=True)

class Event(db.Model):
    __tablename__ = 'Event'
    EventID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Type = db.Column(db.String(100))
    Date = db.Column(db.Date)
    Location = db.Column(db.String(255))
    Budget = db.Column(db.Numeric(10, 2))
    VenueID = db.Column(db.Integer, db.ForeignKey('Venue.VenueID'), nullable=True)
    OrganizerID = db.Column(db.Integer, db.ForeignKey('Organizer.UserID'), nullable=False)

class Venue(db.Model):
    __tablename__ = 'Venue'
    VenueID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    VenueName = db.Column(db.String(100), nullable=False)
    Location = db.Column(db.String(255))
    Capacity = db.Column(db.Integer)

class Feedback(db.Model):
    __tablename__ = 'Feedback'
    FeedbackID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OrganizerID = db.Column(db.Integer, db.ForeignKey('Organizer.UserID'), nullable=False)
    VendorID = db.Column(db.Integer, db.ForeignKey('Vendor.UserID'), nullable=False)
    Review = db.Column(db.Text)
    Rating = db.Column(db.Integer)

class EventVendor(db.Model):
    __tablename__ = 'EventVendor'
    EventID = db.Column(db.Integer, db.ForeignKey('Event.EventID'), primary_key=True)
    VendorID = db.Column(db.Integer, db.ForeignKey('Vendor.UserID'), primary_key=True)

# Routes
# Index Route
@app.route('/')
def index():
    events = Event.query.all()
    return render_template('index.html', events=events)

# Flask code for vendor_signup route
@app.route('/vendor_signup', methods=['POST', 'GET'])
def vendor_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        vendor_type = request.form.get('vendor_type')  # Added to get the vendor type
        price_per_hour = request.form.get('price_per_hour')  # Added to get price per hour
        phone = request.form.get('phone')  # Added to get price per hour

        user_type = 'Vendor'

        existing_user = User.query.filter_by(Email=email).first()
        if existing_user:
            flash("Email already exists. Please login.", "warning")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        
        # Create new user
        new_user = User(Name=name, Email=email, Password=hashed_password, UserType=user_type, Phone=phone)
        db.session.add(new_user)
        db.session.commit()

        # Create new vendor
        new_vendor = Vendor(UserID=new_user.UserID, BookingStatus='Available', VendorType=vendor_type, PricePerHour=price_per_hour)
        db.session.add(new_vendor)
        db.session.commit()

        # Check vendor type and insert into respective table
        if vendor_type == 'decorator':
            decoration_style = request.form.get('decoration_style')
            new_decorator = Decorator(VendorID=new_user.UserID, DecorationStyle=decoration_style)
            db.session.add(new_decorator)
        elif vendor_type == 'performer':
            performance_type = request.form.get('performance_type')
            new_performer = Performer(VendorID=new_user.UserID, PerformanceType=performance_type)
            db.session.add(new_performer)
        elif vendor_type == 'caterer':
            cuisine_type = request.form.get('cuisine_type')
            new_caterer = Caterer(VendorID=new_user.UserID, CuisineType=cuisine_type)
            db.session.add(new_caterer)

        db.session.commit()

        # Set the price per hour in the Vendor table
        new_vendor.PricePerHour = price_per_hour
        db.session.commit()

        flash("Vendor registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('vendor_signup.html')

# Organizer Signup Route
@app.route('/organizer_signup', methods=['GET', 'POST'])
def organizer_signup():
    if request.method == 'POST':
        # Gather data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        organization_name = request.form.get('organization_name')
        event_specialty = request.form.get('event_specialty')
        phone = request.form.get('phone')
        user_type = 'Organizer'

        # Check if user exists
        existing_user = User.query.filter_by(Email=email).first()
        if existing_user:
            flash("Email already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        # Create new user and organizer records
        hashed_password = generate_password_hash(password)
        new_user = User(Name=name, Email=email, Password=hashed_password, UserType=user_type, Phone=phone)
        db.session.add(new_user)
        db.session.commit()

        new_organizer = Organizer(UserID=new_user.UserID, OrganizationName=organization_name, EventSpecialty=event_specialty)
        db.session.add(new_organizer)
        db.session.commit()

        flash("Organizer registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('organizer_signup.html')


# Login Route
# Example of redirecting to my_bookings after login
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(Email=email).first()

        if user and check_password_hash(user.Password, password):
            login_user(user)
            flash("Login successful.", "success")
            #return "SUCCESS"
            return redirect(url_for('index'))  # Redirecting to my_bookings
        else:
            flash("Invalid credentials.", "danger")

    return render_template('login.html')


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "warning")
    return redirect(url_for('login'))

@app.route('/create_event', methods=['POST', 'GET'])
@login_required
def create_event():
    if current_user.UserType != 'Organizer':
        flash("You need to be an organizer to create events.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        type = request.form.get('type')
        location = request.form.get('location')
        date = request.form.get('date')
        budget = request.form.get('budget')
        venue_id = request.form.get('venue_id')

        new_event = Event(
            Name=name,
            Type=type,
            Location=location,
            Date=date,
            Budget=budget,
            VenueID=venue_id,
            OrganizerID=current_user.UserID
        )
        db.session.add(new_event)
        db.session.commit()
        flash("Event created successfully.", "success")
        return redirect(url_for('index'))

    return render_template('create_event.html')

@app.route('/my_bookings', methods=['GET'])
@login_required
def my_bookings():
    # Logic to retrieve and display the user's bookings
    # Example: bookings = Booking.query.filter_by(UserID=current_user.UserID).all()
    return render_template('my_bookings.html', bookings=bookings)

# Running the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
