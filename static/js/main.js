// ShopSphere main JS
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alerts after 4s
    document.querySelectorAll('.alert:not(.alert-danger)').forEach(function (a) {
        setTimeout(function () {
            const inst = bootstrap.Alert.getOrCreateInstance(a);
            inst.close();
        }, 4000);
    });

    // Enable tooltips
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el);
    });
});
