/**
 * Small Shop Inventory Management System - Live Search & Filter
 * Performs fast, client-side filtering on data tables without page reloads.
 */

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('productSearchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const statusFilters = document.querySelectorAll('.status-filter-btn');
    const tableBody = document.getElementById('productsTableBody');

    if (!tableBody) return;

    let activeStatus = 'ALL';

    function filterTable() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectedCategory = categoryFilter ? categoryFilter.value.toLowerCase() : '';
        const rows = tableBody.querySelectorAll('tr.product-row');
        let visibleCount = 0;

        rows.forEach(function (row) {
            const sku = (row.getAttribute('data-sku') || '').toLowerCase();
            const name = (row.getAttribute('data-name') || '').toLowerCase();
            const category = (row.getAttribute('data-category') || '').toLowerCase();
            const status = (row.getAttribute('data-status') || '').toUpperCase();

            // Match text search
            const matchesQuery = !query || sku.includes(query) || name.includes(query) || category.includes(query);

            // Match category
            const matchesCategory = !selectedCategory || category === selectedCategory;

            // Match status
            const matchesStatus = (activeStatus === 'ALL') || (status === activeStatus);

            if (matchesQuery && matchesCategory && matchesStatus) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Show/hide no-results row
        const noResultsRow = document.getElementById('noResultsRow');
        if (noResultsRow) {
            noResultsRow.style.display = visibleCount === 0 ? '' : 'none';
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', filterTable);
    }

    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterTable);
    }

    if (statusFilters.length > 0) {
        statusFilters.forEach(function (btn) {
            btn.addEventListener('click', function () {
                statusFilters.forEach(b => b.classList.remove('active', 'btn-primary'));
                statusFilters.forEach(b => b.classList.add('btn-outline-secondary'));

                this.classList.remove('btn-outline-secondary');
                this.classList.add('active', 'btn-primary');

                activeStatus = this.getAttribute('data-status') || 'ALL';
                filterTable();
            });
        });
    }
});
