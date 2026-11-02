from app.models import Product, StockHistory


def test_products_page_renders(auth_client, db_session):
    """Test that products page lists seeded products."""
    response = auth_client.get('/products')
    assert response.status_code == 200
    assert b"TEST-MILK" in response.data
    assert b"Test Whole Milk 1L" in response.data


def test_add_new_product_success(auth_client, db_session):
    """Test adding a brand new product to inventory."""
    response = auth_client.post('/products/add', data={
        'sku': 'TEST-BREAD',
        'name': 'Artisan Sourdough Bread',
        'category': 'Bakery',
        'price': '4.25',
        'cost_price': '2.10',
        'quantity': '20',
        'min_stock_level': '5'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Artisan Sourdough Bread" in response.data
    assert b"added successfully" in response.data

    # Verify in DB
    product = Product.query.filter_by(sku='TEST-BREAD').first()
    assert product is not None
    assert product.quantity == 20
    assert float(product.price) == 4.25

    # Verify initial stock history was created
    history = StockHistory.query.filter_by(product_id=product.id, change_type='INITIAL').first()
    assert history is not None
    assert history.quantity_change == 20


def test_add_duplicate_sku_rejected(auth_client, db_session):
    """Test that adding a product with an existing SKU is rejected."""
    response = auth_client.post('/products/add', data={
        'sku': 'TEST-MILK',  # Already exists in conftest.py
        'name': 'Duplicate Milk',
        'category': 'Dairy',
        'price': '3.99',
        'cost_price': '2.00',
        'quantity': '10',
        'min_stock_level': '5'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"already exists" in response.data


def test_edit_product_success(auth_client, db_session):
    """Test editing an existing product's details."""
    prod = Product.query.filter_by(sku='TEST-MILK').first()

    response = auth_client.post(f'/products/edit/{prod.id}', data={
        'sku': 'TEST-MILK-UPDATED',
        'name': 'Test Organic Whole Milk 1L',
        'category': 'Organic Dairy',
        'price': '3.99',
        'cost_price': '2.25',
        'min_stock_level': '6'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"updated successfully" in response.data

    updated_prod = Product.query.get(prod.id)
    assert updated_prod.sku == 'TEST-MILK-UPDATED'
    assert updated_prod.name == 'Test Organic Whole Milk 1L'
    assert float(updated_prod.price) == 3.99
    assert updated_prod.min_stock_level == 6


def test_restock_product_success(auth_client, db_session):
    """Test restocking an item increases quantity and writes audit entry."""
    prod = Product.query.filter_by(sku='TEST-MILK').first()
    initial_qty = prod.quantity

    response = auth_client.post(f'/products/restock/{prod.id}', data={
        'quantity_to_add': '15',
        'notes': 'Weekly restock shipment #402'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Added 15 units" in response.data

    updated_prod = Product.query.get(prod.id)
    assert updated_prod.quantity == initial_qty + 15

    # Verify RESTOCK audit log
    history = StockHistory.query.filter_by(product_id=prod.id, change_type='RESTOCK').first()
    assert history is not None
    assert history.quantity_change == 15
    assert history.resulting_quantity == initial_qty + 15


def test_delete_product_success(auth_client, db_session):
    """Test deleting a product removes it from database."""
    prod = Product.query.filter_by(sku='TEST-MILK').first()
    prod_id = prod.id

    response = auth_client.post(f'/products/delete/{prod_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"deleted successfully" in response.data

    assert Product.query.get(prod_id) is None
