-- ==============================================================================
-- Small Shop Inventory Management System - MySQL DDL Schema
-- Compatible with MySQL 8.0+ and Amazon RDS MySQL
-- ==============================================================================

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS inventory_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE inventory_db;

-- 2. Drop Tables if they exist (in proper reverse dependency order)
DROP TABLE IF EXISTS stock_history;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

-- ------------------------------------------------------------------------------
-- 3. Users Table
-- ------------------------------------------------------------------------------
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'Admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. Products Table
-- ------------------------------------------------------------------------------
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    cost_price DECIMAL(10, 2) DEFAULT 0.00,
    quantity INT NOT NULL DEFAULT 0,
    min_stock_level INT NOT NULL DEFAULT 5,
    is_low_stock_notified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Integrity Constraints
    CONSTRAINT chk_price_positive CHECK (price >= 0.00),
    CONSTRAINT chk_cost_positive CHECK (cost_price >= 0.00),
    CONSTRAINT chk_quantity_non_negative CHECK (quantity >= 0),
    CONSTRAINT chk_min_stock_positive CHECK (min_stock_level >= 1),
    
    -- Performance Indexes
    INDEX idx_product_sku (sku),
    INDEX idx_product_category (category),
    INDEX idx_product_stock_levels (quantity, min_stock_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. Sales Table
-- ------------------------------------------------------------------------------
CREATE TABLE sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NULL,
    quantity_sold INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Integrity Constraints
    CONSTRAINT chk_sold_qty_positive CHECK (quantity_sold > 0),
    CONSTRAINT chk_unit_price_positive CHECK (unit_price >= 0.00),
    CONSTRAINT chk_total_price_positive CHECK (total_price >= 0.00),

    -- Foreign Keys
    CONSTRAINT fk_sales_product FOREIGN KEY (product_id) 
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_sales_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE SET NULL,

    -- Performance Indexes
    INDEX idx_sales_date (sale_date),
    INDEX idx_sales_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 6. Stock History (Audit Log) Table
-- ------------------------------------------------------------------------------
CREATE TABLE stock_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NULL,
    change_type VARCHAR(20) NOT NULL, -- 'INITIAL', 'SALE', 'RESTOCK', 'ADJUSTMENT'
    quantity_change INT NOT NULL,     -- Negative for sales, Positive for restock
    resulting_quantity INT NOT NULL,
    notes VARCHAR(255) NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Integrity Constraints
    CONSTRAINT chk_resulting_qty_non_negative CHECK (resulting_quantity >= 0),

    -- Foreign Keys
    CONSTRAINT fk_history_product FOREIGN KEY (product_id) 
        REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_history_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE SET NULL,

    -- Performance Indexes
    INDEX idx_history_recorded_at (recorded_at),
    INDEX idx_history_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
