/**
 * Small Shop Inventory Management System - Main JavaScript
 * Handles dynamic modals, auto-calculations, and interactive state management.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss Bootstrap flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // 2. Setup Edit Product Modal Populate Logic
    const editProductModal = document.getElementById('editProductModal');
    if (editProductModal) {
        editProductModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            const id = button.getAttribute('data-id');
            const sku = button.getAttribute('data-sku');
            const name = button.getAttribute('data-name');
            const category = button.getAttribute('data-category');
            const price = button.getAttribute('data-price');
            const costPrice = button.getAttribute('data-cost-price');
            const minStock = button.getAttribute('data-min-stock');

            document.getElementById('edit_product_id').value = id;
            document.getElementById('edit_sku').value = sku;
            document.getElementById('edit_name').value = name;
            document.getElementById('edit_category').value = category;
            document.getElementById('edit_price').value = price;
            document.getElementById('edit_cost_price').value = costPrice || '0.00';
            document.getElementById('edit_min_stock_level').value = minStock;

            // Form action target
            const editForm = document.getElementById('editProductForm');
            editForm.action = `/products/edit/${id}`;
        });
    }

    // 3. Setup Restock Product Modal Populate Logic
    const restockModal = document.getElementById('restockModal');
    if (restockModal) {
        restockModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            const id = button.getAttribute('data-id');
            const name = button.getAttribute('data-name');
            const currentStock = button.getAttribute('data-current-stock');

            document.getElementById('restock_product_id').value = id;
            document.getElementById('restock_product_name').textContent = name;
            document.getElementById('restock_current_qty').textContent = currentStock;
            document.getElementById('restock_add_qty').value = '';

            const restockForm = document.getElementById('restockForm');
            restockForm.action = `/products/restock/${id}`;
        });
    }

    // 4. Setup Delete Confirmation Modal Logic
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            const id = button.getAttribute('data-id');
            const name = button.getAttribute('data-name');

            document.getElementById('delete_product_name').textContent = name;
            const deleteForm = document.getElementById('deleteForm');
            deleteForm.action = `/products/delete/${id}`;
        });
    }

    // 5. Dynamic Sales Form Auto-Calculation Logic
    const saleProductSelect = document.getElementById('sale_product_select');
    const saleQuantityInput = document.getElementById('sale_quantity_input');
    const saleUnitPriceDisplay = document.getElementById('sale_unit_price');
    const saleTotalDisplay = document.getElementById('sale_total_price');
    const saleStockHelper = document.getElementById('sale_stock_helper');
    const saleSubmitBtn = document.getElementById('sale_submit_btn');

    if (saleProductSelect && saleQuantityInput) {
        function updateSalesCalculation() {
            const selectedOption = saleProductSelect.options[saleProductSelect.selectedIndex];

            if (!selectedOption || !selectedOption.value) {
                if (saleUnitPriceDisplay) saleUnitPriceDisplay.textContent = '$0.00';
                if (saleTotalDisplay) saleTotalDisplay.textContent = '$0.00';
                if (saleStockHelper) saleStockHelper.textContent = 'Select a product to view stock';
                if (saleSubmitBtn) saleSubmitBtn.disabled = true;
                return;
            }

            const unitPrice = parseFloat(selectedOption.getAttribute('data-price') || 0);
            const availableStock = parseInt(selectedOption.getAttribute('data-stock') || 0, 10);
            const requestedQty = parseInt(saleQuantityInput.value || 0, 10);

            // Display unit price
            if (saleUnitPriceDisplay) {
                saleUnitPriceDisplay.textContent = `$${unitPrice.toFixed(2)}`;
            }

            // Display stock helper text
            if (saleStockHelper) {
                if (availableStock <= 0) {
                    saleStockHelper.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-x-circle"></i> Out of stock (0 available)</span>`;
                } else {
                    saleStockHelper.innerHTML = `<span class="text-secondary"><i class="bi bi-box-seam"></i> In stock: <strong>${availableStock}</strong> units</span>`;
                }
            }

            // Compute total
            const total = requestedQty * unitPrice;
            if (saleTotalDisplay) {
                saleTotalDisplay.textContent = `$${total.toFixed(2)}`;
            }

            // Validation: Ensure quantity is > 0 and <= availableStock
            if (saleSubmitBtn) {
                if (availableStock <= 0 || requestedQty <= 0 || requestedQty > availableStock) {
                    saleSubmitBtn.disabled = true;
                    if (requestedQty > availableStock && availableStock > 0) {
                        saleStockHelper.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-exclamation-triangle"></i> Cannot sell ${requestedQty} units. Only ${availableStock} in stock!</span>`;
                    }
                } else {
                    saleSubmitBtn.disabled = false;
                }
            }
        }

        saleProductSelect.addEventListener('change', updateSalesCalculation);
        saleQuantityInput.addEventListener('input', updateSalesCalculation);
    }
});
