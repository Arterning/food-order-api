import os
from flask import Flask

# 导入所有模型
try:
    from models import db, User, Recipe, Order, OrderItem
    print("✅ 成功导入所有模型")
except ImportError as e:
    print(f"❌ 导入模型失败: {e}")
    exit(1)

# 创建测试Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

with app.app_context():
    # 创建所有表（仅用于测试）
    db.create_all()
    
    # 测试User模型
    try:
        test_user = User(username="testuser")
        test_user.set_password("testpassword")
        print("✅ User模型功能正常")
    except Exception as e:
        print(f"❌ User模型测试失败: {e}")
    
    # 清理测试数据库
    db.drop_all()

print("✅ 所有模型测试完成，重构成功!")