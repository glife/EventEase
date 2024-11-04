from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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

    event_vendors = db.relationship('EventVendor', cascade='all, delete-orphan', backref='event')


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

class EventLog(db.Model):
    __tablename__ = 'eventlog'
    
    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EventID = db.Column(db.Integer, nullable=False)
    Action = db.Column(db.Enum('created', 'modified', 'deleted'), nullable=False)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EventLog(LogID={self.LogID}, EventID={self.EventID}, Action={self.Action}, Timestamp={self.Timestamp})>"

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

    # Attach hired vendors to each event
    for event in events:
        event.hired_vendors = [
            (vendor, vendor_name)  # Creates tuple for vendor object and name
            for vendor, vendor_name in db.session.query(Vendor, User.Name)
            .join(EventVendor, Vendor.UserID == EventVendor.VendorID)
            .join(User, Vendor.UserID == User.UserID)
            .filter(EventVendor.EventID == event.EventID)
            .all()
        ]

    return render_template('organizer.html', events=events)



@app.route('/vendor_dashboard')
@login_required
def vendor_dashboard():
    if current_user.UserType != 'Vendor':
        flash("Access denied. You are not a Vendor.", "danger")
        return redirect(url_for('index'))

    # Fetch bookings for the vendor and the related event and organizer details
    bookings = EventVendor.query.filter_by(VendorID=current_user.UserID).all()
    booked_events = []
    for booking in bookings:
        event = Event.query.get(booking.EventID)
        if event:
            # Fetch the organizer details
            organizer = User.query.get(event.OrganizerID)
            booked_events.append({
                'event': event,
                'organizer_name': organizer.Name if organizer else 'Unknown'
            })

    return render_template('vendor.html', booked_events=booked_events)



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


@app.route('/hire_vendors/<int:event_id>', methods=['GET', 'POST'])
@login_required  # Ensure only logged-in users can hire vendors
def hire_vendors(event_id):
    # Fetch the event and its budget
    event = Event.query.get(event_id)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for('organizer_dashboard'))

    if request.method == 'POST':
        # Get the selected vendor IDs from the form
        selected_vendor_ids = request.form.getlist('vendor_ids')

        # List to keep track of successful bookings and total cost
        successful_bookings = []
        total_cost = 0

        # Calculate the cumulative cost of selected vendors
        for vendor_id in selected_vendor_ids:
            vendor = Vendor.query.filter_by(UserID=vendor_id).first()
            if vendor:
                # Check if vendor is already booked
                if vendor.BookingStatus == 'Booked':
                    flash(f"Vendor {vendor_id} is already booked.", "warning")
                    continue

                # Add vendor's price to the total cost
                total_cost += vendor.PricePerHour

        # Check if the total cost exceeds the event budget
        if total_cost > event.Budget:
            flash("Hiring these vendors would exceed the event's budget. Please adjust your selection.", "danger")
            return redirect(url_for('hire_vendors', event_id=event_id))

        # Book vendors if within budget
        for vendor_id in selected_vendor_ids:
            vendor = Vendor.query.filter_by(UserID=vendor_id).first()
            if vendor:
                vendor.BookingStatus = 'Booked'
                db.session.commit()  # Commit status change

                # Create an entry in the EventVendor table
                event_vendor_entry = EventVendor(EventID=event_id, VendorID=vendor.UserID)
                db.session.add(event_vendor_entry)
                successful_bookings.append(vendor.UserID)

        db.session.commit()  # Commit all changes

        if successful_bookings:
            flash("Vendors hired successfully!", "success")
        else:
            flash("No vendors hired. Please check the vendor status.", "info")

        return redirect(url_for('organizer_dashboard'))

    # Query to get available vendors (not booked)
    vendors = Vendor.query.filter(Vendor.BookingStatus == 'Available').all()

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
            performer = Performer.query.filter_by(VendorID=vendor.UserID).first()
            if performer:
                vendor_data['PerformanceType'] = performer.PerformanceType
        elif vendor.VendorType == 'caterer':
            caterer = Caterer.query.filter_by(VendorID=vendor.UserID).first()
            if caterer:
                vendor_data['CuisineType'] = caterer.CuisineType
        elif vendor.VendorType == 'decorator':
            decorator = Decorator.query.filter_by(VendorID=vendor.UserID).first()
            if decorator:
                vendor_data['DecorationStyle'] = decorator.DecorationStyle

        vendor_list.append(vendor_data)

    return render_template('hire_vendors.html', vendors=vendor_list, event_id=event_id, event_budget=event.Budget)

