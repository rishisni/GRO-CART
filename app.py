from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, url_for, redirect,flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from datetime import datetime
import os
from datetime import datetime
from sqlalchemy import desc,or_


from werkzeug.utils import secure_filename

login_manager = LoginManager()
login_manager.login_view = 'home'
login_manager.init_app(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','webp'}  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#User Loader To Load User
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

#------------------------------------------Routes-----------------------------------------------------------------


#Route For Homepage
@app.route('/')
def home():
    return render_template('home.html')


#Route For Register
# Route For Register
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method =="POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        # Check if the username or email already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user or existing_email:
            flash('Username or email already exists. Please choose a different one.', 'danger')
            return redirect('/register')

        new_user = User(username=username, password=password_hash,email=email)
        db.session.add(new_user)
        new_cart = Cart()
        new_user.cart = new_cart
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect('/login')
    return render_template('register.html')

    

#Route For Login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        identifier = request.form['identifier']
        password = request.form['password']
        user = User.query.filter((User.username == identifier) | (
            User.email == identifier)).first()
        if user and check_password_hash(user.password, password) and user.is_admin == 0:
            login_user(user)
            if not user.cart:
                new_cart = Cart()
                user.cart = new_cart
                db.session.commit()
            return redirect(url_for('dashboard'))
        elif user and check_password_hash(user.password, password) and user.is_admin == 1:
            flash('Manager login page. Please login through the manager login page.', 'warning')
        else:
            flash('Invalid username, email, or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')



# Route For Manager-Login
@app.route('/manager-login',methods=['GET','POST'])
def manager_login():
    if request.method == "POST":
        identifier = request.form['identifier']
        password = request.form['password']
        user = User.query.filter((User.username == identifier) | (
            User.email == identifier)).first()
        if user and check_password_hash(user.password, password) and user.is_admin == 1:
            login_user(user)
            return redirect(url_for('show_category'))
        elif user and check_password_hash(user.password, password) and user.is_admin == 0:
            flash('User login page. Please login through the user login page.', 'warning')
        else:
            flash('Invalid username, email, or password.', 'danger')
        return redirect(url_for('manager_login'))

    return render_template('manager_login.html')







@app.route('/dashboard')
@login_required
def dashboard():
    categories = Category.query.all()

    # Fetch products for each category and store them in a dictionary
    products_dict = {}
    for category in categories:
        # Get all products for the category and filter out expired products
        products = Product.query.filter_by(category_id=category.id).order_by(desc(Product.timestamp_added)).all()
        non_expired_products = [product for product in products if product.expiry_date >= datetime.now().date()]

        products_dict[category.id] = non_expired_products

    return render_template('dashboard.html', categories=categories, products_dict=products_dict)





#Route For Add Category 
@app.route('/add-category',methods=['GET','POST'])
@login_required
def add_category():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    if request.method =="POST":

        name = request.form['name']
        new_category =Category(name=name)
        db.session.add(new_category)
        db.session.commit()

        flash('Category added successfully.')

        return redirect(url_for('show_category'))

    return render_template('add_category.html',user=current_user)


#Route to Show Category
@app.route('/show-category')
@login_required
def show_category():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    categories = Category.query.all()
    return render_template('show_category.html', categories=categories)


# Route For Edit Category
@app.route('/edit-category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        category.name = name
        db.session.commit()

        flash('Category updated successfully.')

        return redirect(url_for('show_category'))

    return render_template('edit_category.html', user=current_user, category=category)


# Route For Delete Category
@app.route('/delete-category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    category = Category.query.get(category_id)

    
    products = Product.query.filter_by(category_id=category_id).all()
    for product in products:
        db.session.delete(product)

    db.session.delete(category)
    db.session.commit()
    flash('Category and associated products deleted successfully.')
    return redirect(url_for('show_category'))




@app.route('/add-product/<int:category_id>', methods=['GET', 'POST'])
@login_required
def add_product(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    category = Category.query.get(category_id)
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        manufacturing_date = datetime.strptime(request.form['manufacturing_date'], '%Y-%m-%d').date()
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        quantity = request.form['quantity']
        quantity_unit = request.form['quantity_unit']
        number = request.form['number']

       
        photo = request.files['photo']
        timestamp_added = datetime.now()
       
        if photo and allowed_file(photo.filename):
           
            filename = secure_filename(photo.filename)

            
            new_filename = f"{category_id}-{name}-{timestamp_added}.{filename.rsplit('.', 1)[1].lower()}"

            
            photo.save(os.path.join(app.config['PRODUCT_IMAGE_FOLDER'], new_filename))

            
            

            new_product = Product(name=name, price=price, manufacturing_date=manufacturing_date, expiry_date=expiry_date,
                                  category_id=category.id, quantity=quantity, quantity_unit=quantity_unit,
                                  photo=new_filename, number=number, timestamp_added=timestamp_added)
            db.session.add(new_product)
            db.session.commit()

            flash('Product added successfully.')
            return redirect(url_for('show_products',category_id=category_id))
    
    return render_template('add_product.html', category=category)

@app.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    product = Product.query.get(product_id)
    category_id = product.category_id
    if request.method == "POST":
        
        product.price = request.form['price']
       
        product.quantity = request.form['quantity']
        product.quantity_unit = request.form['quantity_unit']
        product.number = request.form['number']

        photo = request.files['photo']
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            timestamp_added = datetime.now()
            new_filename = f"{product.category_id}-{product.name}-{timestamp_added}.{filename.rsplit('.', 1)[1].lower()}"
            photo.save(os.path.join(app.config['PRODUCT_IMAGE_FOLDER'], new_filename))
            product.photo = new_filename

        db.session.commit()

        flash('Product edited successfully.')
        return redirect(url_for('show_products', category_id=category_id))

    return render_template('edit_product.html', product=product)


@app.route('/show-products/<int:category_id>')
@login_required
def show_products(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    category = Category.query.get(category_id)
    products = Product.query.filter_by(category_id=category_id).all()
    return render_template('show_products.html', category=category, products=products)



@app.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    product = Product.query.get(product_id)

    if not product:
        flash('Product not found.')
        return redirect(url_for('show_category'))

    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('show_products',category_id=product.category_id))



# Route to add a product to the cart
@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    current_user.cart.products.append(product)
    db.session.commit()
    flash('Product added to cart successfully.')
    return redirect(url_for('show_products', category_id=product.category_id))

# Route to remove a product from the cart
@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    product = Product.query.get(product_id)
    current_user.cart.products.remove(product)
    db.session.commit()
    flash('Product removed from cart successfully.')
    return redirect(url_for('show_cart'))

# Route to view the cart
@app.route('/cart')
@login_required
def show_cart():
    cart_products = current_user.cart.products
    total_price = sum(product.price for product in cart_products)
    return render_template('cart.html', cart_products=cart_products, total_price=total_price)





# Route to place an order
@app.route('/place-order', methods=['POST'])
@login_required
def place_order():
    cart_products = current_user.cart.products
    order = Order(user=current_user, products=cart_products)
    
    
    products_to_remove = []
    for product in cart_products:
        product.number -= 1
        products_to_remove.append(product)

   
    for product in products_to_remove:
        current_user.cart.products.remove(product)

    db.session.add(order)
    db.session.commit()
    
    flash('Order placed successfully.')
    return redirect(url_for('show_orders'))


# Route to view user's orders
@app.route('/my-orders')
@login_required
def show_orders():
    orders = current_user.orders

    
    for order in orders:
        order.total_price = sum(product.price for product in order.products)

    return render_template('orders.html', orders=orders)



# Route to Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Route to search products
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_products():
    if request.method == 'POST':
        search_query = request.form['search_query']
        
        products = Product.query.filter(or_(Product.name.ilike(f'%{search_query}%'),
                                            Product.category.has(Category.name.ilike(f'%{search_query}%')))
                                       ).all()
        
        if not current_user.is_admin:
            products = [product for product in products if not product.expiry_date or product.expiry_date >= datetime.now().date()]
        return render_template('search_results.html', products=products, search_query=search_query)
    return redirect('search')



@app.route('/summary')
@login_required
def summary():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    categories = Category.query.all()

    
    products_dict = {}
    for category in categories:
        
        products = Product.query.filter_by(category_id=category.id).order_by(desc(Product.timestamp_added)).all()
        non_expired_products = [product for product in products if product.expiry_date >= datetime.now().date()]

        products_dict[category.id] = non_expired_products
    most_purchased_product, total_purchases = get_most_purchased_product()

    
    out_of_stock_products, expired_products = get_out_of_stock_or_expired_products()

    return render_template('summary.html', categories=categories, products_dict=products_dict,
                           most_purchased_product=most_purchased_product, total_purchases=total_purchases,
                           out_of_stock_products=out_of_stock_products, expired_products=expired_products)



if __name__ == '__main__':
    app.run(debug=True,port=1045,host="0.0.0.0")