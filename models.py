from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta

# Initialize the database object (to be used by the application)
db = SQLAlchemy()

class User(db.Model):
    """User Model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True) # URL to the avatar image

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'avatar_url': self.avatar_url
        }


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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))), onupdate=lambda: datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))))

    def to_dict(self):
        # 收集所有订单中菜品的配料并去重
        all_ingredients = set()
        
        for item in self.items:
            if item.recipe and item.recipe.ingredients:
                # 分割配料（支持空格或逗号分隔）
                ingredients = []
                if ',' in item.recipe.ingredients:
                    ingredients = [ing.strip() for ing in item.recipe.ingredients.split(',')]
                else:
                    ingredients = item.recipe.ingredients.split()
                
                # 添加到集合中自动去重
                for ingredient in ingredients:
                    if ingredient:  # 忽略空字符串
                        all_ingredients.add(ingredient)
        
        return {
            'id': self.id,
            'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'all_ingredients': list(all_ingredients)  # 转换为列表返回
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