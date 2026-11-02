from app.models import Product, Sale, StockHistory


def test_sales_page_renders(auth_client, db_session):
    """Test that POS sales page renders with product options."""
    response = auth_client.get('/sales')
    assert response.status_code == 200
    assert b"Point of Sale" in response.data
    assert b"TEST-MILK" in response.data


def test_record_valid_sale_healthy_stock(auth_client, db_session):
    """Test a customer purchase where remaining stock stays above threshold."""
    prod = Product.query.filter_by(sku='TEST-MILK').first()
    assert prod.quantity == 10
    assert prod.min_stock_level == 5

    # Sell 2 units (Remaining = 8 > 5)
    response = auth_client.post('/sales/record', data={
        'product_id': prod.id,
        'quantity': '2'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Sale recorded successfully" in response.data

    updated_prod = Product.query.get(prod.id)
    assert updated_prod.quantity == 8
    assert updated_prod.is_low_stock_notified is False

    # Check sale record
    sale = Sale.query.filter_by(product_id=prod.id).first()
    assert sale is not None
    assert sale.quantity_sold == 2
    assert float(sale.total_price) == 7.00  # 2 * 3.50

    # Check stock history audit log
    history = StockHistory.query.filter_by(product_id=prod.id, change_type='SALE').first()
    assert history is not None
    assert history.quantity_change == -2
    assert history.resulting_quantity == 8


def test_sale_rejected_insufficient_stock(auth_client, db_session):
    """Test that customer purchase is rejected when requested quantity exceeds stock."""
    prod = Product.query.filter_by(sku='TEST-MILK').first()
    assert prod.quantity == 10

    # Request 25 units when only 10 in stock
    response = auth_client.post('/sales/record', data={
        'product_id': prod.id,
        'quantity': '25'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Insufficient stock" in response.data

    # Stock must remain unchanged
    updated_prod = Product.query.get(prod.id)
    assert updated_prod.quantity == 10


def test_low_stock_trigger_and_deduplication(auth_client, db_session):
    """Test low-stock alert triggers when stock drops <= min threshold, and avoids duplicate alerts."""
    prod = Product.query.filter_by(sku='TEST-MILK').first()
    assert prod.quantity == 10
    assert prod.min_stock_level == 5
    assert prod.is_low_stock_notified is False

    # 1. First Sale: Sell 6 units (Remaining: 4 <= 5) -> Should trigger alert
    response1 = auth_client.post('/sales/record', data={
        'product_id': prod.id,
        'quantity': '6'
    }, follow_redirects=True)

    assert response1.status_code == 200
    assert b"Low-stock threshold reached" in response1.data

    updated_prod = Product.query.get(prod.id)
    assert updated_prod.quantity == 4
    assert updated_prod.is_low_stock_notified is True  # Deduplication flag engaged!

    # 2. Second Sale: Sell 1 more unit (Remaining: 3) -> Should NOT trigger duplicate alert
    response2 = auth_client.post('/sales/record', data={
        'product_id': prod.id,
        'quantity': '1'
    }, follow_redirects=True)

    assert response2.status_code == 200
    assert b"Sale recorded successfully" in response2.data
    # Ensure duplicate alert message is absent
    assert b"Low-stock threshold reached" not in response2.data

    updated_prod = Product.query.get(prod.id)
    assert updated_prod.quantity == 3
    assert updated_prod.is_low_stock_notified is True


def test_restock_resets_low_stock_deduplication_flag(auth_client, db_session):
    """Test that restocking back above min_stock_level resets is_low_stock_notified to False."""
    prod = Product.query.filter_by(sku='TEST-MILK').first()
    # Force low stock state
    prod.quantity = 3
    prod.is_low_stock_notified = True
    db_session.commit()

    # Restock +10 units (New Qty: 13 > min 5)
    response = auth_client.post(f'/products/restock/{prod.id}', data={
        'quantity_to_add': '10'
    }, follow_redirects=True)

    assert response.status_code == 200
    updated_prod = Product.query.get(prod.id)
    assert updated_prod.quantity == 13
    assert updated_prod.is_low_stock_notified is False  # Reset for future alerts!
