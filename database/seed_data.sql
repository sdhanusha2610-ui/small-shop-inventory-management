-- ==============================================================================
-- Small Shop Inventory Management System - Initial Starter Seed Data
-- ==============================================================================

USE inventory_db;

-- 1. Insert Default Administrator User (Password: admin123)
INSERT INTO users (id, username, password_hash, full_name, role)
VALUES (
    1,
    'admin',
    'pbkdf2:sha256:260000$static_salt_demo$9f21c1fdf1934a513683baaff53f155c506a24b2cb4ca90ccdb7b930812e2668',
    'Store Administrator',
    'Admin'
) ON DUPLICATE KEY UPDATE username=username;

-- 2. Insert Realistic Shop Inventory Products
INSERT INTO products (id, sku, name, category, price, cost_price, quantity, min_stock_level, is_low_stock_notified)
VALUES 
    (1, 'PRD-1001', 'Organic Whole Milk 1L', 'Dairy', 3.49, 2.10, 3, 5, TRUE),
    (2, 'PRD-1002', 'Sliced Brown Bread 400g', 'Bakery', 2.29, 1.20, 0, 8, TRUE),
    (3, 'PRD-1003', 'Basmati Rice 5kg', 'Grains', 14.99, 9.50, 28, 10, FALSE),
    (4, 'PRD-1004', 'Pure Arabica Coffee 250g', 'Beverages', 7.99, 4.80, 15, 5, FALSE),
    (5, 'PRD-1005', 'Extra Virgin Olive Oil 500ml', 'Pantry', 8.49, 5.20, 4, 6, TRUE),
    (6, 'PRD-1006', 'Himalayan Rock Salt 1kg', 'Pantry', 3.19, 1.50, 45, 12, FALSE),
    (7, 'PRD-1007', 'Dark Chocolate 70% 100g', 'Snacks', 2.99, 1.40, 20, 6, FALSE)
ON DUPLICATE KEY UPDATE sku=sku;

-- 3. Insert Initial Audit Log Entries in stock_history
INSERT INTO stock_history (product_id, user_id, change_type, quantity_change, resulting_quantity, notes, recorded_at)
VALUES
    (1, 1, 'INITIAL', 10, 10, 'Initial inventory setup', NOW() - INTERVAL 5 DAY),
    (2, 1, 'INITIAL', 15, 15, 'Initial inventory setup', NOW() - INTERVAL 5 DAY),
    (3, 1, 'INITIAL', 30, 30, 'Initial inventory setup', NOW() - INTERVAL 5 DAY),
    (4, 1, 'INITIAL', 20, 20, 'Initial inventory setup', NOW() - INTERVAL 5 DAY),
    (5, 1, 'INITIAL', 8, 8, 'Initial inventory setup', NOW() - INTERVAL 5 DAY),
    (6, 1, 'INITIAL', 50, 50, 'Initial inventory setup', NOW() - INTERVAL 5 DAY),
    (7, 1, 'INITIAL', 25, 25, 'Initial inventory setup', NOW() - INTERVAL 5 DAY);

-- 4. Insert Past Customer Sales Transactions
INSERT INTO sales (id, product_id, user_id, quantity_sold, unit_price, total_price, sale_date)
VALUES
    (1, 1, 1, 4, 3.49, 13.96, NOW() - INTERVAL 2 DAY),
    (2, 1, 1, 3, 3.49, 10.47, NOW() - INTERVAL 1 DAY),
    (3, 2, 1, 15, 2.29, 34.35, NOW() - INTERVAL 1 DAY),
    (4, 3, 1, 2, 14.99, 29.98, NOW() - INTERVAL 4 HOUR),
    (5, 4, 1, 5, 7.99, 39.95, NOW() - INTERVAL 2 HOUR),
    (6, 5, 1, 4, 8.49, 33.96, NOW() - INTERVAL 1 HOUR);

-- 5. Insert Corresponding Audit Logs for the Sales
INSERT INTO stock_history (product_id, user_id, change_type, quantity_change, resulting_quantity, notes, recorded_at)
VALUES
    (1, 1, 'SALE', -4, 6, 'Customer purchase #1', NOW() - INTERVAL 2 DAY),
    (1, 1, 'SALE', -3, 3, 'Customer purchase #2 (Triggered AWS SNS Low Stock)', NOW() - INTERVAL 1 DAY),
    (2, 1, 'SALE', -15, 0, 'Bulk purchase #3 (Out of Stock)', NOW() - INTERVAL 1 DAY),
    (3, 1, 'SALE', -2, 28, 'Customer purchase #4', NOW() - INTERVAL 4 HOUR),
    (4, 1, 'SALE', -5, 15, 'Customer purchase #5', NOW() - INTERVAL 2 HOUR),
    (5, 1, 'SALE', -4, 4, 'Customer purchase #6 (Triggered AWS SNS Low Stock)', NOW() - INTERVAL 1 HOUR);
