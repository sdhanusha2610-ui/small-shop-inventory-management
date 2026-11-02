from functools import wraps
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from sqlalchemy import func
from app.models import db, User, Product, Sale, StockHistory
from app.services.stock_service import (
    create_product_with_initial_stock,
    process_sale,
    process_restock
)

routes = Blueprint('routes', __name__)


def login_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please sign in to access this page.', 'warning')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# 1. Health Check Endpoint (For AWS ALB / SSM / CI-CD)
# -------------------------------------------------------------
@routes.route('/health', methods=['GET'])
def health_check():
    """System health check endpoint for monitoring & deployment validation."""
    db_status = "connected"
    try:
        db.session.execute(func.now()).scalar()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return jsonify({
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": "shop-inventory-system",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status
    }), 200 if "unhealthy" not in db_status else 503


# -------------------------------------------------------------
# 2. Authentication Routes
# -------------------------------------------------------------
@routes.route('/login', methods=['GET', 'POST'])
def login():
    """User login handler."""
    if session.get('user_id'):
        return redirect(url_for('routes.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@routes.route('/logout', methods=['GET'])
def logout():
    """Clear session and log user out."""
    session.clear()
    flash('You have been safely signed out.', 'info')
    return redirect(url_for('routes.login'))


# -------------------------------------------------------------
# 3. Dashboard Route
# -------------------------------------------------------------
@routes.route('/')
@routes.route('/dashboard')
@login_required
def dashboard():
    """Renders main dashboard with telemetry metrics & low stock table."""
    total_products = Product.query.count()
    total_units = db.session.query(func.coalesce(func.sum(Product.quantity), 0)).scalar()

    # Filter low-stock products (quantity <= min_stock_level)
    low_stock_items = Product.query.filter(Product.quantity <= Product.min_stock_level).all()
    low_stock_count = len(low_stock_items)

    # Today's sales metrics
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_revenue = db.session.query(func.coalesce(func.sum(Sale.total_price), 0.00))\
        .filter(Sale.sale_date >= today_start).scalar()
    today_sales_count = Sale.query.filter(Sale.sale_date >= today_start).count()

    # Recent sales activity (latest 8)
    recent_sales_raw = Sale.query.order_by(Sale.sale_date.desc()).limit(8).all()
    recent_sales = []
    for s in recent_sales_raw:
        recent_sales.append({
            'id': s.id,
            'sale_date': s.sale_date,
            'product_name': s.product.name if s.product else 'Unknown',
            'quantity_sold': s.quantity_sold,
            'unit_price': float(s.unit_price),
            'total_price': float(s.total_price),
            'cashier_name': s.cashier.username if s.cashier else 'Admin'
        })

    return render_template(
        'dashboard.html',
        total_products=total_products,
        total_units=int(total_units),
        low_stock_count=low_stock_count,
        low_stock_items=low_stock_items,
        today_revenue=float(today_revenue),
        today_sales_count=today_sales_count,
        recent_sales=recent_sales
    )


# -------------------------------------------------------------
# 4. Product Management Routes
# -------------------------------------------------------------
@routes.route('/products')
@login_required
def products():
    """List all products in inventory."""
    all_products = Product.query.order_by(Product.name.asc()).all()
    categories = [cat[0] for cat in db.session.query(Product.category).distinct().all() if cat[0]]

    return render_template('products.html', products=all_products, categories=categories)


@routes.route('/products/add', methods=['POST'])
@login_required
def add_product():
    """Adds a new product to inventory with initial stock."""
    sku = request.form.get('sku', '').strip().upper()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price = request.form.get('price', 0.0)
    cost_price = request.form.get('cost_price', 0.0)
    quantity = request.form.get('quantity', 0)
    min_stock_level = request.form.get('min_stock_level', 5)

    if Product.query.filter_by(sku=sku).first():
        flash(f"Error: Product with SKU '{sku}' already exists.", 'danger')
        return redirect(url_for('routes.products'))

    try:
        create_product_with_initial_stock(
            sku=sku,
            name=name,
            category=category,
            price=float(price),
            cost_price=float(cost_price) if cost_price else 0.0,
            quantity=int(quantity),
            min_stock_level=int(min_stock_level),
            user_id=session.get('user_id')
        )
        flash(f"Product '{name}' added successfully!", 'success')
    except Exception as e:
        flash(f"Error adding product: {str(e)}", 'danger')

    return redirect(url_for('routes.products'))


@routes.route('/products/edit/<int:product_id>', methods=['POST'])
@login_required
def edit_product(product_id):
    """Edits product details and threshold settings."""
    product = Product.query.get_or_404(product_id)

    new_sku = request.form.get('sku', '').strip().upper()
    # Check if SKU is taken by another product
    existing = Product.query.filter_by(sku=new_sku).first()
    if existing and existing.id != product.id:
        flash(f"Error: SKU '{new_sku}' is already in use by another product.", 'danger')
        return redirect(url_for('routes.products'))

    try:
        product.sku = new_sku
        product.name = request.form.get('name', '').strip()
        product.category = request.form.get('category', '').strip()
        product.price = Decimal(str(request.form.get('price', product.price)))
        product.cost_price = Decimal(str(request.form.get('cost_price', product.cost_price or 0.00)))
        product.min_stock_level = int(request.form.get('min_stock_level', product.min_stock_level))

        # Re-evaluate low-stock flag if min threshold changed
        if product.quantity > product.min_stock_level:
            product.is_low_stock_notified = False

        db.session.commit()
        flash(f"Product '{product.name}' updated successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating product: {str(e)}", 'danger')

    return redirect(url_for('routes.products'))


@routes.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """Deletes a product from the database."""
    product = Product.query.get_or_404(product_id)
    try:
        product_name = product.name
        db.session.delete(product)
        db.session.commit()
        flash(f"Product '{product_name}' deleted successfully.", 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting product: {str(e)}", 'danger')

    return redirect(url_for('routes.products'))


@routes.route('/products/restock/<int:product_id>', methods=['POST'])
@login_required
def restock_product(product_id):
    """Adds stock to a product."""
    try:
        quantity_to_add = int(request.form.get('quantity_to_add', 0))
        notes = request.form.get('notes', '')

        result = process_restock(
            product_id=product_id,
            quantity_to_add=quantity_to_add,
            user_id=session.get('user_id'),
            notes=notes
        )

        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'danger')
    except Exception as e:
        flash(f"Restock error: {str(e)}", 'danger')

    # Return to previous page (dashboard or products)
    referrer = request.referrer or url_for('routes.products')
    return redirect(referrer)


# -------------------------------------------------------------
# 5. Sales Routes
# -------------------------------------------------------------
@routes.route('/sales')
@login_required
def sales():
    """Point of Sale interface & sales history."""
    available_products = Product.query.order_by(Product.name.asc()).all()
    sales_raw = Sale.query.order_by(Sale.sale_date.desc()).all()

    today_start = datetime.combine(date.today(), datetime.min.time())
    today_total = db.session.query(func.coalesce(func.sum(Sale.total_price), 0.00))\
        .filter(Sale.sale_date >= today_start).scalar()

    sales_list = []
    for s in sales_raw:
        sales_list.append({
            'id': s.id,
            'sale_date': s.sale_date,
            'product_name': s.product.name if s.product else 'Deleted Product',
            'product_sku': s.product.sku if s.product else 'N/A',
            'quantity_sold': s.quantity_sold,
            'unit_price': float(s.unit_price),
            'total_price': float(s.total_price),
            'cashier_name': s.cashier.username if s.cashier else 'Admin'
        })

    return render_template(
        'sales.html',
        available_products=available_products,
        sales=sales_list,
        today_total=float(today_total)
    )


@routes.route('/sales/record', methods=['POST'])
@login_required
def record_sale():
    """Records a customer purchase and executes low-stock checks."""
    try:
        product_id = int(request.form.get('product_id', 0))
        quantity = int(request.form.get('quantity', 0))

        result = process_sale(
            product_id=product_id,
            quantity_to_sell=quantity,
            user_id=session.get('user_id')
        )

        if result['success']:
            flash(result['message'], 'success')
            if result.get('sns_dispatched'):
                flash('⚠️ Low-stock threshold reached! AWS SNS Email notification has been dispatched.', 'warning')
        else:
            flash(result['message'], 'danger')
    except Exception as e:
        flash(f"Error processing sale: {str(e)}", 'danger')

    return redirect(url_for('routes.sales'))


# -------------------------------------------------------------
# 6. Stock History Audit Log Route
# -------------------------------------------------------------
@routes.route('/stock-history')
@login_required
def stock_history():
    """Audit log of all inventory changes."""
    history_records = StockHistory.query.order_by(StockHistory.recorded_at.desc()).all()

    formatted_history = []
    for entry in history_records:
        formatted_history.append({
            'id': entry.id,
            'recorded_at': entry.recorded_at,
            'product_name': entry.product.name if entry.product else 'Unknown',
            'product_sku': entry.product.sku if entry.product else 'N/A',
            'change_type': entry.change_type,
            'quantity_change': entry.quantity_change,
            'resulting_quantity': entry.resulting_quantity,
            'username': entry.initiated_by.username if entry.initiated_by else 'Admin',
            'notes': entry.notes
        })

    return render_template('stock_history.html', history=formatted_history)
