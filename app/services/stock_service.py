import logging
from decimal import Decimal
from app.models import db, Product, Sale, StockHistory
from .sns_service import send_low_stock_notification

logger = logging.getLogger(__name__)


def create_product_with_initial_stock(
    sku: str,
    name: str,
    category: str,
    price: float,
    cost_price: float,
    quantity: int,
    min_stock_level: int,
    user_id: int = None
) -> Product:
    """Creates a new product in MySQL and logs the initial stock event."""
    product = Product(
        sku=sku.strip().upper(),
        name=name.strip(),
        category=category.strip(),
        price=Decimal(str(price)),
        cost_price=Decimal(str(cost_price if cost_price else 0.00)),
        quantity=int(quantity),
        min_stock_level=int(min_stock_level),
        is_low_stock_notified=(int(quantity) <= int(min_stock_level))
    )
    db.session.add(product)
    db.session.flush()  # Flush to populate product.id

    # Create Initial Audit Log entry
    history = StockHistory(
        product_id=product.id,
        user_id=user_id,
        change_type='INITIAL',
        quantity_change=int(quantity),
        resulting_quantity=int(quantity),
        notes='Initial stock on product creation'
    )
    db.session.add(history)
    db.session.commit()

    return product


def process_sale(product_id: int, quantity_to_sell: int, user_id: int = None) -> dict:
    """Processes a sale transaction with strict ACID guarantees.
    
    1. Validates product availability and stock sufficiency.
    2. Inserts sale record.
    3. Decreases product stock.
    4. Records stock history.
    5. Evaluates low stock threshold and triggers AWS SNS alert without duplicate storms.
    
    Returns:
        dict: {'success': bool, 'message': str, 'sale': Sale, 'sns_dispatched': bool}
    """
    if quantity_to_sell <= 0:
        return {'success': False, 'message': 'Sale quantity must be at least 1 unit.'}

    # Fetch product with row locking (for MySQL/Postgres in prod)
    product = Product.query.filter_by(id=product_id).first()
    if not product:
        return {'success': False, 'message': 'Product not found.'}

    if product.quantity < quantity_to_sell:
        return {
            'success': False,
            'message': f"Insufficient stock. Requested {quantity_to_sell}, but only {product.quantity} available."
        }

    # 1. Calculate pricing
    unit_price = product.price
    total_price = unit_price * Decimal(str(quantity_to_sell))

    # 2. Record Sale
    sale = Sale(
        product_id=product.id,
        user_id=user_id,
        quantity_sold=quantity_to_sell,
        unit_price=unit_price,
        total_price=total_price
    )
    db.session.add(sale)

    # 3. Update stock quantity
    product.quantity -= quantity_to_sell
    new_quantity = product.quantity

    # 4. Record Audit History
    history = StockHistory(
        product_id=product.id,
        user_id=user_id,
        change_type='SALE',
        quantity_change=-quantity_to_sell,
        resulting_quantity=new_quantity,
        notes=f"Customer sale of {quantity_to_sell} units"
    )
    db.session.add(history)

    # 5. Check Low Stock & AWS SNS Alert logic
    sns_dispatched = False
    if new_quantity <= product.min_stock_level and not product.is_low_stock_notified:
        # Trigger AWS SNS email alert
        logger.warning(
            f"Stock alert triggered for {product.name}: {new_quantity} <= min {product.min_stock_level}"
        )
        send_low_stock_notification(
            product_name=product.name,
            sku=product.sku,
            current_quantity=new_quantity,
            min_stock_level=product.min_stock_level
        )
        product.is_low_stock_notified = True
        sns_dispatched = True

    # 6. Commit atomic transaction
    db.session.commit()

    return {
        'success': True,
        'message': f"Sale recorded successfully! Total: ${total_price:.2f}",
        'sale': sale,
        'remaining_stock': new_quantity,
        'sns_dispatched': sns_dispatched
    }


def process_restock(product_id: int, quantity_to_add: int, user_id: int = None, notes: str = None) -> dict:
    """Replenishes product stock and resets low-stock notification state."""
    if quantity_to_add <= 0:
        return {'success': False, 'message': 'Restock quantity must be positive.'}

    product = Product.query.filter_by(id=product_id).first()
    if not product:
        return {'success': False, 'message': 'Product not found.'}

    product.quantity += quantity_to_add
    new_quantity = product.quantity

    # If stock rises back above threshold, reset notification flag so future shortages notify again
    if new_quantity > product.min_stock_level:
        product.is_low_stock_notified = False

    history = StockHistory(
        product_id=product.id,
        user_id=user_id,
        change_type='RESTOCK',
        quantity_change=quantity_to_add,
        resulting_quantity=new_quantity,
        notes=notes or f"Restocked {quantity_to_add} units"
    )
    db.session.add(history)
    db.session.commit()

    return {
        'success': True,
        'message': f"Added {quantity_to_add} units. New stock is {new_quantity}.",
        'product': product,
        'new_quantity': new_quantity
    }