@app.route('/update_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if current_user.UserType != 'Organizer' or event.OrganizerID != current_user.UserID:
        flash("Access denied.", "danger")
        return redirect(url_for('organizer_dashboard'))
    
    venues = Venue.query.all()
    
    if request.method == 'POST':
        event.Name = request.form.get('name')
        event.Type = request.form.get('type')
        event.Location = request.form.get('location')
        event.Date = request.form.get('date')
        event.Budget = float(request.form.get('budget'))
        venue_id = request.form.get('venue_id')
        
        # Validate budget against venue price
        venue = Venue.query.get(venue_id)
        if venue and event.Budget < venue.Price:
            flash(f"Budget must be at least ₹{venue.Price} for the selected venue.", "danger")
            return render_template('update_event.html', event=event, venues=venues)
        
        event.VenueID = venue_id
        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for('organizer_dashboard'))
    
    return render_template('update_event.html', event=event, venues=venues)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    print(f"Attempting to delete event with ID: {event_id}")  # Log event deletion attempt
    event = Event.query.get_or_404(event_id)

    if current_user.UserType != 'Organizer' or event.OrganizerID != current_user.UserID:
        print("Access denied for user.")  # Log access denial
        flash("Access denied.", "danger")
        return redirect(url_for('organizer_dashboard'))

    # Find all vendors associated with the event
    associated_vendors = EventVendor.query.filter_by(EventID=event.EventID).all()
    print(f"Associated vendors found: {len(associated_vendors)}")  # Log the number of vendors

    # Update the booking status of each associated vendor to "Available"
    for vendor in associated_vendors:
        print(f"Updating vendor {vendor.VendorID} status to 'Available'")  # Log vendor update
        
        # Get the actual vendor object from the Vendor table
        vendor_to_update = Vendor.query.filter_by(UserID=vendor.VendorID).first()
        
        if vendor_to_update:  # Check if the vendor was found
            print("Initial status: ", vendor_to_update.BookingStatus)  # Log initial status
            vendor_to_update.BookingStatus = 'Available'  # Update Booking Status
            print("Updated status: ", vendor_to_update.BookingStatus)  # Log updated status

    try:
        # Commit the changes for the booking status
        db.session.commit()
        print("Booking statuses updated successfully.")
    except Exception as e:
        print(f"Error updating booking statuses: {e}")  # Log error on status update
        db.session.rollback()  # Roll back in case of error
        flash("Error updating vendor status. Event not deleted.", "danger")
        return redirect(url_for('organizer_dashboard'))

    # Delete associated EventVendor records
    delete_count = EventVendor.query.filter_by(EventID=event.EventID).delete()
    print(f"Deleted {delete_count} associated EventVendor records.")  # Log how many were deleted

    try:
        # Now delete the event
        db.session.delete(event)
        db.session.commit()  # Commit changes after deleting the event
        flash("Event deleted successfully.", "success")
        print(f"Event with ID {event.EventID} deleted successfully.")  # Log successful deletion
    except Exception as e:
        print(f"Error deleting event: {e}")  # Log error on event deletion
        db.session.rollback()  # Roll back in case of error
        flash("Error deleting event.", "danger")
    
    return redirect(url_for('organizer_dashboard'))


@app.route('/confirm_delete_event/<int:event_id>')
@login_required
def confirm_delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user.UserType != 'Organizer' or event.OrganizerID != current_user.UserID:
        flash("Access denied.", "danger")
        return redirect(url_for('organizer_dashboard'))
    return render_template('delete_event.html', event=event)

@app.route('/event_logs')
@login_required
def event_logs():
    logs = EventLog.query.all()  # Fetch all logs
    return render_template('event_logs.html', logs=logs)

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
