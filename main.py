import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid

# Get the absolute path of the directory where the script is located
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

# --- App Configuration ---
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# --- Database Models ---

class Recipe(db.Model):
    """Recipe Model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), nullable=True) # URL to the image
    ingredients = db.Column(db.String(300), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'image': self.image,
            'ingredients': self.ingredients
        }

class Order(db.Model):
    """Order Model"""
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default='pending') # e.g., pending, completed
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    """OrderItem Model"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe')

    def to_dict(self):
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'recipe_name': self.recipe.name if self.recipe else 'N/A'
        }


# --- API Routes ---

@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the Food Order API!'})

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
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
def get_recipes():
    """Get all recipes"""
    recipes = Recipe.query.all()
    return jsonify([recipe.to_dict() for recipe in recipes])

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    data = request.get_json()
    # Expected data format: {'recipe_ids': [1, 2, 3]}
    if not data or 'recipe_ids' not in data or not isinstance(data['recipe_ids'], list):
        return jsonify({'error': 'Invalid data. Expected a list of recipe_ids.'}), 400

    new_order = Order(status='pending')
    
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
def get_orders():
    """Get all orders"""
    orders = Order.query.order_by(Order.id.desc()).all()
    return jsonify([order.to_dict() for order in orders])

@app.route('/api/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    """Mark an order as completed"""
    order = Order.query.get_or_404(order_id)
    order.status = 'completed'
    db.session.commit()
    return jsonify(order.to_dict())

@app.route('/api/upload', methods=['POST'])
def upload_file():
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
        
        # Construct the URL
        file_url = request.host_url.rstrip('/') + '/uploads/' + unique_filename
        return jsonify({'url': file_url})
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- Main Execution ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create database tables if they don't exist

        # Check if the recipe table is empty
        if Recipe.query.count() == 0:
            print("Database is empty. Seeding initial data...")
            try:
                # Get the absolute path to the SQL file
                sql_file_path = os.path.join(basedir, 'sql', 'init.sql')
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    # Execute the SQL script
                    from sqlalchemy import text
                    db.session.execute(text(f.read()))
                    db.session.commit()
                print("Data seeding successful.")
            except Exception as e:
                print(f"Error seeding data: {e}")
                db.session.rollback()

    app.run(debug=True)