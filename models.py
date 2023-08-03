from email.policy import default
from xml.dom.pulldom import default_bufsize
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_login import UserMixin
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.app_context().push()
migrate = Migrate(app, db)
app.config['PRODUCT_IMAGE_FOLDER'] = 'static/uploads/product_images'



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    is_admin = db.Column(db.Integer ,default=0)
    cart = db.relationship('Cart', backref='user', uselist=False)
    orders = db.relationship('Order', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    products = db.relationship('Product', backref='category', lazy=True)
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    price = db.Column(db.Float)
    photo = db.Column(db.String(255))
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    quantity = db.Column(db.Integer)
    quantity_unit = db.Column(db.String(10))
    number  = db.Column(db.Integer)
    timestamp_added = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', secondary='cart_products', backref='cart', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', secondary='order_products', backref='order', lazy=True)
 


class CartProducts(db.Model):
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)



class OrderProducts(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)