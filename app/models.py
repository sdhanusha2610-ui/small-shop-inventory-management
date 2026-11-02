from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Represents a shop owner or cashier authorized to manage inventory."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), default='Admin', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sales = db.relationship('Sale', backref='cashier', lazy=True)
    stock_movements = db.relationship('StockHistory', backref='initiated_by', lazy=True)

    def set_password(self, password: str):
        """Hash and store the user's password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the plain text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Product(db.Model):
    """Represents an inventory item tracked by the system."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), default=0.00, nullable=True)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    min_stock_level = db.Column(db.Integer, default=5, nullable=False)
    is_low_stock_notified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    sales = db.relationship('Sale', backref='product', lazy=True, cascade='all, delete-orphan')
    stock_history = db.relationship('StockHistory', backref='product', lazy=True, cascade='all, delete-orphan')

    @property
    def is_low_stock(self) -> bool:
        """Checks if product is at or below minimum threshold."""
        return self.quantity <= self.min_stock_level

    @property
    def is_out_of_stock(self) -> bool:
        """Checks if product quantity is 0 or less."""
        return self.quantity <= 0

    def __repr__(self):
        return f"<Product {self.sku}: {self.name} (Qty: {self.quantity}, Min: {self.min_stock_level})>"


class Sale(db.Model):
    """Represents a customer purchase order."""
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    quantity_sold = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<Sale #{self.id}: Product {self.product_id} x {self.quantity_sold} = ${self.total_price}>"


class StockHistory(db.Model):
    """Immutable audit trail of all inventory movements."""
    __tablename__ = 'stock_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    change_type = db.Column(db.String(20), nullable=False)  # 'INITIAL', 'SALE', 'RESTOCK', 'ADJUSTMENT'
    quantity_change = db.Column(db.Integer, nullable=False)  # Negative for sales, Positive for restock
    resulting_quantity = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<StockHistory #{self.id}: Product {self.product_id} {self.change_type} {self.quantity_change} -> {self.resulting_quantity}>"
