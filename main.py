import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

# Import models and database from models.py
from models import db, User, Recipe, Order, OrderItem

# Load environment variables from .env file
load_dotenv()

# Get the absolute path of the directory where the script is located
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

# --- App Configuration ---
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key') # Added secret key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Authentication ---

def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Expected format: "Bearer <token>"
                token_type, token = auth_header.split()
                if token_type.lower() != 'bearer':
                    return jsonify({'message': 'Invalid token type'}), 401
            except ValueError:
                return jsonify({'message': 'Invalid authorization header format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        if current_user is None:
            return jsonify({'message': 'User not found!'}), 401

        # Pass the user object to the decorated function
        return f(current_user, *args, **kwargs)

    return decorated

# --- API Routes ---

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'New user created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Login route to get the API token and user information"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7) # Token expires in 7 days
    }, app.config['SECRET_KEY'], algorithm="HS256")

    # Return both token and user information
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })


@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the Food Order API!'})

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
@token_required
def delete_recipe(current_user, recipe_id):
    """Delete a recipe and its associated image file"""
    # Find the recipe by ID
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check if there's an associated image file to delete
    if recipe.image:
        try:
            # Extract the filename from the URL
            # The URL format is typically http(s)://host/uploads/filename
            import re
            filename_match = re.search(r'/uploads/(.+)$', recipe.image)
            if filename_match:
                filename = filename_match.group(1)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Delete the file if it exists
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            # Log the error but continue with recipe deletion
            print(f"Error deleting image file: {e}")
    
    # Delete the recipe from the database
    db.session.delete(recipe)
    db.session.commit()
    
    return jsonify({'message': 'Recipe deleted successfully'}), 200

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT', 'GET'])
@token_required
def update_recipe(current_user, recipe_id):
    """Get a recipe by ID"""
    # Find the recipe by ID
    recipe = Recipe.query.get_or_404(recipe_id)
    if request.method == 'GET':
        return jsonify(recipe.to_dict()), 200
        
    """Update an existing recipe"""
    
    # Get the JSON data from the request
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update the recipe fields if provided in the request
    if 'name' in data:
        recipe.name = data['name']
    if 'category' in data:
        recipe.category = data['category']
    if 'ingredients' in data:
        recipe.ingredients = data['ingredients']
    if 'image' in data:
        recipe.image = data['image']
    
    # Commit the changes to the database
    db.session.commit()
    
    # Return the updated recipe
    return jsonify(recipe.to_dict()), 200

@app.route('/api/recipes', methods=['POST'])
@token_required
def create_recipe(current_user):
    """Create a new recipe"""
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'category', 'ingredients']):
        return jsonify({'error': 'Missing data'}), 400

    new_recipe = Recipe(
        name=data['name'],
        category=data['category'],
        ingredients=data['ingredients'],
        image=data.get('image', '') # Image is optional
    )
    db.session.add(new_recipe)
    db.session.commit()
    return jsonify(new_recipe.to_dict()), 201

@app.route('/api/recipes', methods=['GET'])
@token_required
def get_recipes(current_user):
    """Get all recipes"""
    recipes = Recipe.query.all()
    return jsonify([recipe.to_dict() for recipe in recipes])

@app.route('/api/orders', methods=['POST'])
@token_required
def create_order(current_user):
    """Create a new order"""
    data = request.get_json()
    # Expected data format: {'recipe_ids': [1, 2, 3]}
    if not data or 'recipe_ids' not in data or not isinstance(data['recipe_ids'], list):
        return jsonify({'error': 'Invalid data. Expected a list of recipe_ids.'}), 400

    new_order = Order(
        status='pending',
        user_id=current_user.id,
        username=current_user.username
    )
    
    for recipe_id in data['recipe_ids']:
        recipe = Recipe.query.get(recipe_id)
        if recipe:
            order_item = OrderItem(order=new_order, recipe=recipe)
            db.session.add(order_item)
        else:
            # If a recipe_id is invalid, we can choose to fail the whole order
            return jsonify({'error': f'Recipe with id {recipe_id} not found.'}), 400

    db.session.add(new_order)
    db.session.commit()
    return jsonify(new_order.to_dict()), 201

@app.route('/api/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    """Get all orders"""
    orders = Order.query.order_by(Order.id.desc()).all()
    return jsonify([order.to_dict() for order in orders])

@app.route('/api/orders/<int:order_id>/complete', methods=['PUT'])
@token_required
def complete_order(current_user, order_id):
    """Mark an order as completed"""
    order = Order.query.get_or_404(order_id)
    order.status = 'completed'
    db.session.commit()
    return jsonify(order.to_dict())

@app.route('/api/users/me', methods=['PUT', 'GET'])
@token_required
def update_user(current_user):
    """Update current user's information"""
    if request.method == 'GET':
        return jsonify(current_user.to_dict()), 200
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update username if provided
    if 'username' in data:
        new_username = data['username'].strip()
        if not new_username:
            return jsonify({'error': 'Username cannot be empty'}), 400
        
        # Check if username is already taken by another user
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'error': 'Username already exists'}), 409
        
        current_user.username = new_username
    
    # Update password if provided
    if 'password' in data:
        new_password = data['password']
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        current_user.set_password(new_password)
    
    # Update avatar URL if provided
    if 'avatar_url' in data:
        current_user.avatar_url = data['avatar_url']
    
    try:
        db.session.commit()
        return jsonify(current_user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user information'}), 500

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """Upload a file and return its URL"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        # Sanitize filename and make it unique
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        
        # Save the file
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        
        # 确定使用的协议（HTTP或HTTPS）
        # 首先检查X-Forwarded-Proto头，这是代理服务器传递的原始协议
        protocol = request.headers.get('X-Forwarded-Proto', 'http')
        
        # 构建URL时使用正确的协议
        host_with_protocol = protocol + '://' + request.host
        file_url = host_with_protocol + '/api/uploads/' + unique_filename
        
        return jsonify({'url': file_url})
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- Main Execution ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables if they don't exist

        # Check if both tables are empty before seeding
        if Recipe.query.count() == 0 and User.query.count() == 0:
            print("Database is empty. Seeding initial data...")
            try:
                # Get the absolute path to the SQL file
                sql_file_path = os.path.join(basedir, 'sql', 'init.sql')
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    # Execute the SQL script line by line
                    from sqlalchemy import text
                    for statement in f.read().split(';'):
                        if statement.strip():
                            db.session.execute(text(statement))
                    db.session.commit()
                print("Data seeding successful.")
            except Exception as e:
                print(f"Error seeding data: {e}")
                db.session.rollback()

    app.run(debug=True, host='0.0.0.0', port=8080)