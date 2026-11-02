#!/usr/bin/env python3
"""Database Initialization and Seeding Script for Small Shop Inventory System.

Can be run:
1. Locally to initialize development SQLite database:
   python scripts/init_db.py

2. Against Amazon RDS MySQL:
   DB_HOST=your-rds-endpoint.rds.amazonaws.com DB_USER=admin DB_PASSWORD=Secret python scripts/init_db.py
"""

import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, Product, Sale, StockHistory


def initialize_and_seed():
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)

    with app.app_context():
        print("=" * 60)
        print("DATABASE INITIALIZATION & SEEDING")
        print(f"Target Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("=" * 60)

        # 1. Create tables
        print("[1/4] Creating database tables...")
        db.create_all()
        print("  ✓ Tables created successfully.")

        # 2. Seed Admin User
        print("[2/4] Seeding administrator account...")
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                full_name='Store Administrator',
                role='Admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("  ✓ Created user: admin / admin123")
        else:
            print(f"  ✓ User 'admin' already exists (ID: {admin.id}).")

        # 3. Seed Products
        print("[3/4] Seeding inventory products...")
        sample_products = [
            {'sku': 'PRD-1001', 'name': 'Organic Whole Milk 1L', 'category': 'Dairy', 'price': 3.49, 'cost': 2.10, 'qty': 3, 'min': 5, 'notified': True},
            {'sku': 'PRD-1002', 'name': 'Sliced Brown Bread 400g', 'category': 'Bakery', 'price': 2.29, 'cost': 1.20, 'qty': 0, 'min': 8, 'notified': True},
            {'sku': 'PRD-1003', 'name': 'Basmati Rice 5kg', 'category': 'Grains', 'price': 14.99, 'cost': 9.50, 'qty': 28, 'min': 10, 'notified': False},
            {'sku': 'PRD-1004', 'name': 'Pure Arabica Coffee 250g', 'category': 'Beverages', 'price': 7.99, 'cost': 4.80, 'qty': 15, 'min': 5, 'notified': False},
            {'sku': 'PRD-1005', 'name': 'Extra Virgin Olive Oil 500ml', 'category': 'Pantry', 'price': 8.49, 'cost': 5.20, 'qty': 4, 'min': 6, 'notified': True},
            {'sku': 'PRD-1006', 'name': 'Himalayan Rock Salt 1kg', 'category': 'Pantry', 'price': 3.19, 'cost': 1.50, 'qty': 45, 'min': 12, 'notified': False},
            {'sku': 'PRD-1007', 'name': 'Dark Chocolate 70% 100g', 'category': 'Snacks', 'price': 2.99, 'cost': 1.40, 'qty': 20, 'min': 6, 'notified': False},
        ]

        seeded_products = {}
        for p_data in sample_products:
            prod = Product.query.filter_by(sku=p_data['sku']).first()
            if not prod:
                prod = Product(
                    sku=p_data['sku'],
                    name=p_data['name'],
                    category=p_data['category'],
                    price=Decimal(str(p_data['price'])),
                    cost_price=Decimal(str(p_data['cost'])),
                    quantity=p_data['qty'],
                    min_stock_level=p_data['min'],
                    is_low_stock_notified=p_data['notified']
                )
                db.session.add(prod)
                db.session.flush()

                # Add initial stock history entry
                history = StockHistory(
                    product_id=prod.id,
                    user_id=admin.id,
                    change_type='INITIAL',
                    quantity_change=p_data['qty'],
                    resulting_quantity=p_data['qty'],
                    notes='Starter inventory seed',
                    recorded_at=datetime.utcnow() - timedelta(days=5)
                )
                db.session.add(history)
                print(f"  + Added: {prod.sku} - {prod.name} (Stock: {prod.quantity}, Min: {prod.min_stock_level})")
            else:
                print(f"  ✓ {prod.sku} already exists.")
            seeded_products[p_data['sku']] = prod

        db.session.commit()

        # 4. Seed Past Sales Transactions
        print("[4/4] Seeding sample sales transactions...")
        if Sale.query.count() == 0:
            sample_sales = [
                {'sku': 'PRD-1001', 'qty': 4, 'days_ago': 2},
                {'sku': 'PRD-1003', 'qty': 2, 'hours_ago': 4},
                {'sku': 'PRD-1004', 'qty': 5, 'hours_ago': 2},
                {'sku': 'PRD-1005', 'qty': 4, 'hours_ago': 1},
            ]

            for s_data in sample_sales:
                prod = seeded_products.get(s_data['sku'])
                if prod:
                    sale_time = datetime.utcnow()
                    if 'days_ago' in s_data:
                        sale_time -= timedelta(days=s_data['days_ago'])
                    if 'hours_ago' in s_data:
                        sale_time -= timedelta(hours=s_data['hours_ago'])

                    total_price = prod.price * Decimal(str(s_data['qty']))
                    sale = Sale(
                        product_id=prod.id,
                        user_id=admin.id,
                        quantity_sold=s_data['qty'],
                        unit_price=prod.price,
                        total_price=total_price,
                        sale_date=sale_time
                    )
                    db.session.add(sale)

                    history = StockHistory(
                        product_id=prod.id,
                        user_id=admin.id,
                        change_type='SALE',
                        quantity_change=-s_data['qty'],
                        resulting_quantity=prod.quantity,
                        notes=f"Customer purchase of {s_data['qty']} units",
                        recorded_at=sale_time
                    )
                    db.session.add(history)

            db.session.commit()
            print("  ✓ Sample sales records created.")
        else:
            print("  ✓ Sales records already exist.")

        # Summary
        print("=" * 60)
        print("DATABASE SUMMARY:")
        print(f"  - Users:          {User.query.count()}")
        print(f"  - Products:       {Product.query.count()}")
        print(f"  - Sales Records:  {Sale.query.count()}")
        print(f"  - Audit Movements:{StockHistory.query.count()}")
        print("=" * 60)
        print("✓ Database ready for operation!")


if __name__ == '__main__':
    initialize_and_seed()
