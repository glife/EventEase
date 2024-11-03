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
    def get_id(self):
        return str(self.UserID)  # Return the UserID as a string


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
    Price = db.Column(db.Integer)

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
@app.route('/')
def index():
    events = Event.query.all()
    return render_template('homepage.html', events=events)

@app.route('/vendor_signup', methods=['POST', 'GET'])
def vendor_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        vendor_type = request.form.get('vendor_type')
        price_per_hour = request.form.get('price_per_hour')
        phone = request.form.get('phone')

        user_type = 'Vendor'

        existing_user = User.query.filter_by(Email=email).first()
        if existing_user:
            flash("Email already exists. Please login.", "warning")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        
        new_user = User(Name=name, Email=email, Password=hashed_password, UserType=user_type, Phone=phone)
        db.session.add(new_user)
        db.session.commit()

        new_vendor = Vendor(UserID=new_user.UserID, BookingStatus='Available', VendorType=vendor_type, PricePerHour=price_per_hour)
        db.session.add(new_vendor)

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

        flash("Vendor registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('vendor_signup.html')

@app.route('/organizer_signup', methods=['GET', 'POST'])
def organizer_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        organization_name = request.form.get('organization_name')
        event_specialty = request.form.get('event_specialty')
        phone = request.form.get('phone')
        user_type = 'Organizer'

        existing_user = User.query.filter_by(Email=email).first()
        if existing_user:
            flash("Email already exists. Please log in.", "warning")
            return redirect(url_for('login'))

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

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(Email=email).first()

        if user and check_password_hash(user.Password, password):
            login_user(user)
            flash("Login successful.", "success")
        
            # Redirect to specific dashboard based on user type
            if user.UserType == 'Organizer':
                return redirect(url_for('organizer_dashboard'))
            elif user.UserType == 'Vendor':
                return redirect(url_for('vendor_dashboard'))
        else:
            flash("Invalid credentials.", "danger")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "warning")
    return redirect(url_for('login'))

@app.route('/organizer_dashboard')
@login_required
def organizer_dashboard():
    if current_user.UserType != 'Organizer':
        flash("Access denied. You are not an Organizer.", "danger")
        return redirect(url_for('index'))
    # Fetch events managed by the organizer
    events = Event.query.filter_by(OrganizerID=current_user.UserID).all()
    return render_template('organizer.html', events=events)

@app.route('/vendor_dashboard')
@login_required
def vendor_dashboard():
    if current_user.UserType != 'Vendor':
        flash("Access denied. You are not a Vendor.", "danger")
        return redirect(url_for('index'))

    # Fetch bookings for the vendor
    bookings = EventVendor.query.filter_by(VendorID=current_user.UserID).all()
    booked_events = [Event.query.get(booking.EventID) for booking in bookings]
    return render_template('vendor.html', bookings=booked_events)

@app.route('/create_event', methods=['POST', 'GET'])
@login_required
def create_event():
    if current_user.UserType != 'Organizer':
        flash("You need to be an organizer to create events.", "danger")
        return redirect(url_for('index'))

    venues = Venue.query.all()  # Retrieve available venues

    if request.method == 'POST':
        name = request.form.get('name')
        type = request.form.get('type')
        location = request.form.get('location')
        event_date = request.form.get('date')
        budget = float(request.form.get('budget'))
        venue_id = request.form.get('venue_id')
        
        # Retrieve the selected venue's price
        venue = Venue.query.get(venue_id)
        if venue and budget < venue.Price:
            flash(f"Error: Budget must be at least ₹{venue.Price} for the selected venue.", "danger")
            return render_template('create_event.html', venues=venues)
        
        new_event = Event(
            Name=name,
            Type=type,
            Location=location,
            Date=event_date,
            Budget=budget,
            VenueID=venue_id,
            OrganizerID=current_user.UserID
        )
        
        db.session.add(new_event)
        db.session.commit()
        flash("Event created successfully.", "success")
        return redirect(url_for('organizer_dashboard'))

    return render_template('create_event.html', venues=venues)

from flask import flash, redirect, url_for, request, render_template

@app.route('/hire_vendors/<int:event_id>', methods=['GET', 'POST'])
def hire_vendors(event_id):
    if request.method == 'POST':
        # Get the selected vendor IDs from the form
        selected_vendor_ids = request.form.getlist('vendor_ids')

        # Update the BookingStatus of the selected vendors to 'Booked'
        for vendor_id in selected_vendor_ids:
            vendor = Vendor.query.filter_by(UserID=vendor_id).first()
            if vendor:
                vendor.BookingStatus = 'Booked'  # Change status
                db.session.commit()  # Commit the changes to the database

        # Flash success message
        flash("Vendors Hired!", "success")

        # Redirect to the organizer dashboard or another page
        return redirect(url_for('organizer_dashboard'))  # Adjust as needed

    # Query to get vendors with their specific types
    vendors = db.session.query(Vendor).all()  # Adjust as needed to filter by event_id

    # Create a list to hold the vendor data with their specific attributes
    vendor_list = []
    for vendor in vendors:
        vendor_data = {
            'UserID': vendor.UserID,
            'BookingStatus': vendor.BookingStatus,
            'VendorType': vendor.VendorType,
            'PricePerHour': vendor.PricePerHour
        }
        
        # Retrieve specific attributes based on vendor type
        if vendor.VendorType == 'performer':
            performer = db.session.query(Performer).filter_by(VendorID=vendor.UserID).first()
            if performer:
                vendor_data['PerformanceType'] = performer.PerformanceType
        elif vendor.VendorType == 'caterer':
            caterer = db.session.query(Caterer).filter_by(VendorID=vendor.UserID).first()
            if caterer:
                vendor_data['CuisineType'] = caterer.CuisineType
        elif vendor.VendorType == 'decorator':
            decorator = db.session.query(Decorator).filter_by(VendorID=vendor.UserID).first()
            if decorator:
                vendor_data['DecorationStyle'] = decorator.DecorationStyle
        
        vendor_list.append(vendor_data)

    return render_template('hire_vendors.html', vendors=vendor_list, event_id=event_id)

    
@app.route('/my_bookings', methods=['GET'])
@login_required
def my_bookings():
    events = Event.query.filter_by(OrganizerID=current_user.UserID).all()
    return render_template('my_bookings.html', events=events)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        organizer_id = request.form.get('organizer_id')
        vendor_id = request.form.get('vendor_id')
        review = request.form.get('review')
        rating = request.form.get('rating')

        new_feedback = Feedback(OrganizerID=organizer_id, VendorID=vendor_id, Review=review, Rating=rating)
        db.session.add(new_feedback)
        db.session.commit()
        flash("Feedback submitted successfully.", "success")
        return redirect(url_for('index'))

    vendors = Vendor.query.all()
    return render_template('feedback.html', vendors=vendors)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
