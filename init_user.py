import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the absolute path of the directory where the script is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Create Flask application for database operations
app = Flask(__name__)

# Configure the app with the same settings as main.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define User model (same as in main.py)
class User(db.Model):
    """User Model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)  # URL to the avatar image

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

# Function to create a new user
def create_user(username, password):
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"User '{username}' already exists!")
        return False
    
    # Create new user
    new_user = User(username=username)
    new_user.set_password(password)
    
    # Add to database
    db.session.add(new_user)
    db.session.commit()
    
    print(f"User '{username}' created successfully!")
    return True

# Main function to handle command line arguments
if __name__ == '__main__':
    # Check if command line arguments are provided
    if len(sys.argv) < 3:
        print("Usage: python init_user.py <username> <password>")
        sys.exit(1)
    
    # Extract username and password from command line arguments
    username = sys.argv[1]
    password = sys.argv[2]
    
    # Create the user within application context
    with app.app_context():
        # Ensure the database tables are created (in case this is the first run)
        db.create_all()
        create_user(username, password)